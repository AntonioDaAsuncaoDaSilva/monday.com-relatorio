import os
from dotenv import load_dotenv

load_dotenv()

MONDAY_API_TOKEN = os.getenv("MONDAY_API_TOKEN", "")

if not MONDAY_API_TOKEN:
    raise ValueError("MONDAY_API_TOKEN não definido. Copia .env.example para .env e preenche o token.")
