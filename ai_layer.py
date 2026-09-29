import json
from google import genai
import warnings


def _parse_ai_response(response_text: str) -> dict:
    """Parse AI response into 4 sections based on headers."""
    sections = {"recipes": "", "waste_trends": "", "immediate_action": "", "resupply": ""}
    current = None

    keywords = {
        "recipe": "recipes",
        "waste trend": "waste_trends",
        "waste prevention": "waste_trends",
        "immediate action": "immediate_action",
        "resupply": "resupply",
        "restock": "resupply"
    }

    for line in response_text.split('\n'):
        lower = line.lower().strip()
        for kw, section in keywords.items():
            if kw in lower and (line.startswith('#') or line.startswith('**') or line.isupper()):
                current = section
                break
        if current:
            sections[current] += line + '\n'

    if not any(sections.values()):
        sections["recipes"] = response_text

    return sections


def get_ai_suggestions(inventory, expiring_items):
    """Call Gemini API and return parsed sections."""
    if not inventory:
        return None

    expired_list = [item['Food_Name'] for item in inventory if item['Status'] == 'EXPIRED']
    expiring_list = [item['Food_Name'] for item in expiring_items]

    payload = {
        "total_items": len(inventory),
        "expired_items": expired_list,
        "expiring_soon": expiring_list,
        "raw_inventory": inventory
    }

    prompt = f"""
    You are an AI kitchen assistant and food waste prevention specialist.
    Based on this inventory data, provide a structured response with these EXACT section headers:

    ### RECIPES TO PRIORITIZE
    2-3 actionable, delicious recipes using items with fewest days remaining.

    ### WASTE TRENDS
    How much food wasted due to expiry / potentially wasted / saved before expiry.

    ### IMMEDIATE ACTION REQUIRED
    Items requiring immediate attention.

    ### RESUPPLY RECOMMENDATIONS
    Prevent overstocking suggestions.

    Inventory Data:
    {json.dumps(payload, indent=2)}
    """
            
    warnings.filterwarnings(
        "ignore",
        message="Interactions usage is experimental",
        category=UserWarning,
    )

    try:
        client = genai.Client()
        interaction = client.interactions.create(
            model="gemini-3.8-flash",
            input=prompt
        )
        response_text = interaction.output_text
    except Exception as e:
        return {"error": str(e)}

    return _parse_ai_response(response_text)