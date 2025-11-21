"""
Script to train the AI models with your data
"""
import pandas as pd
import os
from ai_training import AITrainingPipeline, SkillMatchingAI, ReadinessPredictionAI
from data_models import DataLoader


def create_training_data_template():
    """
    Create a template Excel file for training data
    This shows the format needed for training
    """
    print("📝 Creating training data template...")
    
    # Sample data for course-skill mappings
    course_skills_data = {
        'course_id': ['C001', 'C001', 'C002', 'C003', 'C003', 'C004'],
        'course_text': [
            'Python Programming Fundamentals - Learn basics of Python',
            'Python Programming Fundamentals - Learn basics of Python',
            'Advanced SQL Database Management - Master SQL queries',
            'Project Management Professional Certification',
            'Project Management Professional Certification',
            'Leadership Skills for Managers'
        ],
        'skill_name': ['Python', 'Programming', 'SQL', 'Project Management', 
                      'Leadership', 'Leadership']
    }
    
    # Sample data for employee readiness scores
    employee_readiness_data = {
        'employee_id': ['0001689', '0001690', '0001691', '0001692', '0001693'],
        'readiness_score': [85.0, 72.5, 90.0, 45.0, 68.0],
        'notes': [
            'Strong technical skills, ready for senior role',
            'Needs more experience in leadership',
            'Fully prepared for promotion',
            'Significant skill gaps remain',
            'Good progress, needs 1-2 more courses'
        ]
    }
    
    # Create Excel file with both sheets
    template_path = 'training_data_template.xlsx'
    
    with pd.ExcelWriter(template_path, engine='openpyxl') as writer:
        pd.DataFrame(course_skills_data).to_excel(
            writer, sheet_name='course_skills', index=False
        )
        pd.DataFrame(employee_readiness_data).to_excel(
            writer, sheet_name='employee_readiness', index=False
        )
    
    print(f"  ✓ Template created: {template_path}")
    print("\n📋 Fill in this template with your actual training data:")
    print("  • course_skills: Map courses to the skills they teach")
    print("  • employee_readiness: Actual readiness scores from performance reviews")
    return template_path


def prepare_training_data_from_existing(data_folder: str, output_file: str = 'my_training_data.xlsx'):
    """
    Extract training data from your existing data files
    This creates a starting point that you can then manually label
    """
    print("\n🔍 Extracting data from existing files...")
    
    # Load existing data
    excel_files = [f for f in os.listdir(data_folder) if f.endswith('.xlsx')]
    if not excel_files:
        print(f"  ❌ No Excel files found in {data_folder}")
        return None
    
    print(f"  Found {len(excel_files)} Excel files")
    
    # Extract course-skill pairs from Skill_mapping.xlsx
    course_skills_rows = []
    
    for file in excel_files:
        file_path = os.path.join(data_folder, file)
        print(f"  Processing: {file}")
        
        try:
            df = pd.read_excel(file_path)
            
            # Check for course-skill mapping file
            if 'ID Kurzu' in df.columns and 'Kompetence / Skill' in df.columns:
                print(f"    → Found course-skill data")
                for _, row in df.iterrows():
                    if pd.notna(row['ID Kurzu']) and pd.notna(row['Kompetence / Skill']):
                        course_id = str(row['ID Kurzu'])
                        course_text = str(row.get('Název D', row.get('Content Title', '')))
                        
                        # Split competencies (can be comma or semicolon separated)
                        comp_str = str(row['Kompetence / Skill'])
                        # Try comma first, then semicolon
                        if ',' in comp_str:
                            skills = [s.strip() for s in comp_str.split(',')]
                        elif ';' in comp_str:
                            skills = [s.strip() for s in comp_str.split(';')]
                        else:
                            skills = [comp_str.strip()]
                        
                        for skill in skills:
                            if skill and skill.lower() not in ['nan', 'none', '']:
                                course_skills_rows.append({
                                    'course_id': course_id,
                                    'course_text': course_text,
                                    'skill_name': skill
                                })
            
            # Also extract from Degreed data if available
            elif 'Content Title' in df.columns and 'Content ID' in df.columns:
                print(f"    → Found Degreed course data")
                # Group by Content ID to get unique courses
                unique_courses = df[['Content ID', 'Content Title']].drop_duplicates()
                for _, row in unique_courses.head(100).iterrows():  # Limit to 100 for now
                    if pd.notna(row['Content ID']) and pd.notna(row['Content Title']):
                        course_skills_rows.append({
                            'course_id': str(row['Content ID']),
                            'course_text': str(row['Content Title']),
                            'skill_name': 'NEEDS_LABELING'  # User needs to fill this in
                        })
        
        except Exception as e:
            print(f"    ⚠️  Could not process: {e}")
    
    course_skills_df = pd.DataFrame(course_skills_rows).drop_duplicates()
    
    # Extract employees from ERP file
    employee_readiness_rows = []
    
    for file in excel_files:
        file_path = os.path.join(data_folder, file)
        
        try:
            df = pd.read_excel(file_path)
            
            if 'persstat_start_month.personal_number' in df.columns:
                print(f"  Processing employees from: {file}")
                employee_ids = df['persstat_start_month.personal_number'].dropna().unique()
                
                for emp_id in employee_ids:
                    employee_readiness_rows.append({
                        'employee_id': str(int(emp_id)),
                        'readiness_score': None,  # You need to fill this in!
                        'notes': 'TODO: Add actual readiness score from performance review'
                    })
        except Exception as e:
            pass
    
    employee_readiness_df = pd.DataFrame(employee_readiness_rows)
    
    # Save to Excel
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        course_skills_df.to_excel(writer, sheet_name='course_skills', index=False)
        employee_readiness_df.to_excel(writer, sheet_name='employee_readiness', index=False)
    
    print(f"  ✓ Extracted training data saved to: {output_file}")
    print(f"  ✓ Found {len(course_skills_df)} course-skill mappings")
    print(f"  ✓ Found {len(employee_readiness_df)} employees")
    print("\n⚠️  IMPORTANT: You must manually fill in the 'readiness_score' column")
    print("    with actual scores from performance reviews or assessments!")
    
    return output_file


