import json
from pydub import AudioSegment
from pydub.generators import Sine
from datetime import datetime
from conversation_highlight import generate_transcript


def redact_mp3_by_time(input_file, output_dir, id, redaction_points,
                       redact_freq=1000, redact_duration=1000):
    """
    Redact an MP3 file by replacing specific time ranges with a bleep tone.

    Args:
        input_file (String): Path to the input MP3 file
        output_dir (String): Directory to save the mp3 file under
        redaction_points (list of tuples): List of (start, end) times in
        milliseconds for redaction
        redact_freq (int): Frequency of the bleep tone in Hz
        (default is 1000 Hz)
        redact_duration (int): Duration of each bleep in milliseconds
        (default is 1000 ms)
    Returns:
        (String): path of redacted mp3 file
    """
    audio = AudioSegment.from_file(input_file, format="mp3")
    bleep = Sine(redact_freq).to_audio_segment(duration=redact_duration)
    for start, end in redaction_points:
        bleep_seg = bleep * ((end - start) // redact_duration + 1)
        bleep_seg = bleep_seg[:end - start]

        audio = audio[:start] + bleep_seg + audio[end:]
    audio.export(output_dir + "/" + f"redacted_{id}.mp3", format="mp3")
    return output_dir + "/" + f"redacted_{id}.mp3"


def redact_mp3_by_single_words(input_audio, input_json, output_dir, id,
                               redacted_indeces, redact_freq=1000):
    """
    Redact an MP3 file by replacing a single word (by index) with a bleep tone.

    Args:
        input_audio (String): Path to the input MP3 file
        input_json (String): Path to .json file of the highlight
        output_dir (String): Directory to save the mp3 file under
        id (String): id of highlight
        redaction_indices (list of ints): List of indices of transcript
        that should be redacted 
        redact_freq (int): Frequency of the bleep tone in Hz
        (default is 1000 Hz)
    Returns:
        (String): path of redacted mp3 file
    """
    audio = AudioSegment.from_file(input_audio, format="mp3")
    with open(input_json, 'r') as file:
        data = json.load(file)
    mappings = gen_words_timestamps(input_json)
    transcript = generate_transcript(input_json).split(" ")
    real_start = data['audio_start_offset']
    for index in redacted_indeces:
        word = transcript[index]
        for instance in mappings[word]:
            if instance[2] != index:
                continue
            start = instance[0]
            end = instance[1]
            duration = (end - start) * 1000
            print(start, end, duration)
            bleep = Sine(redact_freq).to_audio_segment(duration=duration)
            adjusted_start = (start - real_start) * 1000
            adjusted_end = (end - real_start) * 1000
            audio = audio[:adjusted_start+1000] + bleep + audio[adjusted_end+1000:]
    audio.export(output_dir + "/" + f"redacted_{id}_" + datetime.now().strftime('%H:%M:%S') + ".mp3", format="mp3")
    return output_dir + "/" + f"redacted_{id}_" + datetime.now().strftime('%H:%M:%S') + ".mp3"


def redact_mp3_by_words(input_audio, input_json, output_dir, id,
                        redacted_words, redact_freq=1000):
    """
    Redact an MP3 file by replacing every instance of a word with a bleep tone.

    Args:
        input_audio (String): Path to the input MP3 file
        input_json (String): Path to .json file of the highlight
        output_dir (String): Directory to save the mp3 file under
        redaction_words (list of Strings): List of words that should be redacted
        redact_freq (int): Frequency of the bleep tone in Hz
        (default is 1000 Hz)
        redact_duration (int): Duration of each bleep in milliseconds
        (default is 1000 ms)
    Returns:
        (String): path of redacted mp3 file
    """
    audio = AudioSegment.from_file(input_audio, format="mp3")
    mappings = gen_words_timestamps(input_json)
    with open(input_json, 'r') as file:
        data = json.load(file)
    real_start = data['audio_start_offset']
    for word in redacted_words:
        for instance in mappings[word]:
            start = instance[0]
            end = instance[1]
            duration = (end - start) * 1000
            print(start, end, duration)
            bleep = Sine(redact_freq).to_audio_segment(duration=duration)
            adjusted_start = (start - real_start) * 1000
            adjusted_end = (end - real_start) * 1000
            audio = audio[:adjusted_start+1000] + bleep + audio[adjusted_end+1000:]
    audio.export(output_dir + "/" + f"redacted_{id}_" + datetime.now().strftime('%H:%M:%S') + ".mp3", format="mp3")
    return output_dir + "/" + f"redacted_{id}_" + datetime.now().strftime('%H:%M:%S') + ".mp3"


def gen_words_timestamps(input_json):
    """
    Return a dictionary mapping each word to its start and end time.
    
    Args:
        input_json (String): Path to .json file
    Returns:
        mapping (Dictionary): key: word, value: dictionary containing
        start and end times
    """
    with open(input_json, 'r') as file:
        data = json.load(file)
    mapping = {}
    index = 0
    for group in data["snippets"][0]['words']:
        if group['word'] not in mapping:
            mapping[group['word']] = set()
            mapping[group['word']].add((group['start'], group['end'], index))
            index += 1
        else:
            mapping[group['word']].add((group['start'], group['end'], index))
            index += 1
    return mapping


def _keep_words_before_time(words, end_time):
    """
    Given a list of words with timings, keep only words
    that end before end_time
    """
    last_keep_word = 0
    # lets find the last word we can keep
    for i, word in enumerate(words):
        # find first word that ends after keep window
        if word['start'] > end_time:
            # found first word we have to cut
            last_keep_word = i
            break
        else:
            last_keep_word = len(words)
    # remove words that end after keep window
    return words[0:last_keep_word]


def _keep_words_after_time(words, start_time):
    """
    Given a list of words with timings, keep only words
    that start after start_time
    """
    # find the first word we can keep
    first_keep_word = 0
    for i, word in enumerate(words):
        # find first word that starts inside keep window
        if word['end'] >= start_time:
            # first word we can keep
            first_keep_word = i
            break
        else:
            first_keep_word = len(words)
    # remove words that started before keep window
    return words[first_keep_word:]


def redact_reco_words(snippets, redaction_start, redaction_end):
    """
    given a list of snippets and redaction timings, removes reco_words
    that fall between those timings and replaces them with a single instance
    of the [redacted] keyword, with redaction timings as "word" timings
    """
    redaction_inserted = False
    for snippet in snippets:
        unredacted = snippet["words"]
        pre_redaction = _keep_words_before_time(unredacted, redaction_start)
        post_redaction = _keep_words_after_time(unredacted, redaction_end)
        # in the first snippet affected by the redaction, insert [redacted]
        if not redaction_inserted and len(pre_redaction) < len(unredacted):
            pre_redaction.append(["[redacted]", redaction_start, redaction_end, 1])
            redaction_inserted = True
        # modify reco_words field in place
        snippet["reco_words"] = pre_redaction + post_redaction
    output = ""
    for w in snippet['reco_words']:
        if '[redacted]' in w:
            output += '[redacted]' + " "
            continue
        output += w['word'] + " "
    return redaction_inserted, output.strip()


if __name__ == "__main__":
    # with open("testing/conversation-4314790.json", 'r') as file:
    #     data = json.load(file)
    # print("unredacted")
    # output = ""
    # for w in data['snippets'][0]['words']:
    #     output += w['word'] + " "
    # print(output)
    # print('redacted')
    # print(redact_reco_words(data['snippets'], 668, 672))

    # with open("testing/highlight-4314790.mp3", 'rb') as file:
    #     redact_mp3_by_time("testing/highlight-4314790.mp3", "testing",
    #                        "4314790",
    #                        [(3000, 5000)])
    #redact_mp3_by_words("testing/highlight-4314790.mp3","testing/conversation-4314790.json", "testing", "4314790", ['difference'])
    redact_mp3_by_single_words("/Users/granthu/VC Prototype/vc/testing/highlight-5300643.mp3","/Users/granthu/VC Prototype/vc/testing/conversation-5300643.json", "/Users/granthu/VC Prototype/vc/audio-redaction-ui/backend", "5300643",[0])