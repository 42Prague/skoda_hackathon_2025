#!/usr/bin/env python3
"""
Predict employee fitness for SAP IT position
"""

import sys
import os
import json
from pathlib import Path
from dotenv import load_dotenv
from predict_employee_fitness import EmployeeFitnessPredictor

# Load environment variables from .env file
load_dotenv()

# Azure OpenAI Configuration from environment variables
API_URL = os.getenv('AZURE_OPENAI_API_URL')
API_KEY = os.getenv('AZURE_OPENAI_API_KEY')
API_VERSION = os.getenv('AZURE_OPENAI_API_VERSION')
DEPLOYMENT = os.getenv('AZURE_OPENAI_DEPLOYMENT', 'hackathon-gpt-4.1')

# SAP IT Position Description
SAP_POSITION_DESCRIPTION = """SAP IT Professional - SAP Competence Center

Škoda Auto is looking for experienced SAP IT professionals for its SAP Competence Center to deliver services for the VW Group (VW, Audi, Seat, Porsche, Bentley). We offer career growth in an international environment that also values work-life balance.

Location: Prague or Mladá Boleslav

What will you do with us?
- Deliver solution in SAP financial modules with focus on the entire lifecycle of SW product TranS/4m (analysis, solution design and development, testing and deployment).
- Review business function proposals and suggest optimizations of app, systems and processes within the scope.
- Create and maintain automated processes for deployment, testing, and monitoring of SAP systems.
- Collaborate with other VW IT departments, Škoda IT, relevant corporate stakeholders, and external suppliers
- Deliver, implement and manage Continuous Integrations/Continuous Deployment (CI/CD)
- Coordinate function verifications, analyze and evaluate issues in the delivered solutions.

What do you need to know, have, and be able to do?
- University degree.
- Professional experience: 3 years plus.
- English at minimum B2 level – communicative.
- SAP financial modules experience
- TranS/4m lifecycle experience (analysis, design, development, testing, deployment)
- CI/CD implementation and management
- Automated processes for deployment, testing, and monitoring
- Collaboration with IT departments and stakeholders
"""

def main():
    # Check if credentials are available
    if not all([API_URL, API_KEY, API_VERSION, DEPLOYMENT]):
        print("❌ Error: Missing Azure OpenAI credentials")
        print("   Please set environment variables in .env file:")
        print("   - AZURE_OPENAI_API_URL")
        print("   - AZURE_OPENAI_API_KEY")
        print("   - AZURE_OPENAI_API_VERSION")
        print("   - AZURE_OPENAI_DEPLOYMENT")
        sys.exit(1)
    
    # Get employee_id from command line argument or use default
    if len(sys.argv) > 1:
        try:
            employee_id = int(sys.argv[1])
        except ValueError:
            print(f"❌ Error: Invalid employee ID: {sys.argv[1]}")
            sys.exit(1)
    else:
        employee_id = 17425  # Default for testing
    
    print("=" * 70)
    print("SAP IT Position Fitness Prediction")
    print("=" * 70)
    print(f"Employee ID: {employee_id}")
    print(f"Position: SAP IT Professional - SAP Competence Center")
    print()
    
    # Initialize predictor with data folder path
    script_dir = Path(__file__).parent
    data_dir = script_dir.parent / "data"
    predictor = EmployeeFitnessPredictor(data_dir=str(data_dir))
    predictor.load_data()
    
    # Get employee profile first to show it
    profile = predictor.get_employee_profile(str(employee_id))
    if not profile:
        print(f"❌ Employee {employee_id} not found")
        return
    
    print("📋 Employee Profile Summary:")
    print(f"   Current Profession: {profile['current_profession']}")
    print(f"   Planned Position: {profile['planned_position']}")
    print(f"   Education: {profile['education_branch']} - {profile['field_of_study']}")
    print(f"   Qualifications: {profile['num_qualifications']} found")
    print(f"   Courses Completed: {profile['num_courses']} found")
    print()
    
    # Run prediction
    result = predictor.predict_fitness(
        str(employee_id),
        target_position_id=None,
        custom_position_description=SAP_POSITION_DESCRIPTION,
        api_url=API_URL,
        api_key=API_KEY,
        api_version=API_VERSION,
        deployment_name=DEPLOYMENT
    )
    
    if "error" in result:
        print(f"\n❌ Error: {result['error']}")
        sys.exit(1)
    
    # Output JSON result for backend consumption
    output = {
        "employee_id": str(employee_id),
        "fitness_score": result.get("fitness_score"),
        "success": result.get("fitness_score") is not None
    }
    print("\n" + json.dumps(output))

if __name__ == "__main__":
    main()