def train_models(training_data_file: str):
    """
    Train AI models using the prepared training data
    """
    print("\n" + "="*70)
    print("TRAINING AI MODELS")
    print("="*70)
    
    if not os.path.exists(training_data_file):
        print(f"❌ Training data file not found: {training_data_file}")
        return False
    
    try:
        # Load training data
        print("\n📚 Loading training data...")
        course_skills_df = pd.read_excel(training_data_file, sheet_name='course_skills')
        employee_readiness_df = pd.read_excel(training_data_file, sheet_name='employee_readiness')
        
        print(f"  ✓ Loaded {len(course_skills_df)} course-skill pairs")
        print(f"  ✓ Loaded {len(employee_readiness_df)} employee records")
        
        # Check if we have enough data
        if len(course_skills_df) < 10:
            print("\n⚠️  Warning: Less than 10 course-skill pairs. Need more training data.")
            return False
        
        # Check if readiness scores are filled in
        missing_scores = employee_readiness_df['readiness_score'].isna().sum()
        if missing_scores > 0:
            print(f"\n⚠️  Note: {missing_scores} employees missing readiness scores")
            print("    → Will train Skill Matching AI only (employee readiness skipped)")
            train_readiness = False
        else:
            train_readiness = True
        
        # Initialize training pipeline
        pipeline = AITrainingPipeline()
        
        # Train Skill Matching AI
        print("\n" + "-"*70)
        print("1. Training Skill Matching AI")
        print("-"*70)
        
        skill_ai = SkillMatchingAI()
        
        # Prepare data from DataFrame
        X_texts = course_skills_df['course_text'].tolist()
        y_labels = course_skills_df['skill_name'].tolist()
        
        # Vectorize and encode
        from sklearn.preprocessing import LabelEncoder
        X = skill_ai.vectorizer.fit_transform(X_texts)
        skill_ai.skill_encoder = LabelEncoder()
        y = skill_ai.skill_encoder.fit_transform(y_labels)
        
        # Train
        results = skill_ai.train(X, y)
        
        # Save
        skill_ai.save_model('models')
        
        print("\n✅ Skill Matching AI trained successfully!")
        
        # You can add Readiness Prediction AI training here if you have employee features
        
        print("\n" + "="*70)
        print("TRAINING COMPLETE!")
        print("="*70)
        print("\n💾 Models saved to: models/")
        print("\n🚀 Next steps:")
        print("  1. Integrate trained models into main.py")
        print("  2. Use trained AI for better predictions")
        print("  3. Periodically retrain with new data")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error during training: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main training workflow"""
    print("="*70)
    print("AI TRAINING WORKFLOW - Skill Gap Analysis")
    print("="*70)
    
    print("\nWhat would you like to do?")
    print("1. Create training data template (for new users)")
    print("2. Extract training data from existing Excel files")
    print("3. Train AI models (with prepared training data)")
    print("4. Full workflow (extract + train)")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    if choice == '1':
        create_training_data_template()
        
    elif choice == '2':
        data_folder = input("Enter path to data folder [./data]: ").strip() or './data'
        output_file = input("Enter output filename [my_training_data.xlsx]: ").strip() or 'my_training_data.xlsx'
        prepare_training_data_from_existing(data_folder, output_file)
        
    elif choice == '3':
        training_file = input("Enter training data file [my_training_data.xlsx]: ").strip() or 'my_training_data.xlsx'
        train_models(training_file)
        
    elif choice == '4':
        # Full workflow
        data_folder = input("Enter path to data folder [./data]: ").strip() or './data'
        training_file = 'my_training_data.xlsx'
        
        # Extract
        result = prepare_training_data_from_existing(data_folder, training_file)
        
        if result:
            print("\n⏸️  Please fill in the 'readiness_score' column in the Excel file")
            print(f"   File: {training_file}")
            
            proceed = input("\nHave you filled in the readiness scores? (yes/no): ").strip().lower()
            
            if proceed == 'yes':
                train_models(training_file)
            else:
                print("\n📝 Fill in the scores and run option 3 to train models")
    else:
        print("Invalid choice")


if __name__ == "__main__":
    main()
