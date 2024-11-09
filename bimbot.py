# packages
import configparser
from openai import OpenAI
import os
# custom packages
from ifc_interface import IFCClient
from llm_cv import LLMCVClient

# config
#config = configparser.ConfigParser()
#config.read('guesswhat.ini')
#language = config.get('INITIALISATION', 'LANGUAGE')
#test = config.getboolean('TEST', 'TEST')

#classes = config.get('INITIALISATION', 'CLASSES')

# initialise main GPT client
client = OpenAI(api_key=OpenAIKey)
# for some reason this python file only take absolute path
personality = "C:/Users/gneri/OneDrive/Documents/00 - Compactor/01 - uni/99.990 - Aalto/Junction/JunctionBIMBOT\p.txt"
with open(personality, 'r') as file:
    mode = file.read()
messages = [{"role": "system", "content": f"{mode}"}]

# instantiate all clients
cvc = LLMCVClient(OpenAIKey, 'llm_cv_p.txt')
#src = WhisperClient(client)
ifc_path = 'Kaapelitehdas_junction - Copy.ifc'
ifc = IFCClient(ifc_path)

'''
######### MAIN LOOP STARTS HERE #########
'''

# take in image from camera
# take image
# save image
# return image path
img_path = 'Pictures/photo_2024-11-09_19-28-48.jpg'
audio_path = ''
coords = [-67000,-65000,4105]

# format the input string
tag = cvc.transcribe(img_path)
#verbal = src.process_audio(audio_path)
verbal = 'This is the Fire Extinguisher. It must be replaced as the nozzle is damaged'
obj_dict = ifc.get_nearby_elements(['IfcBuildingElementProxy'], coords)
obj_str = ifc.dict_to_string(obj_dict)
separator = '\n<SEPARATOR>\n'
str_in = verbal + separator + tag + separator + obj_str
print(str_in)

# generate response from input string
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

# check if update is correct
all_stuff = ifc.get_nearby_elements(['IfcBuildingElementProxy'], coords)
all_str = ifc.dict_to_string(all_stuff)
print(all_str)


# class object for BIM input
# Retrieve a dictionary. Each key should reference an area code, and the item
# should be another dictionary 
# z = 4105
coordinate_presets = {"1A": [-67000,-65000,4105]}

# if test == True:
#     VideoClient = WhisperClient(client, language)
#     video_input = "sample.mp4"

#     transcription = VideoClient.process_video(video_input)
#     #cvOut = CVClient.video_CV(video_input)

#     print(transcription)
'''
if __name__ == '__main__':
    client = OpenAI(api_key=OpenAIKey)
    personality = 'prompt.txt'
    with open(personality, 'r') as file:
        mode = file.read()
    personality_message = [{"role": "system", "content": f"{mode}"}]

    completion = client.chat.completions.create(
        model='gpt-3.5-turbo',
        messages=personality_message
    )
    print("Personality updated!")
    # ifcdata = os.listdir('./IFCfiles')
    # print("Select the IFC file to open!")
    IFC = IFCClient('Kaapelitehdas_junction - Copy.ifc')
    
    all_checks = False
    while all_checks == False:
        messages = []
        area = input("Indicate your current area code: ")
        itemTypes = ['IfcBuildingElementProxy', 'IfcDoor']
        if area in coordinate_presets.keys():
            area_objects = IFC.get_nearby_elements(types=itemTypes, coords=coordinate_presets[area])
            messages.append({"role" : "user", "content" : area_objects})
            print(messages)
        else:
            raise Exception("Area code not valid!")

        # gpt call
        completion = client.chat.completions.create(
            model='gpt-3.5-turbo',
            messages=messages
        ) 
        
        # choose and print response
        response = completion.choices[0].message.content
        print(response)
        # for item in response:
        #     print(item)

        if response[0] == False:
            print("")
'''