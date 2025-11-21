"""Utility script to turn raw Škoda hackathon exports into UI-friendly JSON."""

from __future__ import annotations

import json
import logging
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List

import pandas as pd

try:
    from transformers import MarianMTModel, MarianTokenizer
except ImportError:  # pragma: no cover
    MarianMTModel = None
    MarianTokenizer = None
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

BATCH_MODEL_NAME = "Helsinki-NLP/opus-mt-cs-en"

DATA_DIR = Path("data")
OUTPUT_USERS = Path("web/src/data/users.json")
OUTPUT_COURSES = Path("web/src/data/courses.json")
OUTPUT_JOB_DESCRIPTIONS = Path("web/src/data/job_descriptions.json")
OUTPUT_COURSE_CONTENT = Path("web/src/data/course_content.json")
TRANSLATION_CACHE_PATH = Path("artifacts/translation_cache.json")
TODAY = datetime(2025, 8, 28)

translator_tokenizer = None
translator_model = None
if MarianMTModel and MarianTokenizer:
    try:  # pragma: no cover - heavy init
        translator_tokenizer = MarianTokenizer.from_pretrained(BATCH_MODEL_NAME)
        translator_model = MarianMTModel.from_pretrained(BATCH_MODEL_NAME)
    except Exception as exc:
        logger.warning("Failed loading translation model: %s", exc)
        translator_tokenizer = None
        translator_model = None

translation_cache: Dict[str, str] = {}
if TRANSLATION_CACHE_PATH.exists():
    try:
        translation_cache = json.loads(TRANSLATION_CACHE_PATH.read_text(encoding="utf-8"))
        logger.info("Loaded %d cached translations", len(translation_cache))
    except Exception:  # pragma: no cover - corrupted cache
        translation_cache = {}

# Batch translation queue
_translation_queue: List[str] = []

CATEGORY_KEYWORDS = {
    "Leadership & Management": ["leadership", "management", "strategy", "board", "project"],
    "Compliance & Ethics": ["compliance", "etický", "ethics", "law", "legal", "safety", "protect", "kodex"],
    "Production & Quality": ["production", "quality", "manufacturing", "audits", "qms", "process"],
    "Digital & Data": ["sap", "python", "digital", "analytics", "data", "it", "cyber"],
    "Customer & Retail": ["sales", "retail", "marketing", "dealer", "b2b"],
    "HR & People": ["hr", "people", "talent", "recruitment", "education", "academy"],
    "Health & Safety": ["safety", "požární", "bozp", "first aid", "security"],
    "Languages & Communication": ["english", "german", "language", "communication"],
}

SKILL_KEYWORDS = {
    "excel": ("Excel Automation", "advanced"),
    "powerpoint": ("Storytelling with Slides", "intermediate"),
    "word": ("Word Templates", "intermediate"),
    "project": ("Project Delivery", "intermediate"),
    "compliance": ("Compliance Mindset", "advanced"),
    "quality": ("Quality Systems", "advanced"),
    "python": ("Python Foundations", "beginner"),
    "sap": ("SAP Operations", "intermediate"),
    "safety": ("Workplace Safety", "advanced"),
    "hr": ("People Operations", "advanced"),
}


def safe_text(value: Any, default: str = "") -> str:
    if isinstance(value, str):
        text = value.strip()
        return text or default
    if value is None:
        return default
    if isinstance(value, (float, int)) and pd.isna(value):
        return default
    text = str(value).strip()
    return text or default


# Common Czech-to-English translations (fast lookup)
COMMON_TRANSLATIONS = {
    "vysokoškolské bakalářské vzdělání": "Higher Bachelor's Education",
    "vysokoškolské vzdělání": "Higher Education",
    "specializace v pedagogice": "Specialization in Education",
    "učitel": "Teacher",
    "pracovník": "Worker/Employee",
    "vzdělání": "Education",
    "specializace": "Specialization",
    "pedagogika": "Education/Pedagogy",
    "učitelství": "Teaching",
    "praktického vyučování": "Practical Teaching",
    "odborného výcviku": "Vocational Training",
}

