from supertonic import TTS

tts = TTS(auto_download=True)
style = tts.get_voice_style(voice_name="M1")
def generate_speech_from_text(text:str) -> None:
    wav, _ = tts.synthesize(text, voice_style=style, lang="na")
    return wav