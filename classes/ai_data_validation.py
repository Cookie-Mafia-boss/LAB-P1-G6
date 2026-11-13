from pydantic import BaseModel, Field
from typing import List

# 1. Define the schema for individual inventory items
class AIItemAnalysis(BaseModel):
    food_name: str = Field(description = "Name of the food item")
    waste_risk_level: str = Field(description = "High, Medium, or Low risk of being wasted")
    days_remaining: int = Field(description = "Estimated days until expiration")
    recommended_action: str = Field(description = "The immediate action (e.g., 'Cook Today', 'Freeze', 'Consume Soon')")

# 2. Define the schema for the overall AI response
class AISuggestionResponse(BaseModel):
    items: List[AIItemAnalysis] = Field(description = "List of analyzed food items")
    waste_trend_summary: str = Field(description = "A brief summary of how much food is wasted vs saved")
    resupply_recommendations: str = Field(description = "Suggestions to prevent overstocking")
    recipe_suggestions: List[str] = Field(description = "2-3 actionable recipes prioritizing high-risk items")

# 3. The Safe Default Object
# Returned if the API fails so the app doesn't crash
def get_safe_default() -> AISuggestionResponse:
    return AISuggestionResponse(
        items=[],
        waste_trend_summary="AI Unavailable. Please review inventory manually.",
        resupply_recommendations="AI Unavailable.",
        recipe_suggestions=["AI Unavailable. Please check back later."]
    )