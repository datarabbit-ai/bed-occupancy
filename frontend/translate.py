import json
import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


def get_openai_client():
    """Initialize and return OpenAI client."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise Exception(
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
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": f"""You are a professional translator, your role is to translate a given transcript of a voice call between AI agent and human to the language: {lang}. \n
                            Only return the translated transcript in the JSON format, nothing else. \n """
                + 'The JSON format should look like this: {"transcript":["role":"<role>", "message":"<translated_message>"]} \n'
                + """Roles should not be translated! Just copy them from the source.
                            Translate only the strings inside of the "message" attributes.
                            Do not translate neither proper nouns nor proper names""",
            },
            {"role": "user", "content": transcript},
        ],
        temperature=0.3,
    )
    res = response.choices[0].message.content.strip()
    return json.loads(res)
