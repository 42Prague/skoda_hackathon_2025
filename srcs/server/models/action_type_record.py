from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional, Dict, Any

CZECH_TO_EN_ACTION_MAP = {
    "Typ akce": "action_type",              # Type of action
    "Označení typu akce": "action_type_code", # Action type code / label
    "IDOBJ": "object_id",                   # Object identifier
    "Datum zahájení": "start_date",          # Start date
    "Datum ukončení": "end_date",            # End date
    "ID účastníka": "participant_id"         # Participant ID
}

@dataclass
class ActionTypeRecord:
    action_type: str = ""
    action_type_code: str = ""
    object_id: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    participant_id: Optional[str] = None
