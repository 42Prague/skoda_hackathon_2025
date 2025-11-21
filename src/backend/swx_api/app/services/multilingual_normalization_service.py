"""
Multilingual Normalization Service
-----------------------------------
Handles Czech/English detection, normalization, and canonicalization.
"""

import re
from typing import Any, Dict, List, Optional, Tuple

from swx_api.core.middleware.logging_middleware import logger


CZECH_CHARS = "áčďéěíňóřšťúůýžÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ"
CZECH_DIACRITICS = set(CZECH_CHARS)


def detect_czech(text: str) -> bool:
    """Detect if text contains Czech characters."""
    if not text:
        return False
    return any(char in CZECH_DIACRITICS for char in text)


def detect_english(text: str) -> bool:
    """Detect if text is primarily English."""
    if not text:
        return False
    text_clean = re.sub(r'[^a-zA-Z\s]', '', text)
    if not text_clean.strip():
        return False
    czech_char_count = sum(1 for char in text if char in CZECH_DIACRITICS)
    total_alpha = sum(1 for char in text if char.isalpha())
    if total_alpha == 0:
        return False
    czech_ratio = czech_char_count / total_alpha
    return czech_ratio < 0.1


def detect_language(text: str) -> str:
    """Detect language: 'cz', 'en', or 'mixed'."""
    if not text:
        return "en"
    
    has_czech = detect_czech(text)
    has_english = detect_english(text)
    
    if has_czech and has_english:
        return "mixed"
    elif has_czech:
        return "cz"
    elif has_english:
        return "en"
    else:
        return "en"


def resolve_mixed_field(text: str) -> Dict[str, str]:
    """Extract Czech and English parts from mixed field."""
    separators = ["/", "|", ";", " - ", " – "]
    
    parts = [text]
    for sep in separators:
        if sep in text:
            parts = text.split(sep)
            break
    
    cz_parts = []
    en_parts = []
    
    for part in parts:
        part = part.strip()
        if not part:
            continue
        lang = detect_language(part)
        if lang == "cz":
            cz_parts.append(part)
        elif lang == "en":
            en_parts.append(part)
        else:
            en_parts.append(part)
    
    return {
        "cz": " / ".join(cz_parts) if cz_parts else "",
        "en": " / ".join(en_parts) if en_parts else text,
        "detected_language": "mixed" if cz_parts and en_parts else (detect_language(text) if not cz_parts and not en_parts else ("cz" if cz_parts else "en"))
    }


def remove_diacritics(text: str) -> str:
    """Remove Czech diacritics for matching."""
    replacements = {
        "á": "a", "č": "c", "ď": "d", "é": "e", "ě": "e",
        "í": "i", "ň": "n", "ó": "o", "ř": "r", "š": "s",
        "ť": "t", "ú": "u", "ů": "u", "ý": "y", "ž": "z",
        "Á": "A", "Č": "C", "Ď": "D", "É": "E", "Ě": "E",
        "Í": "I", "Ň": "N", "Ó": "O", "Ř": "R", "Š": "S",
        "Ť": "T", "Ú": "U", "Ů": "U", "Ý": "Y", "Ž": "Z"
    }
    result = text
    for cz_char, en_char in replacements.items():
        result = result.replace(cz_char, en_char)
    return result


