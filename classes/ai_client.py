from abc import ABC, abstractmethod
from google import genai
#import warnings

class BaseLLMClient(ABC):
    @abstractmethod
    def generate_response(self, prompt: str) -> str:
        pass

class GeminiClient(BaseLLMClient):
    def __init__(self, model_name: str = "gemini-3.6-flash"):
        self.client = genai.Client(api_key="")
        self.model_name = model_name

    def generate_response(self, prompt: str) -> str:
        interaction = self.client.interactions.create(
            model=self.model_name,
            input=prompt,
            response_format={
                "type": "text",
                "mime_type": "application/json"
            }
        )
        if not interaction.output_text:
            raise ValueError("Gemini returned no text.")
        return interaction.output_text