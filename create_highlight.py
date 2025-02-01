import conversation_highlight as ch
import voice_conversion as vc
import fetch_conversations as fetch
import argparse
from pathlib import Path
import json
from conversation_highlight import ConversationHighlight


if __name__ == "__main__":
    response = input("command line or local file: ")
    if response == "command line":
        cmd_input = input("enter args:")
        parser = argparse.ArgumentParser(description="enter command")
        parser.add_argument("--api-key", required=True)
        parser.add_argument("--output-directory", required=True, type=Path)
        parser.add_argument("--type", required=True)
        parser.add_argument("--id", required=True)
        args = parser.parse_args()
        
        json_file, audio_path = fetch.main(args.type, args.id, args.api_key, args.output_directory)
        #create conversation highlight object
        numpy_array = ch.mp3_to_ndarray(audio_path, 16000)
        transcript = ch.generate_transcript(json_file)
        with open(json_file, 'r') as file:
            data = json.load(file)
        highlight = ConversationHighlight(
            share_location=None,
            share_text=None,
            transformed=False,
            auto_gen=False,
            transcript=transcript,
            audio=numpy_array,
            conv_rec=None,
            sharer_iden=None,
            og_hr=None,
            primary_speaker_iden=None,
            add_speaker_iden=None,
            tags=data['tags']
        )
        print(highlight)
        converted_highlight = vc.main(args.output_directory, highlight, 
                                      audio_path, args.id)
        r.redact_mp3_by_words(audio_path, json_file, "testing", id=args.id,
                              redacted_words=['gay'])
        print(converted_highlight)
        
    elif response == "local file":
        json_file = input("enter path of json.file: ")
        audio_path = input("enter path of mp3 file: ")
        numpy_array = ch.mp3_to_ndarray(audio_path, 16000)
        transcript = ch.generate_transcript(json_file)
        with open(json_file, 'r') as file:
            data = json.load(file)
        highlight = ConversationHighlight(
            share_location=None,
            share_text=None,
            transformed=False,
            auto_gen=False,
            transcript=transcript,
            audio=numpy_array,
            conv_rec=None,
            sharer_iden=None,
            og_hr=None,
            primary_speaker_iden=None,
            add_speaker_iden=None,
            tags=data['tags']
        )
        print(highlight)
        converted_highlight = vc.main("testing", highlight, audio_path)
        print(converted_highlight)
