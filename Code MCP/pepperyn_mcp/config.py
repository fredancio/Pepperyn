from dataclasses import dataclass
import os
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class Settings:
    excel_path: str = os.getenv("PEPPERYN_EXCEL_PATH", "./data/pepperyn_finance_template.xlsx")
    currency: str = os.getenv("PEPPERYN_CURRENCY", "EUR")

settings = Settings()
