import httpx
import os
from typing import Dict, List, Any
import json

class LLMService:
    """Service for interacting with Azure GPT-4.1 compatible LLM"""
    
    def __init__(self):
        pass
        
    async def generate_learning_plan(
        self, 
        employee_profile: Dict[str, Any], 
        gaps: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate personalized learning plan using LLM"""
        
        # Load environment variables lazily (after .env has been loaded)
        api_base_url = os.getenv("LLM_API_BASE_URL")
        api_key = os.getenv("LLM_API_KEY")
        deployment_name = os.getenv("LLM_DEPLOYMENT_NAME", "hackathon-gpt-4.1")
        api_version = os.getenv("LLM_API_VERSION", "2025-01-01-preview")
        
        # If LLM not configured, return mock data
        if not api_base_url or not api_key:
            print("⚠️  LLM not configured, using mock data")
            print(f"   API Base URL: {api_base_url}")
            print(f"   API Key: {'***' if api_key else 'None'}")
            return self._generate_mock_plan(employee_profile, gaps)
        
        print(f"🤖 Calling real LLM API: {api_base_url}")
        print(f"   Deployment: {deployment_name}")
        
        try:
            prompt = self._build_prompt(employee_profile, gaps)
            print(f"   Prompt length: {len(prompt)} characters")
            response = await self._call_llm(prompt, api_base_url, api_key, deployment_name, api_version)
            print(f"✅ LLM response received: {len(response)} characters")
            return self._parse_response(response)
        except Exception as e:
            print(f"❌ Error calling LLM: {type(e).__name__}: {e}")
            print(f"   Falling back to mock data")
            return self._generate_mock_plan(employee_profile, gaps)
    
    def _build_prompt(self, employee_profile: Dict[str, Any], gaps: Dict[str, Any]) -> str:
        """Build prompt for LLM"""
        employee = employee_profile.get("employee", {})
        role = gaps.get("role", {})
        
        prompt = f"""You are an AI Career Coach for Škoda Auto. 

Employee Profile:
- Name: {employee.get('user_name')}
- Current Position: {employee.get('profession')}
- Target Position: {role.get('name')}

Current Skills:
{self._format_skills(employee_profile.get('skills', []))}

Current Qualifications:
{self._format_qualifications(employee_profile.get('qualifications', []))}

Target Role Requirements:
Required Skills: {', '.join(gaps.get('required_skills', []))}
Required Qualifications:
{self._format_qualifications(gaps.get('required_qualifications', []))}

Key Activities in Target Role:
{self._format_activities(gaps.get('activities', []))}

Skill Gaps:
{', '.join(gaps.get('missing_skills', [])) or 'None identified'}

Qualification Gaps:
{self._format_qualifications(gaps.get('missing_qualifications', [])) or 'None identified'}

Please generate a personalized learning plan to help this employee transition to their target role. 

Your response must be valid JSON with this exact structure:
{{
  "explanation": "A 2-3 paragraph explanation of the learning journey, including current strengths, key gaps, and strategic approach",
  "learning_path": [
    {{
      "step": 1,
      "title": "Phase title (e.g., 'Build Fundamentals')",
      "courses": [
        {{
          "name": "Course name",
          "provider": "Internal/Degreed/External",
          "minutes": 180
        }}
      ]
    }}
  ],
  "estimated_time_to_readiness": "e.g., '3-4 months' or '8-12 weeks'"
}}

Generate 3-5 learning path steps, each with 1-3 relevant courses. Be specific and practical."""
        
        return prompt
    
    def _format_skills(self, skills: List[Dict[str, Any]]) -> str:
        """Format skills for prompt"""
        if not skills:
            return "No skills recorded"
        return "\n".join([
            f"- {skill['name']} ({skill.get('level', 'unknown')} - {skill.get('source', 'unknown')} source)"
            for skill in skills
        ])
    
    def _format_qualifications(self, qualifications: List[Dict[str, Any]]) -> str:
        """Format qualifications for prompt"""
        if not qualifications:
            return "No qualifications recorded"
        return "\n".join([
            f"- {qual.get('name', qual.get('id'))} ({qual.get('active', 'unknown')})"
            for qual in qualifications
        ])
    
    def _format_activities(self, activities: List[str]) -> str:
        """Format activities for prompt"""
        if not activities:
            return "No activities specified"
        return "\n".join([f"- {activity}" for activity in activities])
    
    async def _call_llm(self, prompt: str, api_base_url: str, api_key: str, deployment_name: str, api_version: str) -> str:
        """Call Azure OpenAI compatible endpoint"""
        url = f"{api_base_url}/openai/deployments/{deployment_name}/chat/completions?api-version={api_version}"
        
        headers = {
            "Content-Type": "application/json",
            "api-key": api_key
        }
        
        payload = {
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert AI Career Coach for Škoda Auto. Provide practical, actionable learning plans."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.7,
            "max_tokens": 2000,
            "response_format": {"type": "json_object"}
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"]
    
    def _parse_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response"""
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # Fallback if response is not valid JSON
            return {
                "explanation": response,
                "learning_path": [],
                "estimated_time_to_readiness": "To be determined"
            }
    
    def _generate_mock_plan(self, employee_profile: Dict[str, Any], gaps: Dict[str, Any]) -> Dict[str, Any]:
        """Generate mock learning plan for development"""
        employee = employee_profile.get("employee", {})
        role = gaps.get("role", {})
        missing_skills = gaps.get("missing_skills", [])
        missing_quals = gaps.get("missing_qualifications", [])
        
        explanation = f"""Based on your profile, transitioning from {employee.get('profession')} to {role.get('name')} is achievable with focused learning.

Your current strengths include {len(employee_profile.get('skills', []))} documented skills. However, to succeed in the target role, you'll need to develop {len(missing_skills)} additional technical skills: {', '.join(missing_skills[:3])}{'...' if len(missing_skills) > 3 else ''}.

We recommend a phased approach starting with foundational skills, then advancing to specialized knowledge, and finally gaining practical experience through projects. This structured path will ensure you're well-prepared for the responsibilities of {role.get('name')}."""
        
        learning_path = []
        
        # Phase 1: Fundamentals
        if missing_skills:
            learning_path.append({
                "step": 1,
                "title": "Build Foundational Skills",
                "courses": [
                    {
                        "name": f"{missing_skills[0]} Fundamentals",
                        "provider": "Internal Training",
                        "minutes": 240
                    },
                    {
                        "name": f"Introduction to {missing_skills[1] if len(missing_skills) > 1 else missing_skills[0]}",
                        "provider": "Degreed",
                        "minutes": 180
                    }
                ]
            })
        
        # Phase 2: Required Qualifications
        if missing_quals:
            learning_path.append({
                "step": 2,
                "title": "Complete Required Certifications",
                "courses": [
                    {
                        "name": qual.get("name", ""),
                        "provider": "Internal/External",
                        "minutes": 480
                    }
                    for qual in missing_quals[:2]
                ]
            })
        
        # Phase 3: Advanced Skills
        if len(missing_skills) > 2:
            learning_path.append({
                "step": 3,
                "title": "Develop Advanced Capabilities",
                "courses": [
                    {
                        "name": f"Advanced {missing_skills[2] if len(missing_skills) > 2 else missing_skills[0]}",
                        "provider": "Degreed",
                        "minutes": 300
                    },
                    {
                        "name": "Best Practices and Patterns",
                        "provider": "Internal Training",
                        "minutes": 180
                    }
                ]
            })
        
        # Phase 4: Practical Application
        learning_path.append({
            "step": len(learning_path) + 1,
            "title": "Practical Application & Projects",
            "courses": [
                {
                    "name": f"{role.get('name')} - Hands-on Workshop",
                    "provider": "Internal Training",
                    "minutes": 480
                },
                {
                    "name": "Mentorship Program",
                    "provider": "Internal",
                    "minutes": 960
                }
            ]
        })
        
        # Calculate total time
        total_minutes = sum(
            course["minutes"] 
            for step in learning_path 
            for course in step.get("courses", [])
        )
        
        weeks = total_minutes // (60 * 10)  # Assuming 10 hours per week
        months = weeks // 4
        
        time_estimate = f"{months}-{months + 2} months" if months > 0 else f"{weeks}-{weeks + 2} weeks"
        
        return {
            "explanation": explanation,
            "learning_path": learning_path,
            "estimated_time_to_readiness": time_estimate
        }

# Global instance
llm_service = LLMService()
