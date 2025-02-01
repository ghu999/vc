from flask import Flask, request, jsonify
from datetime import datetime
from conversation_highlight import generate_transcript
from flask_cors import CORS
from redaction import (
    redact_mp3_by_words, 
    redact_mp3_by_single_words
)
app = Flask(__name__)
CORS(app)

INPUT_AUDIO = "/Users/granthu/VC Prototype/vc/audio-redaction-ui/frontend/src/data/highlight-5300643.mp3"
INPUT_JSON = "/Users/granthu/VC Prototype/vc/audio-redaction-ui/frontend/src/data/conversation-5300643.json"

# Endpoint to serve the transcript
@app.route('/api/transcript', methods=['GET'])
def get_transcript():
    transcript = generate_transcript(INPUT_JSON)
    print(transcript)
    return jsonify({"transcript": transcript})

# Endpoint to process JSON metadata and extract transcript
@app.route('/extract-transcript', methods=['POST'])
def extract_transcript_api():
    # Get the JSON data from the request
    
    # Extract transcript using your conversion script
    transcript = generate_transcript(INPUT_JSON)
    
    # Return the transcript as JSON
    return jsonify({"transcript": transcript})


@app.route("/api/redact", methods=["POST"])
def redact():
    data = request.get_json()
    print(data)
    words_to_redact = data.get("words", [])

    if not words_to_redact:
        return jsonify({"error": "No words provided for redaction"}), 400

    try:
        # Call your redaction function with the selected words
        output_file = ""
        if isinstance(words_to_redact[0], int):
            output_file = redact_mp3_by_single_words(INPUT_AUDIO, INPUT_JSON, "/Users/granthu/VC Prototype/vc/audio-redaction-ui/frontend/build/data", 
                                          "5300643", words_to_redact)
        else:
            output_file = redact_mp3_by_words(INPUT_AUDIO, INPUT_JSON, "/Users/granthu/VC Prototype/vc/audio-redaction-ui/frontend/build/data", 
                                          "5300643", words_to_redact)
        
        print(output_file)
        return jsonify({"message": "Redacted audio created", "filePath": output_file[(output_file.index("data"))-1:]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)