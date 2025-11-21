"""
Async Automated Skill Taxonomy Builder
--------------------------------------
Automatically groups skills into families, clusters, and domains using async AI.
"""

import json
import logging
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiofiles

from swx_api.app.services.llm_client import LLMClient, LLMConfig
from swx_api.app.services.ingestion_service import paths
from swx_api.core.middleware.logging_middleware import logger

logger = logging.getLogger("skill_taxonomy")


class SkillTaxonomyService:
    """Async service for building hierarchical skill taxonomy."""
    
    def __init__(self):
        self.llm_config = LLMConfig.from_env()
        self.data_dir = paths.data_dir
        self.processed_dir = paths.processed_dir
        self.processed_dir.mkdir(parents=True, exist_ok=True)
    
    def build_taxonomy(
        self,
        all_skills: List[str],
        employee_data: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Build hierarchical skill taxonomy (sync/async compatible).
        
        Can be called from sync or async contexts. In sync contexts, automatically
        runs the async implementation.
        """
        try:
            import asyncio
            loop = asyncio.get_running_loop()
            raise RuntimeError("Cannot call sync wrapper from async context - use await build_taxonomy_async()")
        except RuntimeError as e:
            if "Cannot call sync wrapper" in str(e):
                raise
            # No event loop running, run in sync mode
            import asyncio
            return asyncio.run(self._build_taxonomy_async(all_skills, employee_data))

    async def build_taxonomy_async(
        self,
        all_skills: List[str],
        employee_data: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Async version of build_taxonomy - use this in async contexts."""
        return await self._build_taxonomy_async(all_skills, employee_data)

    async def _build_taxonomy_async(
        self,
        all_skills: List[str],
        employee_data: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Build hierarchical skill taxonomy.
        
        Args:
            all_skills: List of unique skill names
            employee_data: Optional employee data for context
            
        Returns:
            Dictionary with:
            - taxonomy: Hierarchical taxonomy structure
            - skill_families: Grouped skill families
            - skill_clusters: Clustered skills
            - skill_domains: High-level domains
            - normalized_mapping: Skill name normalization map
        """
        try:
            # Get AI-powered classification (async)
            ai_taxonomy = await self._get_ai_taxonomy(all_skills, employee_data)
            
            # Build hierarchical structure
            taxonomy = self._build_hierarchy(ai_taxonomy, all_skills)
            
            # Generate normalized mapping
            normalized_mapping = self._generate_normalized_mapping(all_skills, taxonomy)
            
            result = {
                "taxonomy": taxonomy,
                "skill_families": ai_taxonomy.get("skill_families", []),
                "skill_clusters": ai_taxonomy.get("skill_clusters", []),
                "skill_domains": ai_taxonomy.get("skill_domains", []),
                "normalized_mapping": normalized_mapping,
                "total_skills": len(all_skills),
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }
            
            # Save taxonomy (async)
            await self._save_taxonomy(result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error building taxonomy: {e}", exc_info=True)
            return self._fallback_taxonomy(all_skills)
    
    async def _get_ai_taxonomy(
        self,
        all_skills: List[str],
        employee_data: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Get AI-powered taxonomy classification with async support."""
        prompt = self._build_taxonomy_prompt(all_skills, employee_data)
        
        schema = {
            "skill_domains": list,
            "skill_families": list,
            "skill_clusters": list
        }
        
        try:
            # Use async LLM client
            async with LLMClient(self.llm_config) as llm:
                result = await llm.call_llm(
                    prompt=prompt,
                    schema=schema,
                    system_message="You are an expert in skill classification and taxonomy.",
                    temperature=0.5,
                    max_tokens=4000
                )
            return self._validate_taxonomy_result(result)
            
        except Exception as e:
            logger.warning(f"AI taxonomy failed, using fallback: {e}")
            return self._fallback_taxonomy_logic(all_skills)
    
    def _build_taxonomy_prompt(
        self,
        all_skills: List[str],
        employee_data: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """Build prompt for taxonomy classification."""
        # Sample skills for prompt (limit to avoid token limits)
        sample_skills = all_skills[:100] if len(all_skills) > 100 else all_skills
        
        prompt = f"""Classify and organize the following skills into a hierarchical taxonomy.

Skills to classify ({len(all_skills)} total, showing first {len(sample_skills)}):
{', '.join(sample_skills)}

Organize skills into:
1. **Domains**: High-level categories (e.g., "Software Engineering", "Data Science", "Design")
2. **Families**: Related skill groups within domains (e.g., "Low-Level Programming", "Web Development")
3. **Clusters**: Specific skill clusters (e.g., "C++", "Rust", "Embedded Systems" → "Low-Level Programming")

Example structure:
- Domain: "Software Engineering"
  - Family: "Low-Level Programming"
    - Skills: ["C++", "Rust", "Embedded Systems"]
  - Family: "Web Development"
    - Skills: ["JavaScript", "React", "Node.js"]

Provide a JSON response with this structure:
{{
  "skill_domains": [
    {{
      "domain": "domain name",
      "description": "brief description",
      "families": [
        {{
          "family": "family name",
          "description": "brief description",
          "skills": ["skill1", "skill2", ...]
        }}
      ]
    }}
  ],
  "skill_families": [
    {{
      "family": "family name",
      "domain": "parent domain",
      "skills": ["skill1", "skill2", ...]
    }}
  ],
  "skill_clusters": [
    {{
      "cluster_name": "cluster name",
      "skills": ["skill1", "skill2", ...],
      "family": "parent family"
    }}
  ]
}}

Focus on:
- Logical grouping based on skill relationships
- Industry-standard classifications
- Clear hierarchical structure
- All skills must be classified

Response (JSON only):"""
        
        return prompt
    
    def _validate_taxonomy_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and normalize taxonomy result."""
        return {
            "skill_domains": result.get("skill_domains", []),
            "skill_families": result.get("skill_families", []),
            "skill_clusters": result.get("skill_clusters", []),
        }
    
    def _build_hierarchy(
        self,
        ai_taxonomy: Dict[str, Any],
        all_skills: List[str]
    ) -> Dict[str, Any]:
        """Build hierarchical taxonomy structure."""
        taxonomy = {
            "domains": []
        }
        
        # Build from domains
        domains = ai_taxonomy.get("skill_domains", [])
        for domain_data in domains:
            domain_name = domain_data.get("domain", "Unknown")
            families_data = domain_data.get("families", [])
            
            families = []
            for family_data in families_data:
                family_name = family_data.get("family", "Unknown")
                skills = family_data.get("skills", [])
                
                families.append({
                    "name": family_name,
                    "description": family_data.get("description", ""),
                    "skills": skills,
                    "skill_count": len(skills)
                })
            
            taxonomy["domains"].append({
                "name": domain_name,
                "description": domain_data.get("description", ""),
                "families": families,
                "family_count": len(families)
            })
        
        # Ensure all skills are included
        classified_skills = set()
        for domain in taxonomy["domains"]:
            for family in domain["families"]:
                classified_skills.update(family["skills"])
        
        # Add unclassified skills to "Other" domain
        unclassified = [s for s in all_skills if s not in classified_skills]
        if unclassified:
            taxonomy["domains"].append({
                "name": "Other",
                "description": "Unclassified skills",
                "families": [{
                    "name": "Unclassified",
                    "description": "Skills not yet classified",
                    "skills": unclassified,
                    "skill_count": len(unclassified)
                }],
                "family_count": 1
            })
        
        return taxonomy
    
    def _generate_normalized_mapping(
        self,
        all_skills: List[str],
        taxonomy: Dict[str, Any]
    ) -> Dict[str, str]:
        """Generate skill name normalization mapping."""
        mapping = {}
        
        # Extract canonical names from taxonomy
        for domain in taxonomy.get("domains", []):
            for family in domain.get("families", []):
                for skill in family.get("skills", []):
                    # Use first occurrence as canonical
                    if skill not in mapping:
                        mapping[skill] = skill
        
        # Add variations (case-insensitive, common variations)
        skill_lower_map = {s.lower(): s for s in all_skills}
        for skill in all_skills:
            skill_lower = skill.lower()
            if skill_lower in skill_lower_map and skill not in mapping:
                mapping[skill] = skill_lower_map[skill_lower]
            else:
                mapping[skill] = skill
        
        return mapping
    
    async def _save_taxonomy(self, taxonomy: Dict[str, Any]) -> Path:
        """Save taxonomy to file (async)."""
        taxonomy_path = self.processed_dir / "skill_taxonomy.json"
        
        async with aiofiles.open(taxonomy_path, "w", encoding="utf-8") as f:
            await f.write(json.dumps(taxonomy, ensure_ascii=False, indent=2))
        
        logger.info(f"Saved taxonomy to {taxonomy_path}")
        return taxonomy_path
    
    def _fallback_taxonomy(self, all_skills: List[str]) -> Dict[str, Any]:
        """Fallback taxonomy when AI classification fails."""
        return self._fallback_taxonomy_logic(all_skills)
    
    def _fallback_taxonomy_logic(self, all_skills: List[str]) -> Dict[str, Any]:
        """Rule-based taxonomy classification."""
        # Simple keyword-based classification
        domains = {
            "Software Engineering": {
                "families": {
                    "Programming Languages": [],
                    "Web Development": [],
                    "Mobile Development": [],
                    "DevOps": [],
                }
            },
            "Data & Analytics": {
                "families": {
                    "Data Science": [],
                    "Business Intelligence": [],
                    "Database": [],
                }
            },
            "Design & UX": {
                "families": {
                    "UI/UX Design": [],
                    "Graphic Design": [],
                }
            },
            "Other": {
                "families": {
                    "Unclassified": []
                }
            }
        }
        
        # Keywords for classification
        keywords = {
            "Programming Languages": ["python", "java", "javascript", "c++", "rust", "go", "ruby", "php"],
            "Web Development": ["react", "vue", "angular", "html", "css", "node", "express", "django", "flask"],
            "Mobile Development": ["ios", "android", "swift", "kotlin", "react native", "flutter"],
            "DevOps": ["docker", "kubernetes", "ci/cd", "jenkins", "terraform", "ansible"],
            "Data Science": ["python", "r", "pandas", "numpy", "machine learning", "ai", "tensorflow"],
            "Business Intelligence": ["tableau", "power bi", "qlik", "analytics"],
            "Database": ["sql", "postgresql", "mysql", "mongodb", "redis"],
            "UI/UX Design": ["figma", "sketch", "adobe xd", "ui", "ux", "design"],
            "Graphic Design": ["photoshop", "illustrator", "indesign"],
        }
        
        # Classify skills
        for skill in all_skills:
            skill_lower = skill.lower()
            classified = False
            
            for family_name, family_keywords in keywords.items():
                if any(kw in skill_lower for kw in family_keywords):
                    # Find domain
                    for domain_name, domain_data in domains.items():
                        if family_name in domain_data["families"]:
                            domains[domain_name]["families"][family_name].append(skill)
                            classified = True
                            break
                    if classified:
                        break
            
            if not classified:
                domains["Other"]["families"]["Unclassified"].append(skill)
        
        # Convert to taxonomy format
        taxonomy_domains = []
        for domain_name, domain_data in domains.items():
            families = []
            for family_name, skills in domain_data["families"].items():
                if skills:  # Only include families with skills
                    families.append({
                        "name": family_name,
                        "description": f"{family_name} skills",
                        "skills": skills,
                        "skill_count": len(skills)
                    })
            
            if families:
                taxonomy_domains.append({
                    "name": domain_name,
                    "description": f"{domain_name} domain",
                    "families": families,
                    "family_count": len(families)
                })
        
        return {
            "skill_domains": taxonomy_domains,
            "skill_families": [],
            "skill_clusters": [],
        }
