#!/usr/bin/env python3
"""
Batch prediction for hardcoded positions
Predicts fitness scores for all employees against predefined positions
"""

import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from predict_employee_fitness import EmployeeFitnessPredictor
import pandas as pd

# Load environment variables
load_dotenv()

# Get Azure OpenAI credentials
API_URL = os.getenv('AZURE_OPENAI_API_URL')
API_KEY = os.getenv('AZURE_OPENAI_API_KEY')
API_VERSION = os.getenv('AZURE_OPENAI_API_VERSION')
DEPLOYMENT = os.getenv('AZURE_OPENAI_DEPLOYMENT', 'hackathon-gpt-4.1')


def load_positions_config(config_file='positions_config.json'):
    """Load hardcoded positions from JSON file"""
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config.get('positions', [])
    except FileNotFoundError:
        print(f"❌ Error: {config_file} not found")
        return []
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in {config_file}: {e}")
        return []


def predict_all_employees_for_position(predictor, position, output_file=None):
    """
    Predict fitness for all employees against a specific position
    
    Args:
        predictor: EmployeeFitnessPredictor instance
        position: Position dict with 'id', 'title', 'description'
        output_file: Optional file path to save results
    
    Returns:
        List of prediction results
    """
    if not all([API_URL, API_KEY, API_VERSION, DEPLOYMENT]):
        print("❌ Error: Missing Azure OpenAI credentials in .env file")
        return []
    
    print(f"\n{'='*70}")
    print(f"Predicting fitness for position: {position['title']}")
    print(f"{'='*70}")
    
    # Get all employees
    employees = predictor.employees
    if employees is None:
        predictor.load_data()
        employees = predictor.employees
    
    results = []
    total = len(employees)
    
    for idx, row in employees.iterrows():
        personal_number = str(row['persstat_start_month.personal_number'])
        employee_name = row.get('persstat_start_month.user_name', 'N/A')
        
        print(f"\n[{idx+1}/{total}] Processing employee {personal_number} ({employee_name})...")
        
        try:
            # Get employee profile
            profile = predictor.get_employee_profile(personal_number)
            if not profile:
                print(f"  ⚠️  Skipping - profile not found")
                continue
            
            # Make prediction
            result = predictor.predict_fitness(
                personal_number,
                target_position_id=None,
                custom_position_description=position['description'],
                api_url=API_URL,
                api_key=API_KEY,
                api_version=API_VERSION,
                deployment_name=DEPLOYMENT
            )
            
            # Extract fitness score from result if available
            # Note: The score is in the AI response text, we'll parse it
            results.append({
                'employee_id': personal_number,
                'employee_name': employee_name,
                'position_id': position['id'],
                'position_title': position['title'],
                'result': result
            })
            
            print(f"  ✓ Completed")
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
            results.append({
                'employee_id': personal_number,
                'employee_name': employee_name,
                'position_id': position['id'],
                'position_title': position['title'],
                'error': str(e)
            })
    
    # Save results if output file specified
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Results saved to {output_file}")
    
    return results


def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python batch_predict_positions.py <position_id> [output_file.json]")
        print("\nAvailable positions:")
        
        positions = load_positions_config()
        if not positions:
            print("  No positions found in positions_config.json")
            return
        
        for pos in positions:
            print(f"  - {pos['id']}: {pos['title']}")
        print("\nExample:")
        print("  python batch_predict_positions.py sap_it_professional results.json")
        return
    
    position_id = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else f"predictions_{position_id}.json"
    
    # Load positions
    positions = load_positions_config()
    if not positions:
        return
    
    # Find the requested position
    position = next((p for p in positions if p['id'] == position_id), None)
    if not position:
        print(f"❌ Error: Position '{position_id}' not found")
        print("\nAvailable positions:")
        for pos in positions:
            print(f"  - {pos['id']}: {pos['title']}")
        return
    
    # Check credentials
    if not all([API_URL, API_KEY, API_VERSION, DEPLOYMENT]):
        print("❌ Error: Missing Azure OpenAI credentials")
        print("   Please create a .env file with:")
        print("   AZURE_OPENAI_API_URL=...")
        print("   AZURE_OPENAI_API_KEY=...")
        print("   AZURE_OPENAI_API_VERSION=...")
        print("   AZURE_OPENAI_DEPLOYMENT=...")
        return
    
    # Initialize predictor
    print("📂 Initializing predictor...")
    # Use data folder by default
    script_dir = Path(__file__).parent
    data_dir = script_dir.parent / "data"
    predictor = EmployeeFitnessPredictor(data_dir=str(data_dir))
    predictor.load_data()
    
    # Run batch prediction
    results = predict_all_employees_for_position(predictor, position, output_file)
    
    print(f"\n✅ Completed! Processed {len(results)} employees")
    print(f"📊 Results saved to: {output_file}")


if __name__ == "__main__":
    main()

