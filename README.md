# vc

Known Bugs:
1. When a word is selected in single-select, clicking multi-select changes the displayed selected word to its index, unhighlights it, and does not select all instances of the word.
2. Sometimes there is a one second delay due to the naming of the file. Looking to implement differing way of naming file.

Potential future improvements:
1. Add option to convert with voices from ElevenLabs API
2. Run on localhost:3000 instead of current running method
3. When multiple consecutive words are selected, consider redacting in one bleep instead of each individual word

To run this,
1. Go to ```frontend``` directory.
2. ```npm run build```
3. ```cd build```
4. ```python3 -m http.server 9000```

