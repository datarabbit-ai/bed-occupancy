import json
import os
from typing import Any

from dotenv import load_dotenv
from models import Transcript
from openai import OpenAI
from openai.types.responses.easy_input_message_param import EasyInputMessageParam
from openai.types.responses.response_format_text_json_schema_config_param import ResponseFormatTextJSONSchemaConfigParam
from openai.types.responses.response_text_config_param import ResponseTextConfigParam

load_dotenv()


def get_openai_client():
    """Initialize and return OpenAI client."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "OpenAI API key not found. Please set OPENAI_API_KEY environment variable "
            "or create a .env file with OPENAI_API_KEY=your_api_key"
        )
    return OpenAI(api_key=api_key)


def translate(client: OpenAI, transcript: dict, lang: str) -> dict:
    """
    Translates the messages to a language passed as the lang parameter using provided openai client.

    :param client: openai client to use
    :param transcript: messages to translate
    :param lang: language to translate to
    :return: translated messages
    """
    model_schema: dict[str, Any] = Transcript.model_json_schema()
    input_messages = [
        EasyInputMessageParam(
            role="system",
            content=f"""You are a professional translator, your role is to translate a given transcript of a voice call between AI agent and human to the language: {lang}. \n
                        Only return the translated transcript in the JSON format, nothing else. \n
                        Roles should not be translated! Just copy them from the source. \n
                        Translate only the strings inside of the "message" attributes. \n
                        Do not translate neither proper nouns nor proper names""",
        ),
        EasyInputMessageParam(role="user", content=json.dumps(transcript)),
    ]

    response = client.responses.create(
        model="gpt-4o-mini",
        input=input_messages,
        temperature=0.3,
        text=ResponseTextConfigParam(
            format=ResponseFormatTextJSONSchemaConfigParam(
                name="translated_messages", type="json_schema", schema=model_schema, strict=True
            )
        ),
    )
    res = response.output_text
    try:
        return json.loads(res)
    except json.JSONDecodeError as e:
        raise Exception(f"Failed to decode JSON from OpenAI response: {res}") from e


# client = get_openai_client()
# mock_transcript = {
#     "transcript": [
#         {
#             "role": "agent",
#             "message": "Dzień dobry! Z tej strony asystent pacjenta ze Szpitala przy ulicy Szpitalnej w Poznaniu. Chciałbym zaproponować przełożenie wizyty na wcześniejszy termin. Czy mogę prosić o podanie imienia i nazwiska w celu weryfikacji?"
#         },
#         {
#             "role": "user",
#             "message": "Natan Dynia"
#         },
#         {
#             "role": "agent",
#             "message": "Dziękuję, panie Natanie. Aby potwierdzić tożsamość, proszę o podanie trzech ostatnich cyfr numeru PESEL."
#         },
#         {
#             "role": "user",
#             "message": "953" # jak tu będzie int, to nie przetłumaczy
#         }
#     ]
# }
# response = translate(client, mock_transcript, "en")
# print(type(response))
# print(response)