class MultilingualNormalizationService:
    """Service for multilingual normalization."""
    
    def __init__(self):
        self.skill_synonyms_cz = {
            "python": ["python", "py"],
            "javascript": ["javascript", "js"],
            "java": ["java"],
            "c++": ["c++", "cpp", "c plus plus"],
            "sql": ["sql", "databáze"],
            "docker": ["docker"],
            "kubernetes": ["kubernetes", "k8s"],
            "git": ["git"],
            "linux": ["linux", "unix"],
            "agile": ["agile", "scrum", "agilní"],
        }
        
        self.job_title_mapping = {
            "Software Engineer": {
                "cz": "Softwarový inženýr",
                "en": "Software Engineer",
                "synonyms_cz": ["Programátor", "Vývojář", "Vývojář softwaru"],
                "synonyms_en": ["Developer", "Programmer", "Software Developer"]
            },
            "Data Engineer": {
                "cz": "Datový inženýr",
                "en": "Data Engineer",
                "synonyms_cz": ["Datový specialista"],
                "synonyms_en": ["Data Specialist"]
            },
            "Project Manager": {
                "cz": "Projektový manažer",
                "en": "Project Manager",
                "synonyms_cz": ["PM", "Manažer projektu"],
                "synonyms_en": ["PM", "Project Lead"]
            }
        }
    
    def normalize_skill_name(self, skill: str) -> str:
        """Canonicalize skill name (handle Czech/English)."""
        if not skill:
            return ""
        
        skill_lower = skill.lower().strip()
        skill_no_diacritics = remove_diacritics(skill_lower)
        
        for canonical, variants in self.skill_synonyms_cz.items():
            variants_no_diacritics = [remove_diacritics(v) for v in variants]
            if skill_lower in variants or skill_no_diacritics in variants_no_diacritics or skill_lower == canonical:
                return canonical.title()
        
        skill_clean = re.sub(r'\s+', ' ', skill.strip())
        
        if ' ' in skill_clean or '-' in skill_clean:
            words = re.split(r'[\s\-]+', skill_clean)
            normalized = ' '.join(word.capitalize() for word in words if word)
        else:
            normalized = skill_clean.capitalize()
        
        return normalized
    
    def merge_job_titles(self, title_cz: str, title_en: str) -> str:
        """Merge Czech and English job titles."""
        if not title_en and title_cz:
            for job_title, mapping in self.job_title_mapping.items():
                if title_cz in mapping.get("synonyms_cz", []) or title_cz == mapping["cz"]:
                    return job_title
            return title_cz
        
        if not title_cz and title_en:
            return title_en
        
        if title_cz and title_en:
            for job_title, mapping in self.job_title_mapping.items():
                if (title_cz in mapping.get("synonyms_cz", []) or title_cz == mapping["cz"]) and \
                   (title_en in mapping.get("synonyms_en", []) or title_en == mapping["en"]):
                    return job_title
            return title_en
        
        return title_en or title_cz or ""
    
    def normalize_qualification_name(self, qual_name: str, language: Optional[str] = None) -> Dict[str, str]:
        """Normalize qualification name."""
        if not qual_name:
            return {"cz": "", "en": ""}
        
        detected_lang = language or detect_language(qual_name)
        
        if detected_lang == "mixed":
            resolved = resolve_mixed_field(qual_name)
            return {"cz": resolved["cz"], "en": resolved["en"]}
        elif detected_lang == "cz":
            return {"cz": qual_name, "en": remove_diacritics(qual_name)}
        else:
            return {"cz": "", "en": qual_name}
    
    def map_free_text_to_skills(self, description: str, skill_ontology: List[str]) -> List[str]:
        """Map free text competency description to skill ontology."""
        if not description:
            return []
        
        description_lower = description.lower()
        description_no_diacritics = remove_diacritics(description_lower)
        
        matched_skills = []
        
        for skill in skill_ontology:
            skill_lower = skill.lower()
            skill_no_diacritics = remove_diacritics(skill_lower)
            
            if skill_lower in description_lower or skill_no_diacritics in description_no_diacritics:
                matched_skills.append(skill)
        
        return matched_skills
    
    def canonicalize_field(self, field_value: str, field_type: str = "skill") -> Dict[str, Any]:
        """Canonicalize a field value."""
        if not field_value:
            return {"normalized": "", "language": "en", "cz": "", "en": ""}
        
        language = detect_language(field_value)
        
        if field_type == "skill":
            normalized = self.normalize_skill_name(field_value)
            return {
                "normalized": normalized,
                "language": language,
                "cz": field_value if language == "cz" else "",
                "en": field_value if language == "en" else normalized
            }
        elif field_type == "job_title":
            if language == "mixed":
                resolved = resolve_mixed_field(field_value)
                merged = self.merge_job_titles(resolved["cz"], resolved["en"])
                return {
                    "normalized": merged,
                    "language": "mixed",
                    "cz": resolved["cz"],
                    "en": resolved["en"]
                }
            elif language == "cz":
                merged = self.merge_job_titles(field_value, "")
                return {
                    "normalized": merged,
                    "language": "cz",
                    "cz": field_value,
                    "en": merged
                }
            else:
                return {
                    "normalized": field_value,
                    "language": "en",
                    "cz": "",
                    "en": field_value
                }
        else:
            normalized = field_value.strip()
            return {
                "normalized": normalized,
                "language": language,
                "cz": field_value if language == "cz" else "",
                "en": field_value if language == "en" else normalized
            }

    def normalize_course_name(self, title: str) -> str:
        """Normalize Czech/English course titles with diacritic removal."""
        if not title:
            return ""
        stripped = re.sub(r"\s+", " ", title).strip()
        if not stripped:
            return ""
        no_diacritics = remove_diacritics(stripped)
        return " ".join(word.capitalize() for word in no_diacritics.split(" "))

