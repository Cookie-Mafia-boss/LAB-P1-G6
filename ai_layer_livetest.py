# ai_layer_livetest.py
from ai_layer import AIService

# This will now work because we added '= None' in the __init__
ai_service = AIService() 

inventory = [{"Food_Name": "Milk", "Status": "EXPIRING"}, {"Food_Name": "Apples", "Status": "FRESH"}]

print("Calling live Gemini API...")
result = ai_service.process_inventory(inventory)

print(result.model_dump_json(indent=2))