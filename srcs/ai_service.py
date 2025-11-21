import os
from typing import Dict, Any, List, Tuple, Optional

import pandas as pd
from dotenv import load_dotenv
from openai import AzureOpenAI

load_dotenv()


class AIService:
    """
    Service wrapper around Azure OpenAI.
    
    Logic:
    1. Loads Degreed catalog (Title, URL, Summary, Thumbnail).
    2. Returns BOTH the AI text plan AND the structured list of recommended courses.
    """

    def __init__(self):
        # --- Azure config ---
        self.api_key = os.getenv("AZURE_OPENAI_API_KEY")
        self.endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
        self.api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")

        if self.api_key and self.endpoint and self.deployment:
            self.client = AzureOpenAI(
                api_key=self.api_key,
                azure_endpoint=self.endpoint,
                api_version=self.api_version,
            )
            self.is_active = True
        else:
            self.client = None
            self.is_active = False
            print("AI Service Warning: Azure credentials missing.")

        # --- Load Data ---
        self.courses: List[Dict[str, Any]] = self._load_degreed_catalog()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def generate_learning_plan(self, employee_profile: Dict, gaps: Dict) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Returns:
            Tuple[str, List]: (The markdown text plan, The list of course dictionaries used)
        """
        # 1. Find best matches
        selected_courses = self._suggest_courses(gaps, limit=3)
        
        # 2. Build prompt
        prompt = self._construct_prompt(employee_profile, gaps, selected_courses)

        # --- Mock Response Handler ---
        if not self.is_active or self.client is None:
            return self._mock_response(employee_profile, gaps, selected_courses), selected_courses

        try:
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an AI Skill Coach. "
                            "Create a plan using ONLY the provided resources. "
                            "Do not hallucinate links."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                # UPDATED: Higher temperature for more creative writing, 
                # but strictly constrained by context data.
                temperature=0.7,
                max_completion_tokens=800,
            )

            if not response or not getattr(response, "choices", None):
                return self._mock_response(employee_profile, gaps, selected_courses), selected_courses

            content = getattr(response.choices[0].message, "content", None)
            # Return BOTH text and the course objects
            return (content or self._mock_response(employee_profile, gaps, selected_courses)), selected_courses

        except Exception as e:
            print(f"AzureOpenAI ERROR: {e}")
            error_text = self._mock_response(employee_profile, gaps, selected_courses) + f"\n\nError: {e}"
            return error_text, selected_courses

    # ------------------------------------------------------------------
    # 1. LOAD CATALOG
    # ------------------------------------------------------------------
    def _load_degreed_catalog(self) -> List[Dict[str, Any]]:
        # Path handling
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_dir = os.path.join(base_dir, "data")
        filename = os.getenv("DEGREED_CATALOG_FILE", "Degreed_Content_Catalog.xlsx")
        path = os.path.join(data_dir, filename)

        if not os.path.exists(path):
            # Fallback check
            fallback = os.path.join(base_dir, "data", filename)
            if os.path.exists(fallback): path = fallback
            else:
                print(f"AIService ERROR: Catalog NOT found at: {path}")
                return []

        try:
            df = pd.read_excel(path)
        except Exception as e:
            print(f"AIService: Error reading Excel: {e}")
            return []

        # Map columns
        cols = {str(c).lower().strip(): c for c in df.columns}
        def get_col(candidates):
            for cand in candidates:
                if cand.lower() in cols: return cols[cand.lower()]
            return None

        title_col = get_col(["Title", "Content Title", "Titel"])
        url_col = get_col(["URL", "Content URL", "Link", "Web Link"])
        summary_col = get_col(["Summary", "Description"])
        thumb_col = get_col(["Thumbnail URL", "Thumbnail", "Image URL", "Image"])
        cat_cols = [c for c in df.columns if "category" in str(c).lower()]

        if not title_col:
            print("AIService: Title column missing.")
            return []
        
        # Fallback URL search
        if not url_col:
            for c in df.columns:
                if "url" in str(c).lower() and "thumbnail" not in str(c).lower():
                    url_col = c
                    break

        loaded_courses = []
        for _, row in df.iterrows():
            t = str(row.get(title_col, "")).strip()
            if not t or t.lower() == "nan": continue

            u = str(row.get(url_col, "")).strip()
            if u.lower() in ["nan", "none", "null", ""]: u = ""

            s = str(row.get(summary_col, "")).strip() if summary_col else ""
            if s.lower() == "nan": s = ""

            img = str(row.get(thumb_col, "")).strip() if thumb_col else ""
            if img.lower() in ["nan", "none", "null"]: img = ""

            cats = []
            for cc in cat_cols:
                val = str(row.get(cc, "")).strip()
                if val and val.lower() != "nan": cats.append(val)
            cats_text = " ".join(cats)

            search_blob = f"{t} {s} {cats_text}".lower()

            loaded_courses.append({
                "title": t,
                "url": u,
                "summary": s,
                "thumbnail": img,
                "search_text": search_blob
            })

        return loaded_courses

    # ------------------------------------------------------------------
    # 2. SELECTION
    # ------------------------------------------------------------------
    def _suggest_courses(self, gaps: Dict, limit: int = 3) -> List[Dict]:
        if not self.courses: return []

        gap_list = gaps.get("gaps", [])
        keywords = []
        for g in gap_list:
            name = str(g.get("name", ""))
            parts = [w.strip().lower() for w in name.replace("/", " ").split()]
            keywords.extend([w for w in parts if len(w) > 2])
        keywords = list(set(keywords))

        scored = []
        if keywords:
            for c in self.courses:
                score = 0
                txt = c["search_text"]
                for kw in keywords:
                    if kw in txt: score += 1
                
                # Bonus points
                if c['url'] and len(c['url']) > 4: score += 0.5
                if c['thumbnail'] and len(c['thumbnail']) > 4: score += 0.2

                if score > 0: scored.append((score, c))
            scored.sort(key=lambda x: x[0], reverse=True)

        if scored:
            return [item[1] for item in scored[:limit]]
        
        # Fallback: Courses with URL AND Thumbnail preferred
        fallback = sorted(
            self.courses,
            key=lambda x: (1 if x['url'] else 0) + (1 if x['thumbnail'] else 0),
            reverse=True
        )
        return fallback[:limit]

    # ------------------------------------------------------------------
    # 3. PROMPT
    # ------------------------------------------------------------------
    def _construct_prompt(self, profile: Dict, gaps: Dict, courses: List[Dict]) -> str:
        
        resources_block = ""
        if courses:
            for i, c in enumerate(courses, 1):
                resources_block += (
                    f"RESOURCE #{i}:\n"
                    f"  Title: {c['title']}\n"
                    f"  URL: {c['url']}\n"
                    f"  What it covers: {c['summary'][:300]}...\n\n"
                )
        else:
            resources_block = "No specific internal courses found. Suggest general learning activities."

        missing_skills = [g['name'] for g in gaps.get('gaps', [])]
        
        return f"""
You are an expert Talent Development Mentor at Skoda Auto. 
Your goal is to design a personalized, engaging, and motivating growth journey.

EMPLOYEE PROFILE:
- Role: {profile.get('position_name')}
- Department: {profile.get('department')}
- Key Skill Gaps: {', '.join(missing_skills)}

AVAILABLE LEARNING MATERIALS (These are selected specifically for this person):
{resources_block}

STRICT FORMATTING RULES:
1. **NO Main Title**: Do NOT start with a top-level header like "Your Personal Growth Strategy". Start directly with the first section header.
2. **NO Horizontal Lines**: Do NOT use markdown horizontal rules (---) anywhere in your response.
3. **Tone**: Be engaging, professional, and strategic. Speak directly to the employee ("You"). Avoid robotic phrasing.

STRUCTURE:
1. **Strategic Context** (Header: ### 🎯 Strategic Context): 
   Briefly explain why mastering these skills is crucial for their specific role and the department's success. Make it feel impactful.
   
2. **The Action Plan** (Header: ### 🚀 The Action Plan):
   - Break into 3 phases (Foundations, Application, Mastery).
   - Weave the recommendations into the text naturally: "**[Course Title]** (link: [URL])".
   - Explain *why* this specific course helps in this phase.

3. **Closing** (Header: ### ✨ Moving Forward): 
   Short, inspiring call to action.

Length limit: Keep it under 350 words.
"""

    def _mock_response(self, profile: Dict, gaps: Dict, courses: List[Dict]) -> str:
        course_list = ""
        if courses:
            for c in courses:
                u = c['url'] if c['url'] else "Check LMS"
                course_list += f"- **{c['title']}**\n  Link: {u}\n"
        else:
            course_list = "No specific courses found."

        return f"""### Mock Plan
**Gaps:** {', '.join([g['name'] for g in gaps.get('gaps', [])])}
#### Content
{course_list}
"""