import os
import openai
from dotenv import load_dotenv

# Load variables from .env in the project root
load_dotenv()

# Read API key from environment
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    print("⚠️ OPENAI_API_KEY not found in environment! Using raw text instead of enrichment.")
else:
    openai.api_key = api_key

def enrich_update(text):
    """
    Summarize the update text with OpenAI if key is available,
    otherwise just return the raw text.
    """
    if not api_key:
        return text  # fallback: no enrichment

    prompt = f"""
    Summarize the following EPA update and extract:
    - Type of opportunity (funding, regulation, etc.)
    - Affected region or sector
    - Deadline or key dates
    - Recommended action

    Text: {text}
    """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
        return response.choices[0].message["content"]
    except Exception as e:
        print(f"❌ Enrichment failed: {e}")
        return text  # fallback to raw description
