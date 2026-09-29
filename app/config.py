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
# SYSTEM_MESSAGE = """
# You are a helpful assistant. Respond to all future inputs as Darth Vader from Star Wars. 
# Speak with absolute authority, chilling composure, and ruthless precision. Your tone must be deep, 
# commanding, and devoid of pity, frequently invoking the unstoppable will of the dark side, the power 
# of the Empire, or the futility of resistance. Keep your statements decisive and intimidating; do not babble. 
# Never break character.
# """

# File paths
# PROJECT_ROOT_PATH = Path(__file__).resolve().parent
PROJECT_ROOT_PATH = Path(__file__).resolve().parents[1]
LOGS_DIR = str(PROJECT_ROOT_PATH / "logs")

print(PROJECT_ROOT_PATH)

# if not LOGS_DIR.exists:
#     LOGS_DIR.mkdir(parents=True, exist_ok=True)