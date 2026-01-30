#!/usr/bin/env python3
"""
Generate TTS MP3 file using gTTS and return the filename
Usage: generate_tts.py "text to speak"
Outputs: filename of generated MP3
"""
import sys
import hashlib
from gtts import gTTS
import os

if len(sys.argv) < 2:
    print("Usage: generate_tts.py 'text'")
    sys.exit(1)

text = sys.argv[1]
# Generate hash-based filename
text_hash = hashlib.md5(text.encode()).hexdigest()
filename = f"tts_{text_hash}.mp3"
filepath = f"/etc/openhab/html/{filename}"

# Generate if doesn't exist
if not os.path.exists(filepath):
    tts = gTTS(text=text, lang='da')
    tts.save(filepath)

# Output just the filename
print(filename)
