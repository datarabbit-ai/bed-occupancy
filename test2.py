import os

from dotenv import load_dotenv
from elevenlabs import ElevenLabs

load_dotenv()

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
AGENT_ID = os.getenv("AGENT_ID")
PHONE_TO_CALL = os.getenv("PHONE_TO_CALL")
AGENT_PHONE_NUMBER_ID = os.getenv("AGENT_PHONE_NUMBER_ID")

client = ElevenLabs(api_key=ELEVENLABS_API_KEY)

conversation_initiation_client_data = {
    "conversation_initiation_client_data": {
        "dynamic_variables": {
            "patient_name": "Jan",
            "patient_surname": "Topolewski",
            "pesel": "234",
            "patient_sickness": "zapalenie kolana",
            "current_visit_day": 10,
            "suggested_appointment_day": 5,
        }
    }
}

client.conversational_ai.twilio_outbound_call(
    agent_id=AGENT_ID,
    agent_phone_number_id=AGENT_PHONE_NUMBER_ID,
    to_number=PHONE_TO_CALL,
    conversation_initiation_client_data=conversation_initiation_client_data,
)
