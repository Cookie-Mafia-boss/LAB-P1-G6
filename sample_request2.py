import requests
import json

def get_recommendations(prompt, model="qwen2.5-coder:1.5b"):
    #Prompt an AI the following commands
    """user_prompt = (
        "You assign as food waste reduction assistant to monitor the canteen/restaurant's food storage."
        "You are assigned to check the following inputs such as the expiry date given."
        "Given a list of food items nearing its expiry, suggest your users concrete ways to use them up — recipes, menu specials, or staff meals."
        "NEVER suggest the food that has been already expired on the date itself and after."
        "Form your answers into a few short bullet points per item for the users' readability."
        "Thanks!"
    )"""

    user_prompt = (
        input("Please type your input: ")
    )

    try:
        data = {
            "model": model,
            "messages": [
                {"role": "system", "content": user_prompt},
                {"role": "user", "content": prompt}],
                "stream": False
                }

        r = requests.post(
            #Place API here:
            "http://localhost:11434/api/chat",
            json=data, timeout = 60
        )
        r.raise_for_status

        response_data = r.json()

        message_content = response_data.get("message", {}).get("content", "[no content returned]")

        return message_content
    except requests.RequestException as e:
        return f"[request failed: {e}]"


#Test Usage
#prompt = "Items nearing expiry: "
#recommendations = get_recommendations(prompt)
#print(recommendations)