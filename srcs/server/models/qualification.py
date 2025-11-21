from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional, Dict, Any

CZECH_TO_EN_FIELD_MAP = {
    "ID Kurzu": "course_id",
    "Zkratka D": "course_code",
    "Název D": "course_name",
    "Téma": "topic",
    "Oddělení": "department",
    "Kontaktní osoba": "contact_person",
    "Počát.datum": "start_date",
    "Koncové datum": "end_date",
    "ID Skillu": "skill_id",
    "Skill v EN": "skill_name_en"
}

@dataclass
class Qualification:
    course_id: str = ""
    course_code: str = ""
    course_name: str = ""
    topic: str = ""
    department: str = ""
    contact_person: str = ""
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    skill_id: Optional[int] = None
    skill_name_en: str = ""

