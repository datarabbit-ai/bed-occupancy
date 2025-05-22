import os

import requests
from dotenv import load_dotenv

load_dotenv()

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
AGENT_ID = os.getenv("AGENT_ID")
TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
PHONE_TO_CALL = os.getenv("PHONE_TO_CALL")
AGENT_PHONE_NUMBER_ID = os.getenv("AGENT_PHONE_NUMBER_ID")

headers = {"xi-api-key": ELEVENLABS_API_KEY, "Content-Type": "application/json"}

payload = {
    "agent_id": AGENT_ID,
    "conversation_initiation_client_data": {
        "dynamic_variables": {
            "patient_name": "Jan",
            "patient_surname": "Topolewski",
            "personal_number": "234",
            "patient_sickness": "zapalenie kolana",
            "current_visit_day": 10,
            "suggested_appointment_day": 5,
        }
    },
    "to_number": PHONE_TO_CALL,
    "agent_phone_number_id": AGENT_PHONE_NUMBER_ID,
    "twilio_account_sid": TWILIO_SID,
    "twilio_auth_token": TWILIO_TOKEN,
}

response = requests.post("https://api.elevenlabs.io/v1/convai/twilio/outbound_call", headers=headers, json=payload)

if response.status_code == 200:
    call_data = response.json()
    print(f"Call ID: {call_data}")
else:
    print(f"Błąd: {response.text}")
