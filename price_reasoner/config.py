import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    model: str = os.getenv("CLAUDE_MODEL", "claude-sonnet-4")
    output_dir: str = os.getenv("OUTPUT_DIR", "./outputs")
    data_dir: str = os.getenv("DATA_DIR", "./data")