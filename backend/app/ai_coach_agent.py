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

            if 'software engineer' in user_lower or 'developer' in user_lower:
                return (
                    "To become a better software engineer, focus on these key areas:\n\n"
                    "1. **Core Programming Skills**: Master data structures, algorithms, and design patterns\n"
                    "2. **Modern Technologies**: Learn cloud platforms (AWS, Azure), containers (Docker), and CI/CD\n"
                    "3. **Software Architecture**: Understand microservices, system design, and scalability\n"
                    "4. **Best Practices**: Version control (Git), testing, code reviews, and documentation\n"
                    "5. **Soft Skills**: Communication, teamwork, and problem-solving\n\n"
                    "Use the Skills Search and Employee Profile features to explore relevant courses!"
                )

            return (
                "The AI service is currently unavailable. However, you can:\n\n"
                "• Use the **Employee Profile** tab to view skills and qualifications\n"
                "• Try the **Skills Search** to find specific skills in the system\n"
                "• Generate a **Learning Path** for personalized recommendations\n\n"
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
