#!/usr/bin/env python3
"""Direct LLM test to verify Featherless is working"""

import asyncio
import os
import sys
from pathlib import Path

# Set environment before imports
os.environ["FEATHERLESS_API_KEY"] = "rc_3ee2d3406dbcd1e67c60369fbeef1f6cc27f2314d12ae8f8fa135dad30cf774b"
os.environ["SKILL_LLM_PROVIDER"] = "featherless"
os.environ["LOG_LEVEL"] = "info"
os.environ["USE_TONE"] = "false"  # Disable TONE for simpler test

sys.path.insert(0, str(Path(__file__).parent))

async def test():
    from swx_api.app.services.llm_client import LLMClient, LLMConfig
    
    config = LLMConfig.from_env()
    print(f"Provider: {config.provider}")
    print(f"Model: {config.model}")
    print(f"Endpoint: {config.endpoint}")
    print(f"API Key: {config.api_key[:10]}...")
    
    print("\nMaking LLM call...")
    async with LLMClient(config) as llm:
        schema = {"response": str}
        result = await llm.call_llm(
            prompt="Hello from Škoda AI Skill Coach. Reply with a random 7-word sentence.",
            schema=schema,
            system_message="You are a helpful assistant.",
            temperature=0.7,
            max_tokens=50
        )
        print(f"Result: {result}")
        print(f"Response: {result.get('response', 'EMPTY')}")

if __name__ == "__main__":
    asyncio.run(test())

