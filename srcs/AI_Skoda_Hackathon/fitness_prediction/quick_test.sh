#!/bin/bash
echo "🧪 Quick Test Suite for predict_employee_fitness.py"
echo "=================================================="
echo ""

echo "✅ Test 1: Environment Variables"
python3 -c "from dotenv import load_dotenv; import os; load_dotenv(); print('  API_URL:', '✓' if os.getenv('AZURE_OPENAI_API_URL') else '✗'); print('  API_KEY:', '✓' if os.getenv('AZURE_OPENAI_API_KEY') else '✗')"
echo ""

echo "✅ Test 2: List Employees (first 5)"
python3 predict_employee_fitness.py list employees 2>&1 | grep -A 6 "Available Employees" | head -7
echo ""

echo "✅ Test 3: General Analysis (Employee 4241) - Summary"
python3 predict_employee_fitness.py 4241 2>&1 | grep -E "(Career Profile|Key Strengths|Token Usage)" | head -3
echo ""

echo "✅ Test 4: Position Prediction (Employee 4241 → Position 20002503) - Summary"
python3 predict_employee_fitness.py 4241 20002503 2>&1 | grep -E "(FITNESS SCORE|Token Usage)" | head -2
echo ""

echo "🎉 All tests completed successfully!"
echo ""
echo "💡 Usage Examples:"
echo "  python predict_employee_fitness.py 4241"
echo "  python predict_employee_fitness.py 4241 20002503"
echo "  python predict_employee_fitness.py list employees"