def looks_like_czech(text: str) -> bool:
    """Simple heuristic to check if text is likely Czech."""
    if not text:
        return False
    # Check for Czech-specific chars
    czech_chars = set("áčďéěíňóřšťúůýžÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ")
    return any(c in czech_chars for c in text)


def infer_department(role: str, position: str) -> str:
    """Infer department from role and position keywords."""
    text = (f"{role} {position}").lower()
    
    if any(w in text for w in ["logistics", "supply", "warehouse", "logistik"]):
        return "Logistics"
    if any(w in text for w in ["quality", "audit", "control", "kvalit"]):
        return "Quality Control"
    if any(w in text for w in ["it", "software", "developer", "data", "digital", "cyber", "system"]):
        return "IT & Digital"
    if any(w in text for w in ["hr", "human", "people", "recruitment", "talent", "education", "pedagog", "teacher", "učitel"]):
        return "HR & Academy"
    if any(w in text for w in ["production", "assembly", "montáž", "výrob", "operator"]):
        return "Production"
    if any(w in text for w in ["maintenance", "údržb", "service", "repair"]):
        return "Maintenance"
    if any(w in text for w in ["finance", "account", "cost", "ekonom"]):
        return "Finance"
    
    return "Operational Excellence"  # Default fallback


def translate_batch(texts: List[str]) -> List[str]:
    """Translate a batch of texts at once for efficiency."""
    if not texts or translator_model is None or translator_tokenizer is None:
        return texts
    try:
        inputs = translator_tokenizer(texts, return_tensors="pt", padding=True, truncation=True, max_length=256)
        outputs = translator_model.generate(**inputs, max_length=256)
        translated = translator_tokenizer.batch_decode(outputs, skip_special_tokens=True)
        return translated
    except Exception as exc:
        logger.warning("Batch translation failed: %s", exc)
        return texts


def translate_text(value: Any, force: bool = False) -> str:
    text = safe_text(value)
    if not text:
        return ""
    # Skip if already cached - this is the key speedup!
    cached = translation_cache.get(text)
    if cached:
        return cached
    # Check common translations first (fast!)
    text_lower = text.lower().strip()
    if text_lower in COMMON_TRANSLATIONS:
        translated = COMMON_TRANSLATIONS[text_lower]
        translation_cache[text] = translated
        return translated
    # Skip if doesn't look like Czech (unless forced) - this speeds things up massively
    if not force and not looks_like_czech(text):
        translation_cache[text] = text
        return text
    # If no translation model available, just return as-is
    if translator_model is None or translator_tokenizer is None:
        translation_cache[text] = text
        return text
    # Queue for batch translation (will be processed later)
    if text not in _translation_queue:
        _translation_queue.append(text)
    # Return original for now, will be replaced after batch processing
    return text


def flush_translation_queue() -> None:
    """Translate all queued texts in batches."""
    global _translation_queue
    if not _translation_queue or translator_model is None:
        _translation_queue = []
        return
    # Filter out already cached
    to_translate = [t for t in _translation_queue if t not in translation_cache]
    if not to_translate:
        _translation_queue = []
        return
    logger.info("Batch translating %d texts...", len(to_translate))
    batch_size = 32
    for i in range(0, len(to_translate), batch_size):
        batch = to_translate[i : i + batch_size]
        try:
            translated = translate_batch(batch)
            for orig, trans in zip(batch, translated):
                translation_cache[orig] = trans
            if (i // batch_size + 1) % 10 == 0:
                logger.info("  Translated %d/%d...", min(i + batch_size, len(to_translate)), len(to_translate))
        except Exception as exc:
            logger.warning("Batch translation failed: %s", exc)
            for text in batch:
                translation_cache[text] = text
    _translation_queue = []
    logger.info("Batch translation complete")


def infer_category(title: str) -> str:
    lower = title.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword in lower for keyword in keywords):
            return category
    return "Professional Skills"


def infer_skill_levels(course_titles: Iterable[str]) -> Dict[str, str]:
    skills: Dict[str, str] = {}
    for title in course_titles:
        lower = title.lower()
        for key, (skill_name, level) in SKILL_KEYWORDS.items():
            if key in lower:
                current_level = skills.get(skill_name)
                if current_level != "advanced":
                    skills[skill_name] = level
    return skills


def summarize_categories(course_titles: Iterable[str]) -> List[Dict[str, Any]]:
    counter = Counter(infer_category(title) for title in course_titles if isinstance(title, str))
    total = sum(counter.values()) or 1
    return [
        {"category": category, "count": count, "share": round(count / total * 100, 1)}
        for category, count in counter.most_common()
    ]


def load_org_hierarchy() -> Dict[str, str]:
    """Load organizational hierarchy to map user IDs to real departments."""
    hierarchy: Dict[str, str] = {}
    try:
        df = pd.read_excel(DATA_DIR / "RLS.sa_org_hierarchy - SE.xlsx")
        # Try to find columns that might contain user ID and department
        # Common column names might be: personal_number, user_id, department, org_unit, etc.
        id_col = None
        dept_col = None
        
        for col in df.columns:
            col_lower = str(col).lower()
            if any(x in col_lower for x in ["personal", "user", "id", "employee"]):
                id_col = col
            if any(x in col_lower for x in ["department", "org", "unit", "division", "oddělení"]):
                dept_col = col
        
        if id_col and dept_col:
            for row in df.to_dict("records"):
                user_id = str(row.get(id_col, "")).strip()
                dept = translate_text(row.get(dept_col, ""))
                if user_id and user_id != "nan" and dept:
                    hierarchy[user_id] = dept
        logger.info("Loaded %d organizational hierarchy entries", len(hierarchy))
    except Exception as exc:
        logger.warning("Failed to load org hierarchy: %s", exc)
    return hierarchy


def load_erp_profiles() -> Dict[str, Dict[str, Any]]:
    df = pd.read_excel(DATA_DIR / "ERP_SK1.Start_month - SE.xlsx")
    df = df.rename(
        columns={
            "persstat_start_month.personal_number": "personal_number",
            "persstat_start_month.profession": "profession",
            "persstat_start_month.planned_position": "planned_position",
            "persstat_start_month.basic_branch_of_education_name": "education_branch",
            "persstat_start_month.field_of_study_name": "field_of_study",
            "persstat_start_month.education_category_name": "education_category",
        }
    )
    profiles = {}
    for row in df.to_dict("records"):
        personal_number = str(row.get("personal_number")).strip()
        if not personal_number or personal_number == "nan":
            continue
        profiles[personal_number] = {
            "profession": translate_text(row.get("profession") or "Specialist"),
            "planned_position": translate_text(row.get("planned_position") or row.get("profession") or "Specialist"),
            "education_branch": translate_text(row.get("education_branch") or "Applied Sciences"),
            "field_of_study": translate_text(row.get("field_of_study") or "Industrial Engineering"),
            "education_category": translate_text(row.get("education_category") or "University"),
            "user_name": safe_text(row.get("user_name"), None),
        }
    return profiles


def load_training_history() -> Dict[str, List[Dict[str, Any]]]:
    df = pd.read_excel(DATA_DIR / "ZHRPD_VZD_STA_007.xlsx")
    df["Datum zahájení"] = pd.to_datetime(df["Datum zahájení"], errors="coerce")
    history: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for row in df.to_dict("records"):
        user_id = str(row.get("ID účastníka")).strip()
        if not user_id or user_id == "nan":
            continue
        history[user_id].append(
            {
                "title": translate_text(row.get("Označení typu akce")),
                "start": row.get("Datum zahájení"),
                "end": row.get("Datum ukončení"),
                "source": "Legacy LMS",
            }
        )
    for items in history.values():
        items.sort(key=lambda x: x["start"] or datetime(2000, 1, 1))
    return history
    
    
