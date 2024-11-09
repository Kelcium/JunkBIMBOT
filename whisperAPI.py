from moviepy.editor import VideoFileClip as vfc 

class WhisperClient:

    def __init__(self, client, language='English'):
        self.language = language
        self.client = client

    def process_audio(self, audiofile):
        audio_to_process = open(audiofile, "rb")
        if self.language == 'English':
            transcription = self.client.audio.transcriptions.create(
                model="whisper-1", file=audio_to_process)
        else:
            transcription = self.client.audio.translations.create(
                model="whisper-1", file=audio_to_process)
        return transcription.text

    def process_video(self, video):
    
        # Load video file
        video_extract = vfc(video)

        # Extract audio
        audio_extract = video_extract.audio

        # Write audio to a separate file
        audio = "./audiooutput/audio.mp3"
        audio_extract.write_audiofile(audio)

        # Process and extract audio transcription
        transcription = self.process_audio(audio)

        audio_extract.close()
        video_extract.close()

        return transcription