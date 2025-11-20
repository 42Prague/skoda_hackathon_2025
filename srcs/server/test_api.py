"""
Test script to demonstrate the Employee Skills Analyzer API
Run this after starting the server to see how it works.
"""

import requests
import json

# Server URL
SERVER_URL = "http://localhost:5000"

def test_api():
    """Test the API endpoints"""
    print("🚀 Testing Employee Skills Analyzer API")
    print("=" * 50)
    
    try:
        # Test 1: Check if server is running
        print("\n1. Testing server connection...")
        response = requests.get(f"{SERVER_URL}/")
        if response.status_code == 200:
            print("✅ Server is running!")
            print(f"Response: {response.json()['message']}")
        else:
            print("❌ Server not responding")
            return
        
        # Test 2: Get all employees
        print("\n2. Getting all employees...")
        response = requests.get(f"{SERVER_URL}/employees")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Found {data['count']} employees")
            for emp in data['data'][:2]:  # Show first 2
                print(f"   - {emp['name']} ({emp['position']}) - {emp['skills_count']} skills")
        
        # Test 3: Get specific employee
        print("\n3. Getting employee details...")
        response = requests.get(f"{SERVER_URL}/employees/1")
        if response.status_code == 200:
            emp = response.json()['data']
            print(f"✅ Employee: {emp['name']}")
            print(f"   Position: {emp['position']}")
            print(f"   Skills: {', '.join(emp['skills'])}")
        
        # Test 4: Get skill suggestions
        print("\n4. Getting skill suggestions for employee 1...")
        response = requests.get(f"{SERVER_URL}/skills/suggestions/1")
        if response.status_code == 200:
            suggestions = response.json()['suggestions']
            print("✅ Skill suggestions:")
            if suggestions['based_on_similar_roles']:
                print(f"   Similar roles: {', '.join(suggestions['based_on_similar_roles'])}")
            if suggestions['trending_in_company']:
                print(f"   Trending: {', '.join(suggestions['trending_in_company'])}")
            if suggestions['career_advancement']:
                print(f"   Career growth: {', '.join(suggestions['career_advancement'])}")
        
        # Test 5: Add new employee
        print("\n5. Adding new employee...")
        new_employee = {
            "name": "Alice Brown",
            "position": "DevOps Engineer",
            "skills": ["Docker", "Kubernetes", "AWS", "Linux", "Python"],
            "experience_years": 4,
            "department": "IT"
        }
        
        response = requests.post(
            f"{SERVER_URL}/employees",
            headers={'Content-Type': 'application/json'},
            data=json.dumps(new_employee)
        )
        
        if response.status_code == 201:
            print("✅ New employee added successfully!")
            new_emp = response.json()['data']
            print(f"   ID: {new_emp['employee_id']}, Name: {new_emp['name']}")
        
        # Test 6: Skills gap analysis
        print("\n6. Analyzing skills gap for IT department...")
        analysis_request = {"department": "IT"}
        response = requests.post(
            f"{SERVER_URL}/skills/analyze",
            headers={'Content-Type': 'application/json'},
            data=json.dumps(analysis_request)
        )
        
        if response.status_code == 200:
            analysis = response.json()['analysis']
            print(f"✅ Analysis for {analysis['scope']}")
            print(f"   Total employees: {analysis['total_employees']}")
            print(f"   Unique skills: {analysis['total_unique_skills']}")
            print("   Top skills:")
            for skill in analysis['skill_analysis'][:3]:
                print(f"     - {skill['skill']}: {skill['coverage_percentage']}% coverage ({skill['gap_level']})")
        
        print("\n🎉 All tests completed successfully!")
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Make sure it's running on localhost:5000")
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")

def print_usage_examples():
    """Print some usage examples"""
    print("\n📚 API Usage Examples:")
    print("=" * 50)
    
    examples = [
        {
            "description": "Get all employees",
            "method": "GET",
            "url": "/employees",
            "example": "curl http://localhost:5000/employees"
        },
        {
            "description": "Get employee by ID",
            "method": "GET", 
            "url": "/employees/1",
            "example": "curl http://localhost:5000/employees/1"
        },
        {
            "description": "Add new employee",
            "method": "POST",
            "url": "/employees",
            "example": 'curl -X POST http://localhost:5000/employees -H "Content-Type: application/json" -d \'{"name": "John Doe", "position": "Developer", "skills": ["Python", "SQL"]}\''
        },
        {
            "description": "Get skill suggestions",
            "method": "GET",
            "url": "/skills/suggestions/1", 
            "example": "curl http://localhost:5000/skills/suggestions/1"
        }
    ]
    
    for i, example in enumerate(examples, 1):
        print(f"\n{i}. {example['description']}")
        print(f"   {example['method']} {example['url']}")
        print(f"   Example: {example['example']}")

if __name__ == "__main__":
    print("Employee Skills Analyzer - API Test Script")
    print("Make sure the server is running first!")
    print("Start server with: python app.py")
    
    import time
    print("\nWaiting 3 seconds before testing...")
    time.sleep(3)
    
    test_api()
    print_usage_examples()
