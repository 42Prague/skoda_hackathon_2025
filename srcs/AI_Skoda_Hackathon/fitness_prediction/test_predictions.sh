#!/bin/bash
# Test script for predict_employee_fitness.py

echo "=========================================="
echo "Testing predict_employee_fitness.py"
echo "=========================================="
echo ""

# Test 1: List employees
echo "📋 Test 1: List Employees"
echo "------------------------"
python3 predict_employee_fitness.py list employees | head -10
echo ""

# Test 2: List positions
echo "📋 Test 2: List Positions"
echo "------------------------"
python3 predict_employee_fitness.py list positions | head -10
echo ""

# Test 3: General analysis (no target position)
echo "📊 Test 3: General Career Analysis (Employee 4241)"
echo "--------------------------------------------------"
python3 predict_employee_fitness.py 4241 2>&1 | grep -A 5 "Career Profile Summary" | head -10
echo ""

# Test 4: With target position
echo "📊 Test 4: Fitness Prediction with Target Position (Employee 4241 → Position 20002503)"
echo "--------------------------------------------------------------------------------------"
python3 predict_employee_fitness.py 4241 20002503 2>&1 | grep -E "(FITNESS SCORE|STRENGTHS|GAPS|Token Usage)" | head -10
echo ""

echo "✅ All tests completed!"
echo ""
echo "💡 Tips:"
echo "  - Use 'python predict_employee_fitness.py list employees' to see all employees"
echo "  - Use 'python predict_employee_fitness.py <employee_id>' for general analysis"
echo "  - Use 'python predict_employee_fitness.py <employee_id> <position_id>' for specific position"

