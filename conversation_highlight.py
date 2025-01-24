import librosa
import matplotlib.pyplot as plt
import json
import numpy as np


class ConversationHighlight:
    """
    Creates a Conversation Highlight Object.

    @arg share_location = String? metadata
    @arg share_text = String? metadata
    @arg transformed = boolean, if highlight is transformed
    @arg auto_gen = boolean, if highlight is auto generated
    @arg transcript = String, transcript of highlight
    @arg audio = NumPy array, audio
    @arg conv_rec = String?
    @arg sharer_iden = String
    @arg og_hr = String?
    @arg primary_speaker_iden = String or Identity object?
    @arg add_speaker_iden = String or Identity object?
    @arg tags = String?
    """
    def __init__(self, share_location=None, share_text=None, 
                 transformed=False, auto_gen=False, 
                 transcript="", audio=None, conv_rec=None, 
                 sharer_iden=None, og_hr=None, 
                 primary_speaker_iden=None, add_speaker_iden=None,
                 tags=None):
        self.share_location = share_location
        self.share_text = share_text
        self.transformed = transformed
        self.auto_gen = auto_gen
        self.transcript = transcript
        self.audio = audio
        self.conv_rec = conv_rec
        self.sharer_iden = sharer_iden
        self.og_hr = og_hr
        self.primary_speaker_iden = primary_speaker_iden
        self.add_speaker_iden = add_speaker_iden
        self.tags = tags

    def __str__(self):
        """
        Returns a readable string format of a Conversation Highlight.
        """
        output = f'''{self.share_location},
        {self.share_text},
        {self.transformed},
        {self.auto_gen},
        {self.transcript},
        {self.audio},
        {self.conv_rec},
        {self.sharer_iden},
        {self.og_hr},
        {self.primary_speaker_iden},
        {self.add_speaker_iden},
        {self.tags})'''
        return output


def plot_spectogram(path):
    """
    Plots a spectogram given the path to an audio file.

    Args:
        path (String): path to audio file
    
    Returns:
        None
    """
    y, sr = librosa.load(path)
    S = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=128, fmax=8000)
    S_dB = librosa.power_to_db(S, ref=np.max)
    plt.figure(figsize=(10, 4))
    librosa.display.specshow(S_dB, sr=sr,
                             x_axis='time', y_axis='mel', fmax=8000)
    plt.colorbar(format='%+2.0f dB')
    plt.title('Mel spectrogram')
    plt.tight_layout()
    plt.show()


def mp3_to_ndarray(path, samp_rate):
    """
    Converts an mp3 file to a numpy 2D array.

    Args:
        path (String): path to audio file
        samp_rate (int): sampling rate, in samples/sec

    Returns:
        y: (numpy.ndarray): NumPy representation of 2D array
    """
    y, _ = librosa.load(path, sr=samp_rate)
    return y


def generate_transcript(file_path):
    """
    Extracts transcript from Fora .json file of a highlight

    Args:
        file_path (String): path to .json file downloaded from Fora
    
    Returns:
        transcript (String): string containing the entire transcript
        of the highlight
    """
    with open(file_path, 'r') as file:
        data = json.load(file)
    transcript = ""
    for group in data["snippets"][0]["words"]:
        transcript += group["word"] + " "
    return transcript.strip()
