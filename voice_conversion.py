from elevenlabs import ElevenLabs
import apikey
import random
from conversation_highlight import (
    ConversationHighlight,
    mp3_to_ndarray
)
client = ElevenLabs(
    api_key=apikey.API_KEY,
)
OUTPUT_FORMATS = ['mp3_22050_32', 'mp3_44100_32', 'mp3_44100_64', 
                  'mp3_44100_96', 'mp3_44100_128', 'mp3_44100_192',
                  'pcm_16000', 'pcm_22050', 'pcm_24000', 'pcm_44100',
                  'ulaw_8000']
MODELS = ['eleven_multilingual_v2', 'eleven_flash_v2_5', 'eleven_flash_v2',
          'eleven_multilingual_sts_v2', 'eleven_english_sts_v2']
GENDERS = ['female', 'male']
ACCENTS = ['American', 'Australian', 'British', 'Transatlantic', 'Swedish']
AGES = ['middle-aged', 'young', 'old']


def gen_all_voices():
    """
    Generate all voices from ElevenLabs API

    Returns:
        voices (list): List of all Voice objects from ElevenLabs
    """
    voices = []
    for voice in client.voices.get_all():
        for v in voice[1]:
            voices.append(v)
    return voices


ALL_VOICES = gen_all_voices()


def write_all_output_voices(output_dir, input_audio):
    """
    Converts a given audio with all the possible voices from ElevenLabs

    Args:
        output_dir (String): directory to write the audio files under
        input_audio (String): path of input audio to be converted
    """
    for voice in ALL_VOICES:
        write_audio_file(output_dir, input_audio, voice)


def write_audio_file(output_dir, input_audio, voice, id=""):
    """
    Writes an mp3 file tha is converted using the given voice from ElevenLabs,
    model and output_format can be changed based o ElevenLabs models

    Args:
        output_dir (String): directory to write the audio files under
        input_audio (String): path of input audio to be converted
        voice (Voice): Voice object from ElevenLabs API
        id (String): ID of Fora highlight

    Returns:
        output_audio (String): path of newly written mp3 file
    """
    try:
        with open(input_audio, "rb") as audio_file:
            converted_audio = client.speech_to_speech.convert(
                voice_id=voice.voice_id,
                audio=audio_file,
                output_format="mp3_44100_128",
                model_id="eleven_multilingual_sts_v2",
            )
            output_audio = f"{output_dir}/{voice.name}_{id}_output_audio.mp3"
            with open(output_audio, "wb") as output_file:
                for chunk in converted_audio:
                    output_file.write(chunk)
            print(f"Converted audio saved to {output_audio}")
            return output_audio
    except Exception as e:
        print(f"An error occurred: {e}")


def write_output_voice(output_dir, input_audio, id=""):
    """
    Randomly selects one voice from ElevenLabs to convert the input audio to.

    Args:
        output_dir (String): directory to write the audio files under
        input_audio (String): path of input audio to be converted

    Returns:
        (String): path to converted audio file
    """
    random_voices = random.sample(ALL_VOICES, 1)
    for voice in random_voices:
        return write_audio_file(output_dir, input_audio, voice, id=id)


def main(output_dir, input_highlight, audio_path, id=""):
    """
    Takes an input Conversation Highlight and returns a new Conversation
    Highlight that is converted from the original

    Args:
        output_dir (String): directory to write the audio files under
        input_highlight (ConversationHighlight): input highight to be converted
        audio_path (String): path to mp3 file of the highlight to be converted
        to numpy ndarray

    Returns:
        output_highlight (ConversationHighlight): converted Conversation
        Highlight transformed is set to True
        og_hr (original highlight record) is set to the input highlight
    """
    converted_audio = write_output_voice(output_dir, audio_path, id=id)
    numpy_array = mp3_to_ndarray(converted_audio, 16000)
    output_highlight = ConversationHighlight(
        share_location=None,
        share_text=None,
        transformed=True,
        auto_gen=False,
        transcript=input_highlight.transcript,
        audio=numpy_array,
        conv_rec=None,
        sharer_iden=None,
        og_hr=input_highlight,
        primary_speaker_iden=None,
        add_speaker_iden=None,
        tags=input_highlight.tags
    )
    return output_highlight
