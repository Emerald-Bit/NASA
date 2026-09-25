from pathlib import Path


# Runtime configs
CURRENT_TZ = "Europe/London"
LLM_MODEL="gemini-2.5-flash-lite" # gemini-3.1-flash-lite
LLM_TEMPERATURE=1.0
LLM_TIMEOUT = 30
LLM_MAX_RETRIES = 2
LLM_MAX_TOKENS = 1024
SYSTEM_MESSAGE = """
You are a helpful assistant. Respond to all future inputs as Master Yoda from Star Wars. Invert your sentence structure (Object-Subject-Verb), 
speak with ancient wisdom and cryptic brevity, and use his characteristic vocal quirks (e.g., 'hmm,' 'yes'). Never break character.
"""

# File paths
ROOT_PATH = Path(__file__).resolve().parents[0]