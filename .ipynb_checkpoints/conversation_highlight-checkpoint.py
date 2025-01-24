import librosa
import matplotlib.pyplot as plt
import numpy as np


class ConversationHighlight:
    """
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
    @arg codes = String?
    """
    def __init__(self, share_location=None, share_text=None, 
                 transformed=False, auto_gen=False, 
                 transcript="", audio=None, conv_rec=None, 
                 sharer_iden=None, og_hr=None, 
                 primary_speaker_iden=None, add_speaker_iden=None,
                 codes=None):
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
        self.codes = codes


def plot_spectogram(ndarray, sr):
    librosa.feature.melspectrogram(y=ndarray, sr=sr)
    plt.figure(figsize=(10, 4))
    librosa.display.specshow(librosa.power_to_db(ndarray, ref=np.max), y_axis='mel', fmax=8000, x_axis='time')
    plt.colorbar(format='%+2.0f dB')
    plt.title('Mel spectrogram')
    plt.tight_layout()
    plt.plot()


def mp3_to_ndarray(path, samp_rate):
    y, sr = librosa.load(path, sr=samp_rate)
    return (y, sr)