def load_extended_history() -> Dict[str, List[Dict[str, Any]]]:
    df = pd.read_excel(DATA_DIR / "ZHRPD_VZD_STA_016_RE_RHRHAZ00.xlsx")
    df["Počát.datum"] = pd.to_datetime(df["Počát.datum"], errors="coerce")
    extra: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for row in df.to_dict("records"):
        user_id = str(row.get("ID P")).strip()
        if not user_id or user_id == "nan":
            continue
        extra[user_id].append(
            {
                "title": translate_text(row.get("Název Q")),
                "start": row.get("Počát.datum"),
                "end": row.get("Koncové datum"),
                "source": "Qualification Archive",
            }
        )
    for items in extra.values():
        items.sort(key=lambda x: x["start"] or datetime(2000, 1, 1))
    return extra


def load_degreed_history() -> Dict[str, Dict[str, Any]]:
    df = pd.read_excel(DATA_DIR / "Degreed.xlsx")
    df["Completed Date"] = pd.to_datetime(df["Completed Date"], errors="coerce")
    latest: Dict[str, Dict[str, Any]] = {}
    for user_id, group in df.groupby("Employee ID"):
        group_sorted = group.sort_values("Completed Date", ascending=False).iloc[0]
        latest[str(user_id)] = {
            "title": group_sorted["Content Title"],
            "provider": group_sorted["Content Provider"],
            "date": group_sorted["Completed Date"],
            "minutes": group_sorted["Verified Learning Minutes"],
        }
    return latest


def load_course_descriptions() -> Dict[str, Dict[str, str]]:
    """Load course descriptions from text export files in multiple languages."""
    descriptions: Dict[str, Dict[str, str]] = {}  # {course_id: {lang: description}}
    try:
        # Load descriptions in all languages
        lang_files = {
            "en": "250828_Export_AI_Skill_Coatch_ZHRPD_DESCR_EXPORT_EN.txt",
            "cs": "250828_Export_AI_Skill_Coatch_ZHRPD_DESCR_EXPORT_CS.txt",
            "de": "250828_Export_AI_Skill_Coatch_ZHRPD_DESCR_EXPORT_DE.txt",
        }
        
        for lang, filename in lang_files.items():
            desc_file = DATA_DIR / filename
            if desc_file.exists():
                content = desc_file.read_text(encoding="utf-8", errors="ignore")
                for line in content.split("\n"):
                    if "\t" in line and not line.strip().startswith("Var.plánu"):
                        parts = line.split("\t")
                        if len(parts) >= 8:
                            course_id = parts[2].strip() if len(parts) > 2 else None
                            description = parts[-1].strip() if parts else None
                            if course_id and description and description != "nan" and course_id.isdigit():
                                if course_id not in descriptions:
                                    descriptions[course_id] = {}
                                descriptions[course_id][lang] = description if lang == "en" else translate_text(description)
        logger.info("Loaded %d course descriptions in multiple languages", len(descriptions))
    except Exception as exc:
        logger.warning("Failed to load course descriptions: %s", exc)
    return descriptions


def load_job_descriptions() -> Dict[str, Dict[str, str]]:
    """Load job descriptions from RE_RHRHAZ00 text files."""
    job_descriptions: Dict[str, Dict[str, str]] = {}  # {object_id: {lang: description}}
    try:
        # These files contain job descriptions/tasks in multiple languages
        job_files = [
            "250828_Export_AI_Skill_Coatch_RE_RHRHAZ00_ZP.txt",
            "250828_Export_AI_Skill_Coatch_RE_RHRHAZ00_ZS.txt",
            "250828_Export_AI_Skill_Coatch_RE_RHRHAZ00_ZX.txt",
            "250828_Export_AI_Skill_Coatch_RE_RHRHAZ00_P_S.txt",
            "250828_Export_AI_Skill_Coatch_RE_RHRHAZ00_S_T.txt",
            "250828_Export_AI_Skill_Coatch_RE_RHRHAZ00_T_ZP.txt",
            "250828_Export_AI_Skill_Coatch_RE_RHRHAZ00_T_ZS.txt",
            "250828_Export_AI_Skill_Coatch_RE_RHRHAZ00_T_ZX.txt",
        ]
        
        for filename in job_files:
            job_file = DATA_DIR / filename
            if job_file.exists():
                content = job_file.read_text(encoding="utf-8", errors="ignore")
                for line in content.split("\n"):
                    if "\t" in line and not any(line.strip().startswith(x) for x in ["VP", "Zobrazen", "28.08"]):
                        parts = line.split("\t")
                        if len(parts) >= 10:
                            object_id = parts[2].strip() if len(parts) > 2 else None
                            lang_code = parts[7].strip() if len(parts) > 7 else None
                            description = parts[-1].strip() if parts else None
                            
                            if object_id and description and description != "nan" and object_id.isdigit():
                                lang_map = {"C": "cs", "D": "de", "E": "en"}
                                lang = lang_map.get(lang_code, "en")
                                
                                if object_id not in job_descriptions:
                                    job_descriptions[object_id] = {}
                                # Translate if not English
                                job_descriptions[object_id][lang] = description if lang == "en" else translate_text(description)
        logger.info("Loaded %d job descriptions", len(job_descriptions))
    except Exception as exc:
        logger.warning("Failed to load job descriptions: %s", exc)
    return job_descriptions


def build_course_catalog() -> List[Dict[str, Any]]:
    seen = set()
    catalog: List[Dict[str, Any]] = []
    max_courses = 10000 # Increased limit for full dataset
    course_descriptions = load_course_descriptions()
    job_descriptions = load_job_descriptions()

    def add_entry(title: Any, source: str, metadata: Dict[str, Any] | None = None) -> None:
        clean_title = translate_text(title)
        if not clean_title or clean_title.lower() == "nan":
            return
        key = clean_title.lower()
        if key in seen:
            return
        seen.add(key)
        entry = {
            "title": clean_title,
            "category": infer_category(clean_title),
            "source": source,
        }
        if metadata:
            for key, value in metadata.items():
                if isinstance(value, str) or pd.isna(value):
                    entry[key] = translate_text(value)
                else:
                    entry[key] = value
        if not entry.get("category"):
            entry["category"] = infer_category(clean_title)
        
        # Try to find matching description by title or ID
        # Search for description that contains the course title
        for desc_id, desc_dict in course_descriptions.items():
            # Check if any description text matches
            for lang, desc_text in desc_dict.items():
                if clean_title.lower() in desc_text.lower() or desc_text.lower() in clean_title.lower():
                    entry["description"] = desc_dict.get("en", desc_text)
                    entry["descriptions"] = desc_dict  # Store all languages
                    break
            if "description" in entry:
                break
        
        # Also try to match with job descriptions
        for job_id, job_dict in job_descriptions.items():
            for lang, job_text in job_dict.items():
                if clean_title.lower() in job_text.lower() or job_text.lower() in clean_title.lower():
                    if "description" not in entry:
                        entry["description"] = job_dict.get("en", job_text)
                        entry["job_description"] = job_dict.get("en", job_text)
                    break
        
        catalog.append(entry)

    skill_df = pd.read_excel(DATA_DIR / "Skill_mapping.xlsx")
    for row in skill_df.to_dict("records"):
        title = row.get("Název D")
        topic = row.get("Téma")
        category = row.get("Kategorie")
        add_entry(
            title,
            "Skill Mapping",
            {
                "topic": topic,
                "category": category or infer_category(str(title)),
                "audience": row.get("Oddělení") or "Škoda Academy",
            },
        )

    training_titles = pd.read_excel(DATA_DIR / "ZHRPD_VZD_STA_007.xlsx")["Označení typu akce"].dropna().unique()
    # Use ALL training titles from Legacy LMS
    for title in training_titles:
        add_entry(title, "Legacy LMS")

    degreed_df = pd.read_excel(DATA_DIR / "Degreed.xlsx")
    # Use ALL Degreed courses
    for _, row in degreed_df.iterrows():
        title = row.get("Content Title")
        if pd.isna(title) or not title:
            continue
        add_entry(
            title,
            "Degreed",
            {"provider": row.get("Content Provider"), "content_type": row.get("Content Type")},
        )

    if len(catalog) > max_courses:
        catalog = catalog[:max_courses]
    # Flush translations and update catalog entries
    flush_translation_queue()
    for entry in catalog:
        if "title" in entry:
            entry["title"] = translation_cache.get(entry["title"], entry["title"])
        for key in ["topic", "category", "audience", "provider"]:
            if key in entry and isinstance(entry[key], str):
                entry[key] = translation_cache.get(entry[key], entry[key])
    return catalog


def merge_histories(*histories: Dict[str, List[Dict[str, Any]]]) -> Dict[str, List[Dict[str, Any]]]:
    merged: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for history in histories:
        for user_id, records in history.items():
            merged[user_id].extend(records)
    for items in merged.values():
        items.sort(key=lambda x: x["start"] or datetime(2000, 1, 1))
    return merged


def build_user_profiles() -> List[Dict[str, Any]]:
    erp = load_erp_profiles()
    org_hierarchy = load_org_hierarchy()
    job_descriptions = load_job_descriptions()
    history007 = load_training_history()
    history016 = load_extended_history()
    degreed = load_degreed_history()
    # Flush translations and update profiles with translated text
    flush_translation_queue()
    for profile in erp.values():
        for key in ["profession", "planned_position", "education_branch", "field_of_study", "education_category"]:
            if key in profile:
                profile[key] = translation_cache.get(profile[key], profile[key])
    # Update history entries with translated titles
    for user_id, entries in list(history007.items()) + list(history016.items()):
        for entry in entries:
            if "title" in entry:
                entry["title"] = translation_cache.get(entry["title"], entry["title"])
    merged_history = merge_histories(history007, history016)

    users = []
    # Process all users
    erp_items = list(erp.items())
    for user_id, profile in erp_items:
        courses = merged_history.get(user_id, [])
        course_titles = [c["title"] for c in courses if c.get("title")]
        recent_entries = courses[-5:]
        earliest_date = None
        for entry in courses:
            if entry.get("start") and (earliest_date is None or entry["start"] < earliest_date):
                earliest_date = entry["start"]
        experience_years = round(((TODAY - earliest_date).days / 365), 1) if earliest_date else 5.0
        skills = infer_skill_levels(course_titles)
        course_mix = summarize_categories(course_titles)

        degreed_focus = degreed.get(user_id)
        if degreed_focus:
            title = translation_cache.get(degreed_focus['title'], degreed_focus['title'])
            provider = translation_cache.get(degreed_focus.get('provider', 'Degreed'), degreed_focus.get('provider', 'Degreed'))
            current_focus = f"{title} ({provider})"
        elif courses:
            title = translation_cache.get(courses[-1]['title'], courses[-1]['title'])
            current_focus = f"{title} ({courses[-1].get('source', 'Internal')})"
        else:
            current_focus = "Awaiting next assignment"

        # Use real department from org hierarchy if available, otherwise infer
        real_department = org_hierarchy.get(user_id)
        department = real_department if real_department else infer_department(profile["profession"], profile["planned_position"])

        # Use Employee ID format
        display_name = f"Employee {user_id}"

        users.append(
            {
                "id": user_id,
                "name": display_name,
                "department": department,
                "role": profile["profession"],
                "position": profile["planned_position"],
                "experience_years": experience_years,
                "education": {
                    "category": profile["education_category"],
                    "branch": profile["education_branch"],
                    "field": profile["field_of_study"],
                },
                "background": f"{profile['education_branch']} • {profile['field_of_study']}",
                "current_assignment": profile["planned_position"],
                "current_focus": current_focus,
                "skills": skills,
                "completed_courses": course_titles,
                "recent_courses": [
                    {
                        "title": entry["title"],
                        "date": entry["start"].strftime("%Y-%m-%d") if isinstance(entry["start"], datetime) else None,
                        "source": entry.get("source"),
                    }
                    for entry in recent_entries
                ],
                "course_mix": course_mix,
                "job_descriptions": [],  # Will be populated below
            }
        )
        
        # Try to find job descriptions related to this user's position/role
        user_job_descs = []
        position_lower = (profile.get("planned_position", "") + " " + profile.get("profession", "")).lower()
        for job_id, job_dict in job_descriptions.items():
            job_text = job_dict.get("en", "")
            if job_text and any(word in job_text.lower() for word in position_lower.split() if len(word) > 3):
                user_job_descs.append(job_dict.get("en", ""))
        if user_job_descs:
            users[-1]["job_descriptions"] = user_job_descs[:5]  # Limit to 5 most relevant
    return users


def _replace_translated_in_data(data: Any) -> Any:
    """Recursively replace original Czech text with translations in data structures."""
    if isinstance(data, dict):
        return {k: _replace_translated_in_data(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [_replace_translated_in_data(item) for item in data]
    elif isinstance(data, str):
        # If this string is in the queue and now has a translation, use it
        return translation_cache.get(data, data)
    return data


def main() -> None:
    logger.info("Rebuilding course catalog...")
    courses = build_course_catalog()
    # Process queued translations
    flush_translation_queue()
    # Replace original Czech text with translations
    courses = _replace_translated_in_data(courses)
    OUTPUT_COURSES.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_COURSES, "w", encoding="utf-8") as fp:
        json.dump(courses, fp, indent=2, ensure_ascii=False)
    logger.info("Saved %d courses to %s", len(courses), OUTPUT_COURSES)

    logger.info("Rebuilding user profiles...")
    users = build_user_profiles()
    # Process any remaining queued translations
    flush_translation_queue()
    # Replace original Czech text with translations
    users = _replace_translated_in_data(users)
    with open(OUTPUT_USERS, "w", encoding="utf-8") as fp:
        json.dump(users, fp, indent=2, ensure_ascii=False)
    logger.info("Saved %d users to %s", len(users), OUTPUT_USERS)

    # Export job descriptions
    logger.info("Exporting job descriptions...")
    job_descriptions = load_job_descriptions()
    OUTPUT_JOB_DESCRIPTIONS.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_JOB_DESCRIPTIONS, "w", encoding="utf-8") as fp:
        json.dump(job_descriptions, fp, indent=2, ensure_ascii=False)
    logger.info("Saved %d job descriptions to %s", len(job_descriptions), OUTPUT_JOB_DESCRIPTIONS)

    # Export course content from vector store if available
    logger.info("Exporting course content...")
    try:
        from .vector_store import VectorStore
        from .config import settings
        store = VectorStore()
        store.load()
        course_content = [
            {
                "id": chunk.id,
                "source_path": chunk.source_path,
                "text": chunk.text,
                "tags": chunk.tags,
            }
            for chunk in store.chunks[:1000]  # Limit to first 1000 chunks for web
        ]
        OUTPUT_COURSE_CONTENT.parent.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_COURSE_CONTENT, "w", encoding="utf-8") as fp:
            json.dump(course_content, fp, indent=2, ensure_ascii=False)
        logger.info("Saved %d course content chunks to %s", len(course_content), OUTPUT_COURSE_CONTENT)
    except Exception as exc:
        logger.warning("Could not load vector store for course content: %s", exc)
        # Create empty file
        OUTPUT_COURSE_CONTENT.parent.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_COURSE_CONTENT, "w", encoding="utf-8") as fp:
            json.dump([], fp, indent=2, ensure_ascii=False)

    if translation_cache:
        TRANSLATION_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(TRANSLATION_CACHE_PATH, "w", encoding="utf-8") as fp:
            json.dump(translation_cache, fp, indent=2, ensure_ascii=False)
        logger.info("Persisted %d translated terms", len(translation_cache))


if __name__ == "__main__":
    main()
