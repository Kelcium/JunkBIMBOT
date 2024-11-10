from elevenlabs import play
from elevenlabs.client import ElevenLabs

class TTSClient():

    def __init__(self, key, voice='Brian'):
        self.client = ElevenLabs(api_key=key)
        self.voice = voice

    def tts(self, str_in):
        audio = self.client.generate(
            text=str_in,
            voice=self.voice,
            model='eleven_multilingual_v2'
        )
        play(audio)

if __name__ == '__main__':
    key = "placeholder"
    ttsc = TTSClient(key)
    ttsc.tts('I am going to turn into a truck now')