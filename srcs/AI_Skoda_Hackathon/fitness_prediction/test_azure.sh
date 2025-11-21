#!/bin/bash

# Test Azure OpenAI CLI
# Usage: ./test_azure.sh

cd "$(dirname "$0")"
source venv/bin/activate

# Get Azure OpenAI config from backend .env
ENDPOINT=$(cd ../../backend && grep AZURE_OPENAI_ENDPOINT .env 2>/dev/null | cut -d'=' -f2 | tr -d '"' || echo "")
API_KEY=$(cd ../../backend && grep AZURE_OPENAI_API_KEY .env 2>/dev/null | cut -d'=' -f2 | tr -d '"' || echo "")
API_VERSION=$(cd ../../backend && grep AZURE_OPENAI_API_VERSION .env 2>/dev/null | cut -d'=' -f2 | tr -d '"' || echo "2024-08-01-preview")
DEPLOYMENT=$(cd ../../backend && grep AZURE_OPENAI_DEPLOYMENT_NAME .env 2>/dev/null | cut -d'=' -f2 | tr -d '"' || echo "gpt-4o")

if [ -z "$ENDPOINT" ] || [ -z "$API_KEY" ]; then
    echo "⚠️  Azure OpenAI not configured in backend/.env"
    echo "Please add:"
    echo "  AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com"
    echo "  AZURE_OPENAI_API_KEY=your-api-key"
    exit 1
fi

echo "🧪 Testing Azure OpenAI..."
echo "   Endpoint: $ENDPOINT"
echo "   Deployment: $DEPLOYMENT"
echo ""

python3 azure_openai_cli.py \
  "$ENDPOINT" \
  "$API_KEY" \
  "$API_VERSION" \
  "$DEPLOYMENT" \
  "Hello! Can you help me test the Azure OpenAI connection?"

