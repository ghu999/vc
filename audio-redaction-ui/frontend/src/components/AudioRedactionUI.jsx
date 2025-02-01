import { useState, useEffect } from "react";
import "../App.css";
import audio_path from "../data/highlight-5300643.mp3"
//import redacted_path from "../data/redacted_5300643.mp3"
const TranscriptDisplay = ({ transcript, redactedAudio, setRedactedAudio }) => {
  const [selectedWords, setSelectedWords] = useState([]);
  const [selectAll, setSelectAll] = useState(false);
  const handleWordClick = (word, index) => {
    if (selectAll) {
      // Select/Deselect all instances of the word
      const allInstances = transcript.split(" ").filter((w) => w === word);
      if (selectedWords.some((w) => allInstances.includes(w))) {
        // Deselect all instances of the word
        setSelectedWords(selectedWords.filter((w) => !allInstances.includes(w)));
      } else {
        setSelectedWords([...selectedWords, word]);
      }
    } else {
      if (selectedWords.includes(index)) {
        // Deselect the word if its index is already selected
        setSelectedWords(selectedWords.filter((i) => i !== index));
      } else {
        // Select the word by its index
        setSelectedWords([...selectedWords, index]);
      }
    }
  };

  const clearAll = () => {
    setSelectedWords([]);
    setSelectAll(false);
  }

  const redact = () => {
    if (selectedWords.length === 0) {
      alert("Please select words to redact.");
      return;
    }
    // Make a POST request to the backend to redact the selected words
    fetch("http://127.0.0.1:5000/api/redact", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ words: selectedWords}),
    })
      .then((response) => {
        if (!response.ok) {
          throw new Error("Failed to generate redacted audio.");
        }
        return response.json();
      })
      .then((data) => {
        alert("Redacted audio successfully created!");
        // Optionally, handle the redacted audio file path
        setRedactedAudio(`http://localhost:9000${data.filePath}`);
        console.log("Redacted audio file path:", data.filePath);
      })
      .catch((error) => {
        console.error("Error during redaction:", error);
        alert(`An error occurred while redacting the audio. ${error}`);
      });
  };


  return (
    <div className="transcript-container-scrollable">
      <div style={{ marginBottom: "10px" }}>
        <label>
          <input
            type="checkbox"
            checked={selectAll}
            onChange={(e) => setSelectAll(e.target.checked)}
          />
          Select All Instances of a Word
        </label>
      </div>
      <p>
      {transcript &&
        transcript.split(" ").map((word, index) => {
          const isHighlighted = selectAll
            ? selectedWords.includes(word) // Highlight by word when "Select All" is enabled
            : selectedWords.includes(index); // Highlight by index when "Single Select" is enabled

          return (
            <span
              key={index}
              onClick={() => handleWordClick(word, index)}
              style={{
                cursor: "pointer",
                marginRight: "5px",
                color: isHighlighted ? "blue" : "black",
                backgroundColor: isHighlighted ? "#d0ebff" : "transparent",
                padding: "2px 4px",
                borderRadius: "4px",
              }}
            >
              {word}
            </span>
          );
        })}
      </p>
      
      <h3>Transcript Audio</h3>
      <audio controls>
        <source src={audio_path} type="audio/mpeg" />
        Your browser does not support the audio element.
      </audio>
      <div style={{marginTop: "10px"}}>
      {selectedWords.length > 0 && (
        <>
        <p>
          {
            selectAll ? (
              <strong>Multi-Selected Words: {selectedWords.join(", ")}</strong>
            ) : (
              <strong>Single-Selected words: {selectedWords.map((i) => transcript.split(" ")[i]).join(", ") || "None"}</strong>
            )}
  
      </p>
          <button
              onClick={clearAll}
              style={{
                padding: "6px 12px",
                fontSize: "14px",
                backgroundColor: "#ff4d4d",
                color: "white",
                border: "none",
                borderRadius: "4px",
                cursor: "pointer",
              }}
            >
              Clear All
            </button>
            <button
              onClick={redact}
              style={{
                padding: "6px 12px",
                fontSize: "14px",
                backgroundColor: "#ff4d4d",
                color: "white",
                border: "none",
                borderRadius: "4px",
                cursor: "pointer",
              }}
            >
              Redact
            </button>
        </>
        
      )}
      </div>
       {/* Display the redacted audio */}
{redactedAudio &&
        <div>
          <h3>Redacted Audio:</h3>
          <audio key={redactedAudio} controls>
            <source src={redactedAudio} type="audio/mpeg"/>
            Your browser does not support the audio element.
          </audio>
        </div>
}

    </div>
  );
};

// Example usage
const AudioRedactionUI = () => {
  const [transcript, setTranscript] = useState();
  const [redactedAudio, setRedactedAudio] = useState(null);

  useEffect(() => {
    console.log("transcript changed...", transcript?[0] : "empty")
  }, [transcript]);

  useEffect(() => {
    if (!transcript) {
      // Fetch the transcript from the Flask backend
      fetch("http://127.0.0.1:5000/api/transcript")
        .then((response) => response.json())
        .then((data) => {
          setTranscript(data.transcript);
          console.log(data.transcript)
        })
        .catch((error) => console.error("Error fetching transcript:", error));

        console.log("App::useEffect called...");
    }
  }, [transcript]);

  // if (!transcript) return <p>Loading transcript...</p>;

  return (<div className="transcript-container-scrollable">
    <TranscriptDisplay transcript={transcript} redactedAudio={redactedAudio} setRedactedAudio={setRedactedAudio}></TranscriptDisplay>
  </div>
  );
};

export default AudioRedactionUI;