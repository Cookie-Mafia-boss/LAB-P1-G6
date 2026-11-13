# test_ai.py
from ai_layer import AIService
from classes.ai_prompt import KitchenPromptBuilder
from classes.ai_client import BaseLLMClient

# Create a Mock Client (Inheritance)
class MockLLMClient(BaseLLMClient):
    def generate_response(self, prompt: str) -> str:
        assert "Inventory Data" in prompt, "Prompt is missing inventory data!"
        assert "Milk" in prompt, "Prompt is missing the Milk record!"

        # Simulated AI response
        return """
        {
            "items": [
                {"food_name": "Milk", "waste_risk_level": "High", "days_remaining": 1, "recommended_action": "Drink soon"},
                {"food_name": "Apples", "waste_risk_level": "Low", "days_remaining": 10, "recommended_action": "Monitor"}
            ],
            "waste_trend_summary": "You are saving apples but wasting dairy.",
            "resupply_recommendations": "Buy less milk.",
            "recipe_suggestions": ["Pancakes", "Smoothie"]
        }
        """

# Setup with MOCK client (No API key needed!)
mock_client = MockLLMClient()
builder = KitchenPromptBuilder()
ai_service = AIService(client = mock_client, prompt_builder = builder)

# Test Data
inventory = [{"Food_Name": "Milk", "Status": "EXPIRING"}, {"Food_Name": "Apples", "Status": "FRESH"}]

# Run
result = ai_service.process_inventory(inventory)

print("--- AI RESPONSE ---")
for item in result.items:
    print(f"{item.food_name}: {item.recommended_action} (Risk: {item.waste_risk_level})")

# Output will show the Domain Rule worked:
# Milk: CRITICAL: Use it immediately before its expiry! (Risk: High)  <-- Overridden by rule!
# Apples: Monitor (Risk: Low)