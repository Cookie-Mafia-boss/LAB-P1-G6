import json
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
        "total_items": len(inventory),
        "expired_items": expired_list,
        "expiring_soon": expiring_list,
        "raw_inventory": inventory
    }

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

        interaction = client.interactions.create(
            model="gemini-3.8-flash",
            input=prompt
        )

        print("\n--- 💡 AI Recipe & Waste Prevention Suggestions ---")
        print(interaction.output_text)

    except Exception as e:
        print(f"❌ Error calling Gemini API: {e}")