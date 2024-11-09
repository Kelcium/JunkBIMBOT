import speech_recognition as sr
from openai import OpenAI

class SRClient():

    def __init__(self, client):
        r = sr.Recognizer()
        mic = sr.microphone(device_index=0)
        r.dynamic_energy_threshold = False
        r.energy_threshold = 100
        
        self.client = client
