"""
Internationalization (i18n) Support for Skill DNA
Supports English and Czech languages
Handles field names, skill translations, and UI labels
"""
from typing import Dict


class TranslationManager:
    """
    Manages translations between English and Czech
    """

    # Field name translations (Czech → English)
    FIELD_TRANSLATIONS = {
        # Employee fields
        "ID zaměstnance": "employee_id",
        "Jméno": "name",
        "Příjmení": "surname",
        "Oddělení": "department",
        "Pozice": "position",
        "Datum nástupu": "hire_date",

        # Skill fields
        "Dovednost": "skill",
        "Kvalifikace": "qualification",
        "Kompetence": "competence",
        "Certifikát": "certificate",

        # Date fields
        "Datum": "date",
        "Začátek": "start_date",
        "Konec": "end_date",
        "Platí od": "valid_from",
        "Platí do": "valid_to",
        "Dokončeno": "completed_date",

        # Status fields
        "Stav": "status",
        "Aktivní": "active",
        "Neaktivní": "inactive",
        "Dokončeno": "completed",

        # Categories
        "Kategorie": "category",
        "Typ": "type",
        "Úroveň": "level"
    }

    # Reverse mapping (English → Czech)
    FIELD_TRANSLATIONS_REVERSE = {v: k for k, v in FIELD_TRANSLATIONS.items()}

    # UI Labels (for frontend)
    UI_LABELS = {
        "en": {
            # Upload component
            "upload_title": "Upload Employee Data",
            "upload_description": "Drag and drop CSV, Excel, or PDF files here",
            "upload_button": "Select File",
            "upload_processing": "Processing file...",
            "upload_success": "Data uploaded successfully!",
            "upload_error": "Upload failed. Please check the file format.",

            # Format detection
            "format_detected": "Format detected",
            "format_hr_system": "HR System (Czech)",
            "format_planning": "Planning System (Czech)",
            "format_lms": "Learning Management System",
            "format_projects": "Project/Task Data",
            "format_qualifications": "Qualifications",

            # Results
            "employees_processed": "Employees processed",
            "skills_extracted": "Skills extracted",
            "time_range": "Time range",
            "validation_errors": "Validation errors",

            # Genome visualization
            "genome_title": "Organizational Skill Genome",
            "genome_subtitle": "Interactive skill cluster visualization",
            "cluster": "Cluster",
            "skill": "Skill",
            "employees": "employees",

            # Evolution
            "evolution_title": "Skill Evolution Timeline",
            "evolution_subtitle": "Historical trends 2013-2025",
            "emerging_skills": "Emerging Skills",
            "declining_skills": "Declining Skills",
            "stable_skills": "Stable Skills",

            # Categories
            "legacy_engineering": "Legacy Engineering",
            "software_cloud": "Software & Cloud",
            "e_mobility": "E-Mobility",
            "ai_emerging": "AI & Emerging Tech",

            # Actions
            "switch_language": "Switch to Czech",
            "download_report": "Download Report",
            "refresh_data": "Refresh Data",
            "export_csv": "Export CSV"
        },

        "cz": {
            # Upload component
            "upload_title": "Nahrát Data Zaměstnanců",
            "upload_description": "Přetáhněte CSV, Excel nebo PDF soubory sem",
            "upload_button": "Vybrat Soubor",
            "upload_processing": "Zpracování souboru...",
            "upload_success": "Data úspěšně nahrána!",
            "upload_error": "Nahrání selhalo. Zkontrolujte formát souboru.",

            # Format detection
            "format_detected": "Zjištěn formát",
            "format_hr_system": "HR Systém (Český)",
            "format_planning": "Plánovací Systém (Český)",
            "format_lms": "Systém Řízení Učení",
            "format_projects": "Data Projektů/Úkolů",
            "format_qualifications": "Kvalifikace",

            # Results
            "employees_processed": "Zpracováno zaměstnanců",
            "skills_extracted": "Extrahováno dovedností",
            "time_range": "Časové období",
            "validation_errors": "Chyby validace",

            # Genome visualization
            "genome_title": "Organizační Genom Dovedností",
            "genome_subtitle": "Interaktivní vizualizace klastrů dovedností",
            "cluster": "Klastr",
            "skill": "Dovednost",
            "employees": "zaměstnanci",

            # Evolution
            "evolution_title": "Časová Osa Vývoje Dovedností",
            "evolution_subtitle": "Historické trendy 2013-2025",
            "emerging_skills": "Vznikající Dovednosti",
            "declining_skills": "Klesající Dovednosti",
            "stable_skills": "Stabilní Dovednosti",

            # Categories
            "legacy_engineering": "Tradiční Inženýrství",
            "software_cloud": "Software a Cloud",
            "e_mobility": "Elektromobilita",
            "ai_emerging": "AI a Nové Technologie",

            # Actions
            "switch_language": "Přepnout na Angličtinu",
            "download_report": "Stáhnout Zprávu",
            "refresh_data": "Obnovit Data",
            "export_csv": "Exportovat CSV"
        }
    }

    # Skill category translations
    CATEGORY_TRANSLATIONS = {
        "en": {
            "Legacy Engineering": "Legacy Engineering",
            "Software/Cloud": "Software & Cloud",
            "E-Mobility": "E-Mobility",
            "AI/Emerging": "AI & Emerging Tech"
        },
        "cz": {
            "Legacy Engineering": "Tradiční Inženýrství",
            "Software/Cloud": "Software a Cloud",
            "E-Mobility": "Elektromobilita",
            "AI/Emerging": "AI a Nové Technologie"
        }
    }

    # Common skill name translations
    SKILL_TRANSLATIONS = {
        # Programming
        "Python": "Python",
        "JavaScript": "JavaScript",
        "Java": "Java",
        "C++": "C++",

        # Engineering
        "CAD": "CAD",
        "Mechanical Design": "Mechanický Design",
        "CNC Programming": "CNC Programování",
        "CATIA": "CATIA",
        "AutoCAD": "AutoCAD",

        # Cloud
        "AWS": "AWS",
        "Azure": "Azure",
        "Docker": "Docker",
        "Kubernetes": "Kubernetes",

        # E-Mobility
        "Battery Systems": "Bateriové Systémy",
        "Electric Powertrain": "Elektrický Pohon",
        "Charging Infrastructure": "Nabíjecí Infrastruktura",

        # AI
        "Machine Learning": "Strojové Učení",
        "TensorFlow": "TensorFlow",
        "PyTorch": "PyTorch",
        "LLM Integration": "Integrace LLM"
    }

    def __init__(self, default_language: str = "en"):
        """
        Initialize translation manager
        Args:
            default_language: "en" or "cz"
        """
        self.current_language = default_language

    def translate_field(self, field_name: str, to_english: bool = True) -> str:
        """
        Translate field name between Czech and English
        """
        if to_english:
            return self.FIELD_TRANSLATIONS.get(field_name, field_name)
        else:
            return self.FIELD_TRANSLATIONS_REVERSE.get(field_name, field_name)

    def translate_skill(self, skill_name: str, target_language: str = "en") -> str:
        """
        Translate skill name to target language
        """
        if target_language == "en":
            # Find Czech key that matches and return English value
            for eng, cz in self.SKILL_TRANSLATIONS.items():
                if cz == skill_name:
                    return eng
            return skill_name
        else:
            return self.SKILL_TRANSLATIONS.get(skill_name, skill_name)

    def get_ui_label(self, key: str, language: str = None) -> str:
        """
        Get UI label in specified language
        """
        lang = language or self.current_language
        return self.UI_LABELS.get(lang, {}).get(key, key)

    def translate_category(self, category: str, target_language: str = "en") -> str:
        """
        Translate skill category
        """
        return self.CATEGORY_TRANSLATIONS.get(target_language, {}).get(category, category)

    def set_language(self, language: str):
        """
        Change current language
        """
        if language in ["en", "cz"]:
            self.current_language = language

    def get_all_labels(self, language: str = None) -> Dict:
        """
        Get all UI labels for specified language
        Useful for frontend to load all translations at once
        """
        lang = language or self.current_language
        return self.UI_LABELS.get(lang, {})

    def normalize_text(self, text: str) -> str:
        """
        Normalize Czech text for comparison (remove diacritics for search)
        č→c, š→s, ř→r, ž→z, ě→e, á→a, í→i, ý→y, ú→u, ů→u
        """
        replacements = {
            'á': 'a', 'č': 'c', 'ď': 'd', 'é': 'e', 'ě': 'e',
            'í': 'i', 'ň': 'n', 'ó': 'o', 'ř': 'r', 'š': 's',
            'ť': 't', 'ú': 'u', 'ů': 'u', 'ý': 'y', 'ž': 'z',
            'Á': 'A', 'Č': 'C', 'Ď': 'D', 'É': 'E', 'Ě': 'E',
            'Í': 'I', 'Ň': 'N', 'Ó': 'O', 'Ř': 'R', 'Š': 'S',
            'Ť': 'T', 'Ú': 'U', 'Ů': 'U', 'Ý': 'Y', 'Ž': 'Z'
        }

        for cz_char, ascii_char in replacements.items():
            text = text.replace(cz_char, ascii_char)

        return text


# Global translation manager instance
translator = TranslationManager(default_language="en")


if __name__ == "__main__":
    # Test translations
    tm = TranslationManager()

    print("[TEST] Translation Manager initialized")
    print(f"[INFO] Default language: {tm.current_language}")

    # Test field translation
    print(f"[TEST] 'ID zaměstnance' → '{tm.translate_field('ID zaměstnance')}'")

    # Test UI labels
    print(f"[TEST] EN upload_title: {tm.get_ui_label('upload_title', 'en')}")
    print(f"[TEST] CZ upload_title: {tm.get_ui_label('upload_title', 'cz')}")

    # Test normalization
    test_text = "Kvalifikace Řízení"
    print(f"[TEST] Normalize '{test_text}' → '{tm.normalize_text(test_text)}'")
