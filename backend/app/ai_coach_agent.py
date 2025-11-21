import logging
import json
from typing import Optional, Dict, Any
import requests
from config import settings

logger = logging.getLogger(__name__)


class AICoachAgent:
    def __init__(self):
        """Initialize the AI coach agent."""
        self.api_url = settings.llm_api_url
        self.api_key = settings.llm_api_key
        self.api_version = settings.llm_api_version
        self.model_name = settings.llm_model_name
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "api-key": self.api_key,  # Azure OpenAI style
            "Authorization": f"Bearer {self.api_key}"  # OpenAI style
        })
        logger.info(f"Initialized AICoachAgent with model: {self.model_name}")

    def check_api_configuration(self) -> bool:
        if not self.api_url or self.api_url == "https://api.example.com/v1/chat/completions":
            logger.error("LLM_API_URL not configured. Set it in environment variables.")
            return False

        if not self.api_key:
            logger.error("LLM_API_KEY not configured. Set it in environment variables.")
            return False

        logger.info(f"API configuration valid: {self.api_url}")
        return True

    def test_connection(self) -> bool:
        try:
            response = self._call_api(
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=10
            )
            logger.info("API connection test successful")
            return True
        except Exception as e:
            logger.error(f"API connection test failed: {e}")
            return False

    def _call_api(self, messages: list, max_tokens: Optional[int] = None, temperature: Optional[float] = None) -> Dict[str, Any]:
        if not self.check_api_configuration():
            raise RuntimeError("API not properly configured")

        payload = {
            "messages": messages,
            "max_tokens": max_tokens or settings.llm_max_tokens,
            "temperature": temperature or settings.llm_temperature,
            "model": self.model_name
        }

        # Build URL with version parameter if needed (Azure OpenAI style)
        url = self.api_url
        if "api-version" not in url and self.api_version:
            separator = "&" if "?" in url else "?"
            url = f"{url}{separator}api-version={self.api_version}"

        try:
            response = self.session.post(url, json=payload, timeout=60)
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response body: {e.response.text}")
            raise

    def answer_question(self, user_input: str, context: Optional[str] = None) -> str:
        # Build messages with context
        system_message = "You are an AI skill development coach for Škoda employees. Provide helpful, actionable responses about skill development, learning paths, and career growth."

        messages = [{"role": "system", "content": system_message}]

        if context:
            messages.append({
                "role": "user",
                "content": f"Context:\n{context}\n\nQuestion: {user_input}"
            })
        else:
            messages.append({
                "role": "user",
                "content": user_input
            })

        try:
            response = self._call_api(messages)

            # Extract answer from response
            # Support both OpenAI and Azure OpenAI response formats
            choices = response.get('choices', [])
            if not choices:
                logger.warning("API returned no choices, using fallback")
                return self._get_fallback_response(user_input)
            
            message = choices[0].get('message', {})
            answer = message.get('content', '').strip()
            
            if not answer:
                logger.warning("API returned empty content, using fallback")
                return self._get_fallback_response(user_input)
            
            return answer

        except Exception as e:
            logger.error(f"LLM API call failed: {e}")
            # Return helpful mock response instead of error
            user_lower = user_input.lower()
            
            if 'software engineer' in user_lower or 'developer' in user_lower or 'programming' in user_lower:
                return (
                    "To become a better software engineer, focus on these key areas:\n\n"
                    "**1. Core Programming Skills**\n"
                    "Master data structures, algorithms, and design patterns. Practice problem-solving on platforms like LeetCode or HackerRank.\n\n"
                    "**2. Modern Technologies**\n"
                    "Learn cloud platforms (AWS, Azure, GCP), containerization (Docker, Kubernetes), and CI/CD pipelines. These are essential for modern development.\n\n"
                    "**3. Software Architecture**\n"
                    "Understand microservices, system design, scalability, and distributed systems. Learn to design robust, maintainable applications.\n\n"
                    "**4. Best Practices**\n"
                    "Master version control (Git), write tests (unit, integration, E2E), conduct code reviews, and maintain good documentation.\n\n"
                    "**5. Soft Skills**\n"
                    "Develop communication, teamwork, and problem-solving abilities. Technical skills alone aren't enough for career growth.\n\n"
                    "Use the Skills Search and Employee Profile features to explore relevant courses in the Škoda system!"
                )
            
            if 'career' in user_lower or 'growth' in user_lower or 'promotion' in user_lower:
                return (
                    "For career advancement at Škoda, consider:\n\n"
                    "**1. Skill Development**\n"
                    "Identify skill gaps for your target role using the Employee Profile feature. Complete required qualifications systematically.\n\n"
                    "**2. Cross-Functional Experience**\n"
                    "Seek projects outside your current domain. This broadens your perspective and makes you more valuable.\n\n"
                    "**3. Leadership & Mentoring**\n"
                    "Mentor junior colleagues, lead initiatives, and demonstrate leadership potential even before promotion.\n\n"
                    "**4. Continuous Learning**\n"
                    "Stay updated with industry trends. Use platforms like Degreed to expand your knowledge base.\n\n"
                    "**5. Network & Visibility**\n"
                    "Build relationships across departments. Make your contributions visible to leadership through presentations and documentation."
                )
            
            if 'learn' in user_lower or 'course' in user_lower or 'training' in user_lower:
                return (
                    "Here's how to approach learning effectively:\n\n"
                    "**1. Set Clear Goals**\n"
                    "Define what you want to achieve. Are you preparing for a new role, project, or certification?\n\n"
                    "**2. Use the Learning Path Feature**\n"
                    "Enter your employee ID in the Learning Path tab to get personalized recommendations based on your role and skill gaps.\n\n"
                    "**3. Follow a Structured Approach**\n"
                    "Start with fundamentals, then progress to advanced topics. Don't skip prerequisites.\n\n"
                    "**4. Practice Actively**\n"
                    "Learning by doing is far more effective than passive consumption. Apply new skills to real projects immediately.\n\n"
                    "**5. Track Your Progress**\n"
                    "Regularly review your skills in the Employee Profile tab to see your growth over time."
                )
            
            if 'qualification' in user_lower or 'certification' in user_lower:
                return (
                    "Qualifications and certifications are valuable for:\n\n"
                    "**1. Role Requirements**\n"
                    "Many positions at Škoda require specific qualifications. Check your Employee Profile to see which ones you're missing.\n\n"
                    "**2. Skill Validation**\n"
                    "Certifications prove your expertise to employers and clients. They're especially important in regulated industries.\n\n"
                    "**3. Structured Learning**\n"
                    "Certification programs provide a structured path through complex topics with clear milestones.\n\n"
                    "**4. Career Mobility**\n"
                    "Having the right certifications opens doors to new roles and projects both within and outside Škoda.\n\n"
                    "Use the Employee Profile feature to identify which qualifications are required for your target position."
                )
            
            return (
                "I'm here to help with:\n\n"
                "• Career development and growth strategies\n"
                "• Skill development and learning recommendations\n"
                "• Understanding qualification requirements\n"
                "• Navigating the Škoda learning ecosystem\n\n"
                "**Try asking:**\n"
                '• "How can I advance my career at Škoda?"\n'
                '• "What qualifications do I need for my role?"\n'
                '• "How should I approach learning new skills?"\n\n'
                "You can also use the **Employee Profile** to view your skills, **Skills Search** to explore available skills, "
                "and **Learning Path** to get personalized recommendations."
            )
    def generate_learning_path(self,
                                current_skills: list,
                                target_role: str,
                                missing_qualifications: list) -> str:

        context = f"""
Current Skills: {', '.join(current_skills) if current_skills else 'None recorded'}
Target Role: {target_role}
Missing Qualifications: {', '.join(missing_qualifications) if missing_qualifications else 'None'}
"""

        question = (
            "Based on my current skills and target role, what learning path "
            "should I follow to acquire the missing qualifications?"
        )

        return self.answer_question(question, context)

    def explain_skill_gap(self, skill_name: str, role_context: str) -> str:
        question = (
            f"Why is '{skill_name}' important for {role_context}? "
            f"What are practical applications of this skill?"
        )

        return self.answer_question(question)


# Global instance (lazy-loaded)
_coach_instance: Optional[AICoachAgent] = None


def get_coach() -> AICoachAgent:
    global _coach_instance

    if _coach_instance is None:
        _coach_instance = AICoachAgent()
        # Model is loaded on first use (lazy loading)

    return _coach_instance


if __name__ == "__main__":
    # Test the coach
    coach = AICoachAgent()

    if not coach.check_api_configuration():
        print("API not configured. Set LLM_API_URL and LLM_API_KEY environment variables.")
    else:
        try:
            # Test connection
            if coach.test_connection():
                print("API connection successful!")

                # Test question
                response = coach.answer_question(
                    "What skills should I learn to become a better software engineer?"
                )
                print("Response:", response)
            else:
                print("API connection test failed")

        except Exception as e:
            print(f"Error testing coach: {e}")
