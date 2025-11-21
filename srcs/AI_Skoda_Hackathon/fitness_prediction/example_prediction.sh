#!/bin/bash
# Example script for running employee fitness predictions

# Load environment variables from .env file
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "⚠️  Warning: .env file not found. Using environment variables or defaults."
fi

# Azure OpenAI Configuration (from .env or environment)
API_URL="${AZURE_OPENAI_API_URL}"
API_KEY="${AZURE_OPENAI_API_KEY}"
API_VERSION="${AZURE_OPENAI_API_VERSION}"
DEPLOYMENT="${AZURE_OPENAI_DEPLOYMENT:-hackathon-gpt-4.1}"

# Check if credentials are set
if [ -z "$API_URL" ] || [ -z "$API_KEY" ]; then
    echo "❌ Error: Azure OpenAI credentials not found"
    echo "   Please create a .env file with:"
    echo "   AZURE_OPENAI_API_URL=..."
    echo "   AZURE_OPENAI_API_KEY=..."
    echo "   AZURE_OPENAI_API_VERSION=..."
    echo "   AZURE_OPENAI_DEPLOYMENT=..."
    exit 1
fi

# Example 1: List available employees
echo "=== Listing Available Employees ==="
python3 predict_employee_fitness.py list employees

echo -e "\n=== Listing Available Positions ==="
python3 predict_employee_fitness.py list positions

# Example 2: Predict fitness for employee 4241 without target position
# (Using environment variables from .env)
echo -e "\n=== Predicting Fitness for Employee 4241 (General Analysis) ==="
python3 predict_employee_fitness.py 4241

# Example 3: Predict fitness for employee 4241 for position 20002503
echo -e "\n=== Predicting Fitness for Employee 4241 → Position 20002503 ==="
python3 predict_employee_fitness.py 4241 20002503

# Example 4: Using explicit credentials (overrides .env)
echo -e "\n=== Predicting with Explicit Credentials ==="
python3 predict_employee_fitness.py \
  "$API_URL" \
  "$API_KEY" \
  "$API_VERSION" \
  "$DEPLOYMENT" \
  4241 \
  20002503

