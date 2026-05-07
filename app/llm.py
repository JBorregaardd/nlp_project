import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

API_KEY = os.getenv("CAMPUSAI_API_KEY")
API_URL = os.getenv("CAMPUSAI_API_URL")
CHAT_MODEL = os.getenv("CAMPUSAI_MODEL")


if not API_KEY:
    raise ValueError("CAMPUSAI_API_KEY is not set")

if not API_URL:
    raise ValueError("CAMPUSAI_API_URL is not set")

if not CHAT_MODEL:
    raise ValueError("CAMPUSAI_MODEL is not set")

client = OpenAI(
    api_key=API_KEY,
    base_url=API_URL,
)

def generate_answer(query: str, context: str) -> str:
    system_prompt = (
        "Du er en medicinsk assistent. "
        "Svar kun ud fra den givne kontekst fra officielle danske sundhedskilder. "
        "Svar direkte på brugerens spørgsmål først. "
        "Medtag kun information, der er relevant for spørgsmålet. "
        "Undgå at opsummere hele kilden, hvis brugeren kun spørger om én ting. "
        "Hold svaret kort, typisk 3-4 sætninger. "
        "Omskriv gerne, men tilføj ikke ny information. "
        "Hvis symptomerne i spørgsmålet passer med information i konteksten, må du nævne mulige forklaringer, "
        "men du må ikke stille en sikker diagnose. "
        "Brug formuleringer som 'det kan være foreneligt med' eller 'det kan skyldes'. "
        "Hvis konteksten slet ikke indeholder relevant information, så sig: jeg ved det ikke. "
        "Hvis muligt, nævn kort hvilken kilde (titel) svaret kommer fra til sidst i svaret."
    )

    user_prompt = f"""Spørgsmål:
{query}

Kontekst:
{context}

Svar:"""

    response = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.0,
    )

    return response.choices[0].message.content.strip()

def rewrite_query(query: str) -> str:
    system_prompt = (
        "Du omskriver danske bruger-spørgsmål til korte søgeforespørgsler. "
        "Bevar kun vigtige symptomer, sygdomme og medicinske nøgleord. "
        "Tilføj gerne nært beslægtede synonymer. "
        "et eksempel kan være at omskrive kaste op til opkast. "
        "Svar kun med søgeforespørgslen, ingen forklaring. "
    )

    user_prompt = f"Spørgsmål: {query}\nSøgeforespørgsel:"

    response = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.0,
    )

    return response.choices[0].message.content.strip()