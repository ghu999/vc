class Identity:
    def __init__(self, name="", pfp=None, mero_tags=None,voice_color=None,default=False,
                 conversion_voice=None,parent=None):
        self.name = name
        self.pfp = pfp
        self.mero_tags = mero_tags
        self.voice_color = voice_color
        self.default = default
        self.conversion_voice = conversion_voice
        self.parent = parent