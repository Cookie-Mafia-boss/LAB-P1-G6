#$env:GEMINI_API_KEY="your_actual_api_key_here" ===> initialise this first.....
#docker run --rm -it -e GEMINI_API_KEY="your_actual_gemini_api_key" food-waste-management-system
import json
from classes.ai_prompt import BasePromptBuilder, KitchenPromptBuilder
from classes.ai_client import BaseLLMClient, GeminiClient
from classes.ai_data_validation import AISuggestionResponse, get_safe_default

class AIService:
    def __init__(self, client: BaseLLMClient = None, prompt_builder: BasePromptBuilder = None):
        # Injects dependencies rather than creating them here
        self.client = client or GeminiClient()
        self.prompt_builder = prompt_builder or KitchenPromptBuilder()

    def process_inventory(self, inventory: list) -> AISuggestionResponse:
        """Orchestrates: Build Prompt -> Call API -> Parse -> Validate -> Apply Domain Rule"""
        
        # If inventory is empty, it will return a safe default immediately
        if not inventory:
            return get_safe_default()

        prompt = self.prompt_builder.build_prompt(inventory)

        try:
            # 1. Calls the API
            raw_response = self.client.generate_response(prompt)
            
            # 2. Parse JSON (It can also handle a malformed JSON safely)
            parsed_data = json.loads(raw_response)
            
            # 3. Validates using Pydantic
            validated_response = AISuggestionResponse(**parsed_data)
            
            # 4. Apply a Multi-Condition Domain Rule
            validated_response = self._apply_domain_rules(validated_response)
            
            return validated_response

        except Exception as e:
            #Handles connection/parsing/validation failures
            print(f"[AI Layer Error] Processing failed: {e}")
            return get_safe_default()

    def _apply_domain_rules(self, response: AISuggestionResponse) -> AISuggestionResponse:
        """
        The Multi-condition rule uses two or more fields from the AI response.
        Rule: If Risk Level is 'High' AND the days_remaining <= 2, 
        it will override the action to force an immediate alert.
        """
        for item in response.items:
            if item.waste_risk_level.lower() == "high" and item.days_remaining <= 2:
                item.recommended_action = "CRITICAL: Use it immediately before its expiry!"
        
        return response