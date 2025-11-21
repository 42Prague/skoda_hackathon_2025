import requests
import sys
import json

def azure_openai_cli(api_url, api_key, api_version, deployment_name, user_message, system_message=None):
    """
    Call Azure OpenAI API
    
    Args:
        api_url: Azure OpenAI endpoint (e.g., https://your-resource.openai.azure.com)
        api_key: API key
        api_version: API version (e.g., 2024-08-01-preview)
        deployment_name: Deployment name (e.g., gpt-4o)
        user_message: User message to send
        system_message: Optional system message
    """
    headers = {
        "api-key": api_key,
        "Content-Type": "application/json"
    }
    params = {
        "api-version": api_version
    }
    
    messages = []
    if system_message:
        messages.append({"role": "system", "content": system_message})
    messages.append({"role": "user", "content": user_message})
    
    data = {
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 2000
    }

    try:
        response = requests.post(
            f"{api_url}/openai/deployments/{deployment_name}/chat/completions",
            headers=headers,
            params=params,
            json=data,
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            if "choices" in result and len(result["choices"]) > 0:
                content = result["choices"][0]["message"]["content"]
                print("✅ Response from Azure OpenAI:")
                print("-" * 60)
                print(content)
                print("-" * 60)
                
                # Print usage if available
                if "usage" in result:
                    usage = result["usage"]
                    print(f"\n📊 Token Usage:")
                    print(f"   Prompt tokens: {usage.get('prompt_tokens', 'N/A')}")
                    print(f"   Completion tokens: {usage.get('completion_tokens', 'N/A')}")
                    print(f"   Total tokens: {usage.get('total_tokens', 'N/A')}")
            else:
                print("⚠️  No response content in result")
                print(json.dumps(result, indent=2))
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
            try:
                error_detail = response.json()
                print(f"Error details: {json.dumps(error_detail, indent=2)}")
            except:
                pass
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 6:
        print("Usage: python azure_openai_cli.py <api_url> <api_key> <api_version> <deployment_name> <message> [system_message]")
        print("\nExample:")
        print("  python azure_openai_cli.py \\")
        print("    https://azureoai-hackathon.openai.azure.com \\")
        print("    your_api_key \\")
        print("    2024-08-01-preview \\")
        print("    gpt-4o \\")
        print("    'What is machine learning?'")
        print("\nWith system message:")
        print("  python azure_openai_cli.py \\")
        print("    https://azureoai-hackathon.openai.azure.com \\")
        print("    your_api_key \\")
        print("    2024-08-01-preview \\")
        print("    gpt-4o \\")
        print("    'Analyze this employee profile' \\")
        print("    'You are a career development expert'")
        sys.exit(1)

    api_url = sys.argv[1]
    api_key = sys.argv[2]
    api_version = sys.argv[3]
    deployment_name = sys.argv[4]
    user_message = sys.argv[5]
    system_message = sys.argv[6] if len(sys.argv) > 6 else None

    print(f"🚀 Calling Azure OpenAI...")
    print(f"   Endpoint: {api_url}")
    print(f"   Deployment: {deployment_name}")
    print(f"   API Version: {api_version}")
    print(f"   Message: {user_message[:50]}...")
    print()

    azure_openai_cli(api_url, api_key, api_version, deployment_name, user_message, system_message)
