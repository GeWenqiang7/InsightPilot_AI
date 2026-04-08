from openai import OpenAI

class LLMClient:

    def __init__(self):
        self.client = OpenAI()

    def generate(self, prompt):

        response = self.client.chat.completions.create(
            model="gpt-4.1",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )

        return response.choices[0].message.content