from google import genai
from google.genai import types
from datetime import date, datetime
import csv
from tools import *
from dotenv import load_dotenv
import os

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=GEMINI_API_KEY)
TODAY = date.today().strftime('%d/%m/%Y')

SYSTEM_INSTRUCTION = f"""Today is {TODAY}.
                        You are a food waste management assistant for a canteen/food court.
                        You do NOT have direct access to the inventory data. To see current stock,
                        you must call the expiry_alert tool. Always call it before answering any
                        question about food, inventory, or expiry — never guess or say the database
                        is empty without calling the tool first."""

RESSUPPLYING_INSTRUCTION = f"""Your task is to open the inventory, analyze
                            the data, especially the  
                            and generate Resupplying Recommendations (Prevents overstocking of food)"""

CATEGORY_INSTRUCTION = f""" Your task is to open the inventory, analyze
                            the data, and split/categorize each item based on it's category (eg. dairy products, vegetables, meat, ext)."""

PREDICTIONI_ALLERT_INSTRUCTION = f"""Your task is to open the inventory, analyze
                                the data, and make a prediction of which item should we use prioritize in using them first."""

MODEL = "gemini-3.5-flash-lite"


def AI_Model(prompt: str):
    chat = client.chats.create(
        model=MODEL,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            temperature=0.3,
            tools=list(TOOLS.values()),
        )
    )
    response = chat.send_message(prompt)
    return response.text

    




# print(expiry_alert())

print("--- Direct tool test ---")
print(expiry_alert())

print("--- AI test ---")
result = AI_Model(CATEGORY_INSTRUCTION)
print(result)

# def waste_trends():




# def Resupplying_Recommendations():









#Tools





