# packages
import configparser
from openai import OpenAI
import os
import sounddevice as sd
import time
import copy
from scipy.io.wavfile import write
# custom packages
from ifc_interface import IFCClient
from llm_cv import LLMCVClient
from whisperAPI import WhisperClient
from ttsAPI import TTSClient
from camclient import Camera

OpenAIKey = 'placeholder'
elevenkey = "placeholder"

# initialise main GPT client
print('Loading OpenAI Key and Client')
client = OpenAI(api_key=OpenAIKey)
# for some reason this python file only take absolute path
personality = "p.txt"
with open(personality, 'r') as file:
    mode = file.read()
messages = [{"role": "system", "content": f"{mode}"}]
print('OpenAI client loaded')

# instantiate all clients
print('|\tInitialising Clients...')
cvc = LLMCVClient(OpenAIKey, 'llm_cv_p.txt')
print('BimBot Client Initialised')
src = WhisperClient(client)
print('Whisper Client Initialised')
ttsc = TTSClient(elevenkey)
print('tts Initialised')
ifc_path = 'Kaapelitehdas_junction - Copy.ifc'
ifc = IFCClient(ifc_path)
print('Building IFC File loaded: {}'.format(ifc_path))
camc = Camera()
print('Camera Module Initialised')
print('All clients successfully initialised.')

## Initial data points
# preset locations which will be selected by the user
# represents coordinates within the building
# for the scope of this project, only 1A will return any proper results
presetcoords = {'1A':[-67000,-65000,4105]}
# item types
# currently only two are available
itemTypes = ['IfcBuildingElementProxy', 'IfcDoor']
# recording
# Sampling frequency
freq = 44100
# Recording duration. Preset as 5 seconds, should eventually be unlimited
duration = 5

separator = '\n<SEPARATOR>\n'

# generate response from input string
def llminput(str_in):
    messages.append({
        'role': 'user',
        'content': [
            {
                'type': 'text',
                'text': str_in
            }
        ]
    })
    completion = client.chat.completions.create(
        model = 'gpt-4o-mini',
        messages = messages,
        max_tokens = 300
    )
    response = completion.choices[0].message.content

    # save response into messsages
    messages.append({
        'role': 'assistant',
        'content': [
            {
                'type': 'text',
                'text': response
            }
        ]
    })

    # output response
    print(response)
    out_ls = response.split('///')
    desc = out_ls[0].strip()
    checked_id = out_ls[1].strip()
    prose = out_ls[2].strip()
    ifc.update_element_description(ifc_path, checked_id, desc)
    ttsc.tts(prose)

'''
######### MAIN LOOP STARTS HERE #########
'''
if __name__ == '__main__':
    print('|\tHello! Welcome to BimBot!')
    print('|\tPlease begin inventory inspection for {}.'.format(ifc_path))
    while True:
        action = input('Select course of action - ADD, INSPECT: ')

        if action.upper() == 'INSPECT':
            print('Inspection mode. Please wait...')
            inspectioncoords = copy.deepcopy(presetcoords)
            while len(inspectioncoords) != 0:
                time.sleep(1)
                print('|\tThe available inspection points are as follows: ')
                for coord in inspectioncoords:
                    print(coord)
                coord_input = input('Please select your inspection point: ')
                if coord_input in inspectioncoords.keys():
                    coords = inspectioncoords[coord_input]
                    all_elements = ifc.get_nearby_elements(itemTypes, coords)
                    all_str = ifc.dict_to_string(all_elements)
                    str_in = "Output items that require inspection" + separator + all_str
                    llminput(str_in)
                    inspection = input('Proceed with inspection? (Y/N) ')
                    if inspection.upper() == 'Y':
                        print('Proceed with inspection')
                        tag = ''
                        file_input_query = input('Upload files? (Y/N) ')
                        if file_input_query.upper() == 'Y':
                            formattype = input('Adding file. Choose filetype - IMG: ')
                            if formattype.upper() == 'IMG':
                                # take in image from camera
                                # take image
                                # save image
                                # return image path
                                img_path = 'Pictures/temp.png'
                                camc.take_pic(img_path)
                                # format the input string
                                tag = cvc.transcribe(img_path)
                        obj_dict = ifc.get_nearby_elements(['IfcBuildingElementProxy'], coords)
                        obj_str = ifc.dict_to_string(obj_dict)
                        str_in = tag + separator + obj_str
                        adding_audio = input('Adding audio? (Y/N) ')
                        if adding_audio.upper() == 'Y':
                            print("Recording...")
                            recording = sd.rec(int(duration * freq), 
                                            samplerate=freq, channels=2)
                            sd.wait()
                            audio_path = 'Audio/temp.wav'
                            write(audio_path, freq, recording)
                            # transcription = WhisperClient.process_audio(audio_path)
                            transcription = 'The double door is in good condition. It has been inspected.'
                            str_in = transcription + separator + str_in
                        llminput(str_in)
                    del inspectioncoords[coord_input]
                else:
                    print("Invalid area code! Please try again.")
            else:
                print("Inspection Complete! Select next action.")

        elif action.upper() == 'ADD':
            formattype = input('Adding item. Choose filetype - IMG: ')
            if formattype.upper() == 'IMG':
                # take in image from camera
                # take image
                # save image
                # return image path
                img_path = 'Pictures/temp.png'
                camc.take_pic(img_path)
                # format the input string
                tag = cvc.transcribe(img_path)
                print('Please provide coordinates for this new item')
                presetask = input('Use presets? (Y/N) ')
                if presetask.upper() == 'Y':
                    coord_input = input('Select preset: ')
                    coords = presetcoords.get(coord_input)
                elif presetask.upper() == 'N':
                    x_coord = input('x: ')
                    y_coord = input('y: ')
                    z_coord = input('z: ')
                    coords = [x_coord, y_coord, z_coord]
                print('Retrieving IFC data')
                obj_dict = ifc.get_nearby_elements(['IfcBuildingElementProxy'], coords)
                print('IFC data retrieved')
                obj_str = ifc.dict_to_string(obj_dict)
                str_in = tag + separator + obj_str
                adding_audio = input('Adding audio? (Y/N) ')
                if adding_audio.upper() == 'Y':
                    print("Recording...")
                    recording = sd.rec(int(duration * freq), 
                                    samplerate=freq, channels=2)
                    sd.wait()
                    audio_path = 'Audio/temp.wav'
                    write(audio_path, freq, recording)
                    # transcription = WhisperClient.process_audio(audio_path)
                    transcription = 'This is a fire extinguisher. It must be replaced as the nozzle is damaged. Please add this as a new item'
                    str_in = transcription + separator + str_in
                llminput(str_in)