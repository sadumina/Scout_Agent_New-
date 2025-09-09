import os
from openai import OpenAI
from dotenv import load_dotenv

# Load variables from .env
load_dotenv()

# Create client with API key
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("⚠️ OPENAI_API_KEY not found in environment! Using raw text instead of enrichment.")
    client = None
else:
    client = OpenAI(api_key=api_key)

def enrich_update(text: str) -> str:
    """
    Summarize the update text with OpenAI if key is available,
    otherwise just return the raw text.
    """
    if not client:
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
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # ✅ correct new API
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=150,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"❌ Enrichment failed: {e}")
        return text  # fallback
