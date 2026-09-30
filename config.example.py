from pathlib import Path
import random

# Runtime configs
CURRENT_TZ = ""
LLM_MODEL= "" 
LLM_TEMPERATURE= 0
LLM_TIMEOUT = 0
LLM_MAX_RETRIES = 0
LLM_MAX_TOKENS = 0
SYSTEM_MESSAGE_YODA = ""
SYSTEM_MESSAGE_VADER = ""

RANDOM_NUMBER = random.random()


# File paths
PROJECT_ROOT_PATH = Path(__file__).resolve().parents[1]
LOGS_DIR = str(PROJECT_ROOT_PATH / "logs")

print(PROJECT_ROOT_PATH)

