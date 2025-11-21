
from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional, Dict, Any

CZECH_TO_EN_FIELD_MAP = {
    "ID objektu (FM)": "object_id",
    "Počát.datum": "start_date",
    "Koncové datum": "end_date",
    "Variabilní pole (os. číslo)": "personal_number",
}

@dataclass
class Position:
    object_id: str = ""
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    personal_number: str = ""
    
