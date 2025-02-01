# Building a Deployable System for Voice Anonymization
MIT Center for Constructive Communication, IAP 2025

Faculty Supervisor: Deb Roy
Direct Supervisor: Wonjune Kang
UROP Student: Grant Hu

**Overview**
The MIT Center for Constructive Communication (CCC) is working on developing a system that can anonymize speakers’ voices by masking attributes of their vocal identity from speech utterances. CCC currently has a system that is based on a voice conversion (VC) model, which can transform a speech utterance to take on the timbre of another person while preserving the underlying linguistic content and prosodic elements (e.g., emotion, rhythm, intonation). Another option in the current anonymization toolkit is text-to-speech (TTS) synthesis, which also removes the prosodic elements from the original speech.

However, speech synthesis and editing technologies have improved significantly since the initial version of this framework was developed. CCC is interested in exploring these new technologies to extend and improve upon the currently existing framework. There is a wide variety of improvements that could be incorporated, ranging from relatively simple (adding audio redaction capabilities, replacing the VC and TTS models with better performing ones) to more exploratory (modifying the UI to allow users to characterize the synthetic voices for VC or TTS, adding in additional modules such as speech enhancement).

This UROP will involve working together with CCC research and prototype engineering staff in order to implement extensions to the voice anonymization pipeline as described above. Beyond implementing the new speech and audio processing capabilities, the goal will be to develop a modularized repository and/or package that can be used in demos or real-world deployment settings.

To run this,
1. In the ```backend``` directory, run ```python app.py``` Failure to do so will not fetch the transcript!
2. Go to ```frontend``` directory.
3. ```npm run build```
4. ```cd build```
5. ```python3 -m http.server 9000```

