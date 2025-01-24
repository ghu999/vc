import json
import logging
from operator import xor

from marshmallow import ValidationError, fields
from opentelemetry import trace
from sqlalchemy import exc, or_, select
from sqlalchemy.engine import Engine

from cortico.helpers.authorization import user_has_permission
from cortico.helpers.conversations import get_conversation_snippets
from cortico.helpers.transcript_edit import (
    AppSnippetSchema,
    Edit,
    SnippetSchema,
    add_edit_row,
    conversation_ready_to_edit,
    force_align_edits,
    redact_reco_words,
    update_highlight_snippets,
    update_participants,
)
from cortico.json_util import normalize_results_core
from cortico.lib.etl.audio import MIN_REDACTION_SEGMENT_LENGTH
from cortico.lib.falcon import FailException, ForbiddenException
from cortico.lib.marshmallow import SchemaExcludeUnknown
from cortico.models import conversation_attendees, conversations
from cortico.permissions import LeavenPermissionTypes, Permission
from fora.repos.conversations import ConversationRepository

logger = logging.getLogger("leaven")
tracer = trace.get_tracer(__name__)


class TranscriptRedactionResource:
    """
    Resource for Transcript Redaction
    """

    def __init__(self, engine: Engine):
        self.engine = engine  # sqlalchemy engine

    class TranscriptRedactionSchema(SchemaExcludeUnknown):
        version = fields.Integer(required=True)
        snippets = fields.List(fields.Nested(SnippetSchema), required=True)

        # Redaction timings
        redaction_start_offset = fields.Float(required=True)
        redaction_end_offset = fields.Float(required=True)

    def on_put(self, req, resp, conversation_id):
        """
        Redact a conversation. Expects:
            - modified snippets, as in a transcript edit, except that the
            only edit should be the words in question replaced with
            the keyword "[redacted]"
            - exact audio timings to be replaced with a redaction tone
        """
        logger.info("Redacting conversation %s", conversation_id)
        with tracer.start_as_current_span("validation") as span:
            try:
                params = json.load(req.bounded_stream)
                data = self.TranscriptRedactionSchema().load(params)
                conversation_id = int(conversation_id)
            except json.JSONDecodeError:
                resp.context["fail"] = {"error": "put body not valid json"}
                return
            except ValidationError as err:
                resp.context["fail"] = err.messages
                return
            except ValueError:
                resp.context["fail"] = (
                    f"could not convert conversation_id '{conversation_id}' to int"
                )
                return
            span.set_attribute("validation", "validation")
        # Get relevant user permissions
        user = req.context["user"]

        # get conversation metadata
        with self.engine.begin() as conn:
            conversation = (
                conn.execute(
                    select(
                        conversations.c.collection_id,
                        conversations.c.forum_id,
                        conversations.c.irl,
                        conversations.c.duration,
                    )
                    .select_from(
                        conversations.outerjoin(
                            conversation_attendees,
                            conversation_attendees.c.conversation_id
                            == conversations.c.id,
                        )
                    )
                    .where(
                        conversations.c.id == conversation_id,
                        or_(
                            conversations.c.forum_id.is_(None),
                            # for forum conversations, check app transcript visibility logic
                            ConversationRepository.user_can_view_transcript_stmt(
                                user=user
                            ),
                        ),
                    )
                )
                .mappings()
                .fetchone()
            )
        if conversation is None:
            raise FailException(f"Unable to find conversation {conversation_id}")
        if not xor(
            (collection_id := conversation.get("collection_id")) is None,
            (forum_id := conversation.get("forum_id")) is None,
        ):
            raise FailException(
                f"Conversation {conversation_id} must be in either a collection or forum."
            )
        if forum_id is not None and conversation.irl is False:
            raise FailException("Can only redact IRL forum conversations.")
        if (
            data["redaction_start_offset"] - MIN_REDACTION_SEGMENT_LENGTH < 0
            or data["redaction_end_offset"] + MIN_REDACTION_SEGMENT_LENGTH
            > conversation["duration"]
        ):
            raise FailException(
                "Cannot redact at the ends of a conversation: trim instead."
            )

        user_can_update = (
            user_has_permission(
                user,
                Permission(
                    "update",
                    LeavenPermissionTypes.conversation_transcript,
                    collection_id=collection_id,
                ),
            )
            if collection_id is not None
            # TODO: should be a separate update Forum X Conversations permission
            else True
        )
        if not user_can_update:
            raise ForbiddenException("Insufficient permissions to redact a transcript")

        user_is_staff = user_has_permission(
            user, Permission("read", LeavenPermissionTypes.staff_features)
        )
        if not user_is_staff:
            raise ForbiddenException("Insufficient permissions due to not being staff")

        with self.engine.begin() as conn:
            try:
                if not conversation_ready_to_edit(conn, conversation_id):
                    raise ForbiddenException(
                        "Cannot redact this transcript as it is still being processed."
                    )

                new_snippets = data["snippets"]
                with tracer.start_as_current_span("load previous") as span:
                    orig_snippets = get_conversation_snippets(conn, conversation_id)
                    # Use marshmallow to filter out the fields we don't need
                    prev_snippets = AppSnippetSchema(many=True).load(orig_snippets)

                    span.set_attribute("load previous", len(prev_snippets))

                with tracer.start_as_current_span("create edit boundaries") as span:
                    edit = Edit(prev_snippets, new_snippets, conversation_id)
                    edit_boundaries = (
                        edit.update_boundaries + edit.insert_delete_boundaries
                    )
                    span.set_attribute("boundaries", len(edit_boundaries))
                # ensure that only one edit boundary exists, and it contains one new redaction
                if (
                    len(edit_boundaries) != 1
                    or (boundary := edit_boundaries[0]).redaction_diff != 1
                ):
                    raise FailException(
                        "Edit text must contain one new redaction and no other edits"
                    )
                # add a little leeway for redaction timing not lining up with snippets
                padding = boundary.padding
                boundary.padding = 2
                # redact v1 reco_words, as those are the ones used in force alignment
                redaction_successful = redact_reco_words(
                    edit.snippets_v1[boundary.v1_start_padded : boundary.v1_end_padded],
                    data["redaction_start_offset"],
                    data["redaction_end_offset"],
                )
                boundary.padding = padding
                if not redaction_successful:
                    raise FailException(
                        "redaction timings must correspond to redacted text"
                    )
                force_align_edits(edit)
                update_participants(conn, conversation_id, edit.snippets_v2)
                with tracer.start_as_current_span("save snippets") as span:
                    # Update each changed contiguous snippet set
                    edit.save_all_snippets(conn)

                # update the snippet words within edit boundaries
                update_highlight_snippets(
                    conn, conversation_id=conversation_id, edit=edit
                )

                with tracer.start_as_current_span("get conversation snippets") as span:
                    updated_snippets = get_conversation_snippets(conn, conversation_id)
                    span.set_attribute("updated snippets", len(updated_snippets))
                add_edit_row(
                    conn,
                    updated_snippets,
                    conversation_id,
                    data["version"] + 1,
                    user["id"],
                    redaction_timings=(
                        data["redaction_start_offset"],
                        data["redaction_end_offset"],
                    ),
                )

                resp.context["success"] = {
                    **normalize_results_core(
                        snippets=AppSnippetSchema(many=True).load(updated_snippets)
                    ),
                    "version": data["version"] + 1,
                }

            except exc.SQLAlchemyError as e:
                logger.info("error %s", e)
                conn.rollback()
                raise FailException(
                    f"Unable to redact transcript for conversation {conversation_id}, version {data['version']}"
                )
            
def redact_mp3(engine, conversation_id, redaction_times):
    """
    trim out conversation audio inside tone_times and splice in redaction tones

    tone_times must be positive and within (0 < tone_time < length, exclusive)
    the conversation length

    non-sequential and overlapping times will be normalized
    """
    if not redaction_times:
        return redaction_times
    tone_times = normalize_redaction_timings(redaction_times)

    # Get conversation data
    logger.info("Querying db for conversation")
    conversation = get_conversation_info(engine, conversation_id)

    # app and web conversations have different buckets and keys
    if (asset_id := conversation.get("asset_id")) is not None:
        s3_bucket = AssetRepository.asset_bucket("audio")
        conversation_mp3_key = AssetRepository.asset_key(
            asset_type="audio",
            extension=AssetRepository.asset_extension("audio"),
            id_=asset_id,
        )
    elif (
        conversation.get("audio_url") is not None
        or conversation.get("_audio_id") is not None
    ):
        s3_bucket = config.S3_BUCKET
        conversation_mp3_key = conversation_to_audio_key(conversation)
    else:
        raise ValueError(f"Conversation {conversation_id} has no audio key")

    with tempfile.TemporaryDirectory() as tmpdir:
        original_mp3 = Path(tmpdir) / "original.mp3"
        redacted_mp3 = Path(tmpdir) / "redacted.mp3"

        # Download file from s3
        s3 = boto3.client("s3")
        logger.info(
            "Downloading %s to %s",
            f"{s3_bucket}/{conversation_mp3_key}",
            original_mp3,
        )
        s3.download_file(
            Bucket=s3_bucket, Key=conversation_mp3_key, Filename=original_mp3
        )
        audio_metadata = get_ffprobe_data(audio_path=original_mp3)["streams"][0]

        # Build soX trimming parameters
        # https://sox.sourceforge.net/sox.html#EFFECTS
        splice_excess = 0.005
        splice_points = []
        trim_commands = []
        prev_end_time = splice_excess
        splice_point_offset = splice_excess
        for tone in tone_times:
            # trim all sections slightly long, so SoX can overlap them by splice_excess
            trim_start = prev_end_time - splice_excess
            trim_end = tone["start_time"] + splice_excess
            trim_commands.append(
                f"|sox {original_mp3} -p trim ={trim_start} ={trim_end}"
            )
            prev_end_time = tone["end_time"]
            # record the splice points. SoX seems to calculate timings by "lining up"
            # the long-trimmed pieces before overlapping, so each subsequent splice
            # point is slightly more offset from its "actual" time than the last
            splice_points.append(
                f"={tone['start_time'] + splice_point_offset},{splice_excess},0"
            )
            splice_point_offset += 2 * splice_excess
            splice_points.append(
                f"={tone['end_time'] + splice_point_offset},{splice_excess},0"
            ),
            splice_point_offset += 2 * splice_excess
        # the last section gets no explicit end time
        trim_start = prev_end_time - splice_excess
        trim_commands.append(f"|sox {original_mp3} -p trim ={trim_start}")

        # Create sine tone commands
        tone_commands = []
        for tone in tone_times:
            # tones are slightly long for splicing, too
            duration = (
                float(tone["end_time"])
                - float(tone["start_time"])
                + (2 * splice_excess)
            )
            # synth outputs 2 channels of sine waves, remix mixes them into one waveform
            # and outputs a copy for each input channel
            tone_commands.append(
                f"|sox -n -r {audio_metadata['sample_rate']} -p "
                f"synth {duration} sin 440 sin 880 remix"
                + " 1p-18.1,2p-41" * audio_metadata["channels"],
            )

        # Interleave tone commands and trim commands together
        redaction_parameters = [None] * (len(trim_commands) + (len(tone_commands)))
        redaction_parameters[::2] = trim_commands
        redaction_parameters[1::2] = tone_commands

        # perform multiple splice operations
        sox_redaction_command = [
            "sox",
            *redaction_parameters,
            redacted_mp3,
            "splice",
            *splice_points,
        ]

        # Call sox to splice together redacted mp3
        sox_output = subprocess.check_output(
            sox_redaction_command, stderr=subprocess.STDOUT
        )
        logger.info("stdout: %s", sox_output)

        # Copy redacted mp3 to s3
        logger.info("Uploading %s to %s", redacted_mp3, conversation_mp3_key)
        s3.upload_file(redacted_mp3, s3_bucket, conversation_mp3_key)

    return tone_times

def mark_redacted(engine):
    """
    Any conversation with edits (so this excludes conversations that were backfilled
    after a redaction happened) that has redactions gets all transcript_edit rows
    marked as redactions where there are more '[redacted]' words in that version than
    the previous one
    """
    with engine.connect() as conn:
        # Edits on the conversation that happened after the backfill
        stmt = (
            select(
                models.transcript_edits.c.conversation_id,
                func.count(models.transcript_edits.c.conversation_id).label(
                    "number_of_edits"
                ),
            )
            .group_by(models.transcript_edits.c.conversation_id)
            .having(func.count(models.transcript_edits.c.conversation_id) > 1)
        )

        results = rows_to_json(conn.execute(stmt).fetchall())
        binds = []
        for conversation in results:
            logger.info(f"conversation {conversation['conversation_id']}")

            # In the check as part of transcript editing to see if we made a new redaction,
            # we compare all the redactions (in case a redaction was moved), but since
            # the snippets written to the transcript_edits table will have different timings,
            # due to force alignment having been run, this won't work.
            # But Kelly says that isn't a thing she does, so we're going to rely on that
            # and only check for the number of redactions
            transcript_edits = rows_to_json(
                conn.execute(
                    select(
                        models.transcript_edits.c.version_snippets,
                        models.transcript_edits.c.user_id,
                    )
                    .where(
                        models.transcript_edits.c.conversation_id
                        == conversation["conversation_id"],
                    )
                    .order_by(models.transcript_edits.c.id)
                )
            )

            for i, edit in enumerate(transcript_edits):
                snippets = edit["version_snippets"]
                words = list(
                    itertools.chain.from_iterable(s["words"] for s in snippets)
                )
                redactions = [tuple(w) for w in words if "[redacted]" in w[0]]
                if i == 0:
                    redaction_count = len(redactions)
                    continue

                if redactions and len(redactions) > redaction_count:
                    logger.info(
                        f"Conversation {conversation['conversation_id']}, version {i} has redactions"
                    )
                    binds.append(
                        {"conv_id": conversation["conversation_id"], "version_num": i}
                    )
                redaction_count = len(redactions)

        stmt = (
            models.transcript_edits.update()
            .where(
                and_(
                    models.transcript_edits.c.conversation_id == bindparam("conv_id"),
                    models.transcript_edits.c.version == bindparam("version_num"),
                )
            )
            .values(redaction=True)
        )
        conn.execute(stmt, binds)

class TranscriptEdit(Base):
    __tablename__ = "transcript_edits"
    __table_args__ = (
        UniqueConstraint("conversation_id", "version", name="conversation_version_uc"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    conversation_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("conversations.id", ondelete="CASCADE"), index=True
    )
    version: Mapped[Optional[int]]
    user_id: Mapped[Optional[int]] = mapped_column(Integer, index=True)
    version_snippets = mapped_column(JSONB)
    is_reset: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    edit_timestamp: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime, default=datetime.datetime.utcnow, index=True
    )
    alignment_info = mapped_column(JSONB)
    trim = mapped_column(JSONB)
    redaction: Mapped[Optional[str]] = mapped_column(Boolean, default=False)
    redaction_start_offset: Mapped[Optional[float]]
    redaction_end_offset: Mapped[Optional[float]]
    redaction_complete: Mapped[Optional[bool]]

    def __repr__(self):
        return "<TranscriptEdit %s: conversation_id %s, user_id %s" % (
            self.id,
            self.conversation_id,
            self.user_id,
        )