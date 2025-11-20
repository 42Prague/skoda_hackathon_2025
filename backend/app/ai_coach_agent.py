"""
AI Coach Agent using Hosted LLM API.

Supports any OpenAI-compatible API endpoint (Azure OpenAI, OpenAI, etc.).
Configured via environment variables for security.

USER ACTIONS REQUIRED:
1. Set LLM_API_URL in environment
2. Set LLM_API_KEY in environment
3. Set LLM_API_VERSION (if using Azure OpenAI)
4. Set LLM_MODEL_NAME (deployment/model name)
"""

import logging
import json
from typing import Optional, Dict, Any
import requests
from config import settings

logger = logging.getLogger(__name__)


class AICoachAgent:
    """
    AI Coach for answering skill development questions using hosted LLM API.
    
    Supports OpenAI-compatible endpoints (Azure OpenAI, OpenAI, custom deployments).
    """
    
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
        """
        Check if API is properly configured.
        
        Returns True if configuration is valid, False otherwise.
        """
        if not self.api_url or self.api_url == "https://api.example.com/v1/chat/completions":
            logger.error("LLM_API_URL not configured. Set it in environment variables.")
            return False
        
        if not self.api_key:
            logger.error("LLM_API_KEY not configured. Set it in environment variables.")
            return False
        
        logger.info(f"API configuration valid: {self.api_url}")
        return True
    
    def test_connection(self) -> bool:
        """
        Test connection to hosted LLM API.
        
        Returns True if connection successful, False otherwise.
        """
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
        """
        Call the hosted LLM API.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
        
        Returns:
            API response dict
        """
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
        """
        Answer a user's question using the hosted LLM API.
        
        Args:
            user_input: The user's question
            context: Optional context (e.g., employee profile, skills, gaps)
        
        Returns:
            LLM's response as a string
        """
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
                return "I apologize, but I couldn't generate a response. Please try again."
            
            message = choices[0].get('message', {})
            answer = message.get('content', '').strip()
            
            if not answer:
                return "I apologize, but I couldn't generate a response. Please try rephrasing your question."
            
            return answer
        
        except Exception as e:
            logger.error(f"LLM API call failed: {e}")
            return f"I encountered an error while processing your question: {str(e)}"
    
    def generate_learning_path(self, 
                                current_skills: list,
                                target_role: str,
                                missing_qualifications: list) -> str:
        """
        Generate a personalized learning path.
        
        Args:
            current_skills: List of skill names the employee currently has
            target_role: Target role/position
            missing_qualifications: List of qualification names needed
        
        Returns:
            Formatted learning path recommendation
        """
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
        """
        Explain why a particular skill is important for a role.
        
        Args:
            skill_name: Name of the skill
            role_context: Description or name of the role
        
        Returns:
            Explanation of the skill's importance
        """
        question = (
            f"Why is '{skill_name}' important for {role_context}? "
            f"What are practical applications of this skill?"
        )
        
        return self.answer_question(question)


# Global instance (lazy-loaded)
_coach_instance: Optional[AICoachAgent] = None


def get_coach() -> AICoachAgent:
    """
    Get or create the global AI coach instance.
    
    This implements singleton pattern for model reuse across requests.
    """
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
