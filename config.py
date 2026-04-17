import os
import yaml
from dotenv import load_dotenv

load_dotenv()

GENAI_API_KEY = os.getenv("GENAI_API_KEY")
GENAI_BASE_URL = os.getenv("GENAI_BASE_URL")
LLM_MODEL = os.getenv("LLM_MODEL")
EMBED_MODEL = os.getenv("EMBED_MODEL")

# Fix: Force UTF-8 encoding to prevent emoji corruption
with open("config.yaml", "r", encoding="utf-8") as file:
    app_config = yaml.safe_load(file)

WELCOME_MSG = app_config["ui"]["welcome_message"]
THEME = app_config["ui"]["theme"]
TOP_K = app_config["rag"]["top_k"]
COLLECTION_NAME = app_config["rag"]["collection_name"]
PERSIST_DIR = app_config["rag"]["persist_dir"]
GUARDRAIL_PROMPT = app_config["system"]["guardrail_prompt"]