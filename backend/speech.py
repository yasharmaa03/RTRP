"""
speech.py - Speech-to-text conversion using SpeechRecognition library.
Accepts audio file uploads and converts them to text using Google Web Speech API.
"""

import os
import tempfile
import speech_recognition as sr
from pydub import AudioSegment


def convert_audio_to_wav(input_path: str) -> str:
    """
    Convert any audio format (webm, mp3, ogg, etc.) to WAV format.
    Returns the path to the converted WAV file.
    """
    wav_path = input_path.rsplit(".", 1)[0] + ".wav"
    audio = AudioSegment.from_file(input_path)
    audio.export(wav_path, format="wav")
    return wav_path



# Supported languages for Google Speech Recognition
LANGUAGE_CODES = {
    "en": "en-IN",   # English (India)
    "hi": "hi-IN",   # Hindi
    "te": "te-IN",   # Telugu
}


def speech_to_text(audio_bytes: bytes, filename: str = "audio.webm", language: str = "en") -> str:
    """
    Convert audio bytes to text.

    Args:
        audio_bytes: Raw audio file bytes
        filename: Original filename (used to determine format)
        language: Language code — "en" (English), "hi" (Hindi), or "te" (Telugu)

    Returns:
        Transcribed text string

    Raises:
        ValueError: If speech could not be recognized
        RuntimeError: If the speech recognition service is unavailable
    """
    recognizer = sr.Recognizer()
    lang_code = LANGUAGE_CODES.get(language, "en-IN")

    # Save bytes to a temporary file
    suffix = os.path.splitext(filename)[1] or ".webm"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        # Convert to WAV if not already
        if not tmp_path.endswith(".wav"):
            wav_path = convert_audio_to_wav(tmp_path)
            os.unlink(tmp_path)  # Remove original temp file
            tmp_path = wav_path

        # Perform speech recognition in the selected language
        with sr.AudioFile(tmp_path) as source:
            audio_data = recognizer.record(source)

        text = recognizer.recognize_google(audio_data, language=lang_code)
        return text

    except sr.UnknownValueError:
        raise ValueError("Could not understand the audio. Please speak clearly and try again.")
    except sr.RequestError as e:
        raise RuntimeError(f"Speech recognition service error: {str(e)}")
    finally:
        # Clean up temp files
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
