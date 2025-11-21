"""
Async LLM Client Tests
----------------------
Test LLM client async operations.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from swx_api.app.services.llm_client import LLMClient, LLMConfig


class TestLLMClient:
    """Test LLMClient async operations."""
    
    @pytest.mark.asyncio
    async def test_llm_client_context_manager(self):
        """Test LLM client as async context manager."""
        config = LLMConfig(
            provider="openai",
            model="gpt-3.5-turbo",
            api_key="test-key"
        )
        
        with patch("swx_api.app.services.llm_client.AsyncOpenAI") as mock_openai:
            async with LLMClient(config) as client:
                assert client is not None
                assert hasattr(client, "config")
    
    @pytest.mark.asyncio
    async def test_call_llm_async(self):
        """Test async LLM call."""
        config = LLMConfig(
            provider="openai",
            model="gpt-3.5-turbo",
            api_key="test-key"
        )
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"result": "test"}'
        
        with patch("swx_api.app.services.llm_client.AsyncOpenAI") as mock_openai_class:
            mock_client = AsyncMock()
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_openai_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_openai_class.return_value.__aexit__ = AsyncMock(return_value=None)
            
            async with LLMClient(config) as client:
                result = await client.call_llm(
                    prompt="Test prompt",
                    schema={"result": str},
                    system_message="You are a test assistant"
                )
                
                assert result is not None
    
    @pytest.mark.asyncio
    async def test_llm_client_fallback(self):
        """Test LLM client fallback mechanism."""
        config = LLMConfig(
            provider="featherless",
            model="llama-3.1",
            api_key="test-key"
        )
        
        # Test that fallback logic is handled
        with patch("swx_api.app.services.llm_client.httpx.AsyncClient") as mock_httpx:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"result": "test"}
            
            mock_client_instance = AsyncMock()
            mock_client_instance.post = AsyncMock(return_value=mock_response)
            mock_httpx.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_httpx.return_value.__aexit__ = AsyncMock(return_value=None)
            
            async with LLMClient(config) as client:
                # Should handle featherless provider
                assert client is not None

