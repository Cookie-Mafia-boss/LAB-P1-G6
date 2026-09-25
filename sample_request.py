import requests
import json

#Created by Moses and Jerome

def get_recommendations(prompt, model="qwen2.5-coder:1.5b"):
    system_prompt = (
        "You assign as food waste reduction assistant to monitor the canteen/restaurant's food storage."
        "You are assigned to check the following inputs such as the expiry date given."
        "Given a list of food items nearing its expiry, suggest your users concrete ways to use them up — recipes, menu specials, or staff meals."
        "NEVER suggest the food that has been already expired on the date itself and after."
        "Form your answers into a few short bullet points per item for the users' readability."
        "Thanks!"
    )
    try:
        r = requests.post(
            "http://localhost:11434/api/chat",
            json={
            "model": model,
            "messages": [
               {"role": "system", "content": system_prompt},
               {"role": "user", "content": prompt}],
               "stream": False}, timeout = 60
        )
        r.raise_for_status
        data = r.json()
        return data.get("message", {}).get("content", "[no content returned]")
    except requests.RequestException as e:
        return f"[request failed: {e}]"


        
    return r.json()["message"]["content"]

print(get_recommendations("Items nearing expiry: "))