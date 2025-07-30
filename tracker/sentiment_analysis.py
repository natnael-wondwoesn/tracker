import os
import json
import requests
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables from .env
load_dotenv()

# Set up API keys
GEMINI_API_KEY = os.getenv("API_KEY")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash-002")

def rateSentence(text):
    prompt = f"""
        Analyze the following sentence and return a JSON object with two fields: "positive" and "negative",
        each representing the percentage (from 0 to 100) of how positive or negative the sentence is.
        The percentages must sum to 100.
        
        If the sentence is having hard time it is ok, it is mostly positive, only if it is a bad advice rate it as negative.
        If the sentence is a bad advice or harmful, rate it as negative.
        {text}
        """
    
    response = model.generate_content(prompt)
    raw_output = response.text.strip()

    print(raw_output)
    if raw_output.startswith("```json"):
        raw_output = raw_output.lstrip("```json").rstrip("```").strip()
    elif raw_output.startswith("```"):
        raw_output = raw_output.lstrip("```").rstrip("```").strip()

    try:
        output = json.loads(f"""{raw_output}""")
        if isinstance(output, dict) and "positive" in output and "negative" in output:
            return output
        else:
            raise ValueError("Invalid JSON format")
        
    except json.JSONDecodeError:
        raise ValueError("Failed to decode JSON from response")




