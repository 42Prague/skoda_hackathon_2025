from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional, Dict, Any

# Czech -> English field mapping for reference
CZECH_TO_EN_FIELD_MAP_QUAL_REC = {
    "personal_number": "personal_number",      # already English-ish
    "Počát.datum": "start_date",
    "Koncové datum": "end_date",
    "ID Q": "qualification_id",
    "Název Q": "qualification_name"
}

@dataclass
class QualificationRecord:
    """Represents a time-bounded qualification assignment / status.

    Fields (translated):
      personal_number    -> internal employee identifier
      start_date         -> qualification start date (Počát.datum)
      end_date           -> qualification end date (Koncové datum)
      qualification_id   -> numeric qualification identifier (ID Q)
      qualification_name -> human readable qualification name (Název Q)
    """
    personal_number: str = ""
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    qualification_id: Optional[str] = None
    qualification_name: str = ""
    
    