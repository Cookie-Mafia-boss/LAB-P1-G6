from abc import ABC, abstractmethod
import json

class BasePromptBuilder(ABC):
    @abstractmethod
    def build_prompt(self, inventory: list) -> str:
        pass

class KitchenPromptBuilder(BasePromptBuilder):
    def build_prompt(self, inventory: list) -> str:
        inventory_json = json.dumps(inventory, indent=2)
        
        # We explicitly instruct the AI to return JSON matching our schema
        prompt = f"""
        You are an AI kitchen assistant and food waste prevention specialist.
        Analyze the following inventory data. 
        
        You MUST return the response as a valid JSON object matching this exact schema:
        {{
            "items": [
                {{
                    "food_name": "string",
                    "waste_risk_level": "High/Medium/Low",
                    "days_remaining": integer,
                    "recommended_action": "string"
                }}
            ],
            "waste_trend_summary": "string",
            "resupply_recommendations": "string",
            "recipe_suggestions": ["string", "string"]
        }}

        Inventory Data:
        {inventory_json}
        """
        return prompt