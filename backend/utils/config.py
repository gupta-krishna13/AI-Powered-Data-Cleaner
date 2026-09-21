import os

from dotenv import load_dotenv


load_dotenv()


APP_ENV = os.getenv(
    "APP_ENV",
    "development",
)

AI_MODE = os.getenv(
    "AI_MODE",
    "gemini",
)

GEMINI_API_KEY = os.getenv(
    "GEMINI_API_KEY",
)

GEMINI_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-3.7-flash",
)

GEMINI_FALLBACK_MODEL = os.getenv(
    "GEMINI_FALLBACK_MODEL",
    "gemini-3.6-flash",
)