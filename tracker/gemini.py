import os
import json
import requests
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables from .env
load_dotenv()

# Set up API keys
GEMINI_API_KEY = os.getenv("API_KEY")
AUTH_TOKEN = os.getenv("AUTH_TOKEN")
DASHBOARD_URL = "http://localhost:8000/api/api/dashboard/?child=1"  # Replace with actual child_id or remove query
REPORT_POST_URL = "http://localhost:8000/api/api/report/"


# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash-002")

def fetch_dashboard_data() -> dict:
    """
    Fetches dashboard log data from your Django API.
    """
    headers = {
        "Authorization": f"Token {AUTH_TOKEN}"
    }
    response = requests.get(DASHBOARD_URL, headers=headers)
    response.raise_for_status()
    return response.json()

def summarize_dashboard_data(data: dict) -> dict:
    """
    Sends dashboard JSON to Gemini and receives structured health summary.
    Cleans response from Markdown and parses JSON.
    """
    prompt = f"""
You are a health assistant for caregivers of autistic children. Based on the following JSON-formatted log data, generate a summary report in strict JSON format only.
for the week make it look like a weekly report
Return a JSON object in the following format:
{{
  "summary": "...",
  "suggestion": "...",
  "insight": {{
    "heartbeat": ["average bpm with short explanation", number of logs for heartbeat]
    "behavior": ["summary of behavior patterns", number of logs for behavior],
    "bloodpressure": ["average with comment and suggestion", number of logs for bloodpressure],
    "food": ["categorize food as good/bad or suggestions (be creative)", number of logs for food],
    "sleep": ["average sleep hours with quality insight", number of logs for sleep]
    "scratchnotes": [insights from scratch notes]
  }}
}}
make everything descriptive, also it is going to be displayed for the parent so make it for the parent, don't mention about child ID,
Here is the input data:
{data}
"""

    response = model.generate_content(prompt)
    raw_output = response.text.strip()

    # Strip code block markers if present
    if raw_output.startswith("```json"):
        raw_output = raw_output.lstrip("```json").rstrip("```").strip()
    elif raw_output.startswith("```"):
        raw_output = raw_output.lstrip("```").rstrip("```").strip()

    try:
        return json.loads(raw_output)
    except json.JSONDecodeError:
        print("⚠️ Gemini did not return valid JSON. Cleaned output:")
        print(raw_output)
        return {"error": "Invalid JSON returned by Gemini"}
    
# def save_report_to_django(report: dict, child_id: int, report_type="daily"):
#     headers = {
#         "Authorization": f"Token {AUTH_TOKEN}",
#         "Content-Type": "application/json"
#     }

#     payload = {
#         "child": child_id,
#         "report_type": report_type,
#         "summary": report["summary"],
#         "suggestion": report["suggestion"],
#         "insight": report["insight"]
#     }

#     response = requests.post(REPORT_POST_URL, headers=headers, data=json.dumps(payload))
#     response.raise_for_status()
#     print("✅ Report successfully saved.")


# try:
#     dashboard_data = fetch_dashboard_data()
#     report = summarize_dashboard_data(dashboard_data)
#     save_report_to_django(report, child_id=1, report_type="daily") 
#     print(json.dumps(report, indent=2))
# except Exception as e:
#     print(f"❌ Error: {e}")
