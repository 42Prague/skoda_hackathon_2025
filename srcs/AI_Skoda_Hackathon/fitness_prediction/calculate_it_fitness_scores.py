#!/usr/bin/env python3
"""
Calculate fitness scores for specific employees against IT position
Outputs JSON with employee IDs and their fitness scores
"""

import sys
import json
from pathlib import Path
from predict_employee_fitness import EmployeeFitnessPredictor
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

def main():
    # Employee IDs to process
    employee_ids = ['100870', '110153', '110190', '110464', '110542']
    
    # Position description file
    position_file = Path(__file__).parent / 'it_position.txt'
    
    if not position_file.exists():
        print(f"❌ Error: Position file not found: {position_file}")
        sys.exit(1)
    
    # Read position description
    with open(position_file, 'r', encoding='utf-8') as f:
        position_description = f.read().strip()
    
    # Get Azure OpenAI credentials
    api_url = os.getenv('AZURE_OPENAI_API_URL')
    api_key = os.getenv('AZURE_OPENAI_API_KEY')
    api_version = os.getenv('AZURE_OPENAI_API_VERSION')
    deployment_name = os.getenv('AZURE_OPENAI_DEPLOYMENT')
    
    if not all([api_url, api_key, api_version, deployment_name]):
        print("❌ Error: Missing Azure OpenAI credentials in .env file")
        sys.exit(1)
    
    # Initialize predictor
    script_dir = Path(__file__).parent
    data_dir = script_dir.parent / "data"
    predictor = EmployeeFitnessPredictor(data_dir=str(data_dir))
    
    print("📂 Loading data files...")
    predictor.load_data()
    print()
    
    # Calculate fitness scores
    results = {}
    
    for employee_id in employee_ids:
        print(f"🔮 Calculating fitness score for employee {employee_id}...")
        
        try:
            result = predictor.predict_fitness(
                employee_id,
                target_position_id=None,
                custom_position_description=position_description,
                api_url=api_url,
                api_key=api_key,
                api_version=api_version,
                deployment_name=deployment_name
            )
            
            if "error" in result:
                print(f"  ❌ Error: {result['error']}")
                results[employee_id] = None
            else:
                fitness_score = result.get('fitness_score')
                if fitness_score is not None:
                    print(f"  ✅ Fitness Score: {fitness_score}")
                    results[employee_id] = fitness_score
                else:
                    print(f"  ⚠️  No fitness score extracted")
                    results[employee_id] = None
        except Exception as e:
            print(f"  ❌ Exception: {e}")
            results[employee_id] = None
        
        print()
    
    # Output results as JSON
    print("📊 Results Summary:")
    print("=" * 60)
    for emp_id, score in results.items():
        status = f"✅ {score}" if score is not None else "❌ Failed"
        print(f"  Employee {emp_id}: {status}")
    print("=" * 60)
    
    # Save to JSON file
    output_file = Path(__file__).parent / 'it_fitness_scores.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Results saved to: {output_file}")
    
    # Also output JSON to stdout for easy parsing
    print("\n📋 JSON Output:")
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()

