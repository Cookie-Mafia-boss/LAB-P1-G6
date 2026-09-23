from ollama import chat
from datetime import date, datetime
import csv
from tools import *

SYSTEM_INSTRUCTION = f"""You are a food waste management assistant for a canteen/food court. 
                        You will be given a food inventory/database, your main task is to review the inventory, 
                        and give an expiry alert for any item expiring within 5 days from today. 
                        Today's date is {date.today().strftime('%d/%m/%Y')} without the time. Please don't include the time
                        You additional tasks are:
                        AI can help to generate these outputs:
                        Waste Trends (How much food has been wasted due to expiry/How much food you have saved before its expiry.)
                        Resupplying Recommendations (Prevents overstocking of food)
                    """
MODEL = "qwen3:1.7b"




def AI_Model(prompt: str):
    messages = [{
                "role": "system",
                "content": SYSTEM_INSTRUCTION,
            },
            {
                "role": "user",
                "content": prompt,
            }]
    response = chat(
        model = MODEL,
        messages = messages,
        tools=list(TOOLS.values()),
        think=False,
        stream=False,
        options={
            "temperature": 0.3
        }
    )

    tool_calls = response.message.tool_calls or []
    if tool_calls:
        messages.append(response.message)
        for call in response.message.tool_calls or []:
            result = TOOLS[call.function.name](**call.function.arguments)
            messages.append({"role": "tool", "tool_name": call.function.name, "content": result})

        final_response = chat(
                model=MODEL,
                messages=messages,
                tools=list(TOOLS.values()),
                think=False,
                stream=False,
                options={"temperature": 0.3}
            )
        return final_response.message.content

    return response.message.content




print(expiry_alert())

result = AI_Model("can you tell me what food that will approach expiry? just give me 5")
print(result)

# def waste_trends():




# def Resupplying_Recommendations():









#Tools





