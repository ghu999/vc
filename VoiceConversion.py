from elevenlabs import ElevenLabs

input_audio = "highlight_4547831.mp3"

client = ElevenLabs(
    api_key="sk_117691c66476b038f139c79efb58fa455b3688db8a1fb337",
)

def gen_all_output_voices():
    print("Voices:")
    for voice in client.voices.get_all():
        for v in voice[1]:
            print(v.name + " " + v.voice_id)
            try:
                with open(input_audio, "rb") as audio_file:
                    converted_audio = client.speech_to_speech.convert(
                        voice_id=v.voice_id,
                        audio=audio_file,
                        output_format="mp3_44100_128",
                        model_id="eleven_multilingual_sts_v2",
                    )
                    output_audio = f"outputs/{v.name}_output_audio.mp3"
                    with open(output_audio, "wb") as output_file:
                        for chunk in converted_audio:
                            output_file.write(chunk)
                    print(f"Converted audio saved to {output_audio}")
            except Exception as e:
                print(f"An error occurred: {e}")

gen_all_output_voices()



