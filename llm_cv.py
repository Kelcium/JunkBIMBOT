import base64
import openai

class LLMCVClient():
   
    # initilialise client
    def __init__(self, key, personality_path) -> None:
        self.key = key
        with open(personality_path, 'r') as file:
             self.mode = file.read()
        self.msgs = [{"role": "system", "content": f"{self.mode}"}]
        self.client = openai.OpenAI(api_key=self.key)
        return

    # Function to encode the image
    def _encode_image(self, image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
        
    def transcribe(self, image_path):
        base64_image = self._encode_image(image_path)
        # append imagae to chat
        self.msgs.append({
                'role': 'user',
                'content': [
                    {
                        'type': 'image_url',
                        'image_url': {
                            'url': f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            })
            # generate response
        response = self.client.chat.completions.create(
            model = 'gpt-4o-mini',
            messages = self.msgs,
            max_tokens = 300
        )
        return response.choices[0].message.content

if __name__ == '__main__':
    img_path = 'Pictures/photo_2024-11-09_19-28-48.jpg'
    yhkey = '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'
    cvc = LLMCVClient(yhkey, 'llm_cv_p.txt')
    tag = cvc.transcribe(img_path)
    print(tag)

