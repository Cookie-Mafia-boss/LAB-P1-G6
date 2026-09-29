import json
<<<<<<< HEAD
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
=======
from rich import print

# AI API (pip install google-genai)
from google import genai


# ==========================================
# AI LAYER (Interactions API)
# ==========================================
def get_ai_suggestions(inventory, expiring_items):
    """Sends food inventory payload to Gemini using the Interactions API."""
    print("\n🤖 [bold cyan]Analyzing Inventory with AI...[/bold cyan]")
    
    if not inventory:
        print("⚠️ Inventory is empty. Add items to analyze with the AI model.")
        return

    # STEP 1: Extract and prepare data for your AI payload
    expired_list = [item['Food_Name'] for item in inventory if item['Status'] == 'EXPIRED']
    expiring_list = [item['Food_Name'] for item in expiring_items]
    
    payload_data = {
>>>>>>> ccb4b06753ff59e084999f7c2bba9faa1945c0df
        "total_items": len(inventory),
        "expired_items": expired_list,
        "expiring_soon": expiring_list,
        "raw_inventory": inventory
    }

<<<<<<< HEAD
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
=======
    # STEP 2: Format the payload dictionary into a string prompt
    prompt = f"""
    You are an AI kitchen assistant and food waste prevention specialist.
    Based on this inventory data:
        1. Suggest 2-3 actionable, delicious recipes to prioritize using up items with the fewest days remaining.
        2. Provide Waste Trends (How much food has been wasted due to expiry or will potentially be wasted/How much food you have saved before its expiry.)
        3. Call out any items requiring immediate action.
        4. Suggest Resupplying Recommendations (Prevent overstocking of food)


    Inventory Data:
    {json.dumps(payload_data, indent=2)}
    """

    # STEP 3: Call the Interactions API
    try:
        client = genai.Client()

>>>>>>> ccb4b06753ff59e084999f7c2bba9faa1945c0df
        interaction = client.interactions.create(
            model="gemini-3.8-flash",
            input=prompt
        )
<<<<<<< HEAD
        response_text = interaction.output_text
    except Exception as e:
        return {"error": str(e)}

    return _parse_ai_response(response_text)
=======

        print("\n--- 💡 AI Recipe & Waste Prevention Suggestions ---")
        print(interaction.output_text)

    except Exception as e:
        print(f"❌ Error calling Gemini API: {e}")
>>>>>>> ccb4b06753ff59e084999f7c2bba9faa1945c0df
