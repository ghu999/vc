import numpy

class ConversationHighlight:
    def __init__(self, share_location=None, share_text=None, transformed=False, auto_gen=False, 
                 transcript="", audio=None, conv_rec=None, share_iden=None, og_hr=None, 
                 primary_speaker_iden=None, additional_speaker_iden=None,
                 codes=None):
        self.share_location = share_location
        self.share_text = share_text
        self.transformed = transformed
        self.auto_gen = auto_gen
        self.transcript = transcript
        self.audio = audio
        self.conv_rec = conv_rec
        self.share_iden = share_iden
        self.og_hr = og_hr
        self.primary_speaker_iden = primary_speaker_iden
        self.additional_speaker_iden = additional_speaker_iden
        self.codes = codes
    
