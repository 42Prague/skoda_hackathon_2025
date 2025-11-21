"""
Simple one-step training: Extract from data folder and train immediately
"""
import pandas as pd
import os
from ai_training import SkillMatchingAI
from sklearn.preprocessing import LabelEncoder
import re

def extract_and_train_from_data_folder(data_folder='data', num_courses=500):
    """
    Extract data from folder, auto-label skills, and train AI in one step
    """
    print("="*70)
    print("ONE-STEP AI TRAINING FROM DATA FOLDER")
    print("="*70)
    
    # Step 1: Load all Excel files
    print(f"\n📂 Step 1: Loading data from {data_folder}/")
    excel_files = [f for f in os.listdir(data_folder) if f.endswith('.xlsx')]
    print(f"   Found {len(excel_files)} Excel files")
    
    all_courses = []
    
    # Step 2: Extract courses from all files
    print(f"\n📊 Step 2: Extracting courses...")
    
    for file in excel_files:
        file_path = os.path.join(data_folder, file)
        try:
            df = pd.read_excel(file_path)
            
            # From Degreed data
            if 'Content Title' in df.columns and 'Content ID' in df.columns:
                print(f"   ✓ Extracting from {file}")
                # Get most completed courses
                courses = df[['Content ID', 'Content Title']].drop_duplicates()
                for _, row in courses.head(num_courses).iterrows():
                    if pd.notna(row['Content Title']):
                        all_courses.append({
                            'course_id': str(row['Content ID']),
                            'course_text': str(row['Content Title'])
                        })
            
            # From Skill_mapping data (if it has skills)
            elif 'ID Kurzu' in df.columns and 'Název D' in df.columns:
                print(f"   ✓ Extracting from {file}")
                for _, row in df.head(num_courses).iterrows():
                    if pd.notna(row.get('Název D')) or pd.notna(row.get('ID Kurzu')):
                        all_courses.append({
                            'course_id': str(row['ID Kurzu']),
                            'course_text': str(row.get('Název D', ''))
                        })
                        
        except Exception as e:
            print(f"   ⚠️  Skipped {file}: {e}")
    
    print(f"\n   Total courses extracted: {len(all_courses)}")
    
    if len(all_courses) < 10:
        print("\n❌ Error: Need at least 10 courses to train")
        return False
    
    # Step 3: Auto-label skills based on course titles
    print(f"\n🏷️  Step 3: Auto-labeling skills from course titles...")
    
    skill_patterns = {
        'Excel': ['excel', 'tabulk', 'spreadsheet', 'kontingenční', 'sešit', 'vzorce'],
        'PowerPoint': ['powerpoint', 'ppt', 'prezentace', 'presentation', 'snímk'],
        'Word': ['word', 'dokument', 'document writing', 'text', 'psaní'],
        'Microsoft 365': ['microsoft 365', 'm365', 'office 365', 'teams', 'ekosystém microsoft'],
        'Cloud': ['cloud', 'onedrive', 'sharepoint', 'storage', 'soubory v cloudu', 'úložiště'],
        'Email': ['email', 'outlook', 'inbox', 'e-mail', 'pošta', 'zero inbox'],
        'Data Analysis': ['data analyz', 'data analysis', 'analytics', 'visualization', 'tableau', 'power bi', 'práce s daty', 'analýza dat'],
        'Project Management': ['project', 'jira', 'agile', 'scrum', 'kanban', 'projekt', 'řízení projekt'],
        'AI': ['ai', 'artificial intelligence', 'machine learning', 'chatgpt', 'gpt', 'umělá inteligence', 'strojové učení'],
        'Communication': ['communication', 'komunikace', 'public speaking', 'writing', 'prezentování', 'vystupování'],
        'Leadership': ['leadership', 'leader', 'management', 'manager', 'vedení', 'lídr', 'vedoucí'],
        'Programming': ['python', 'java', 'javascript', 'coding', 'programming', 'developer', 'programování', 'vývoj', 'kód'],
        'SQL': ['sql', 'database', 'query', 'databáz', 'dotaz'],
        'Design': ['design', 'canva', 'photoshop', 'figma', 'graphics', 'grafik', 'návrh'],
        'Collaboration': ['collaboration', 'teamwork', 'team', 'spolupráce', 'týmová práce', 'tým'],
        'Security': ['security', 'cybersecurity', 'privacy', 'bezpečnost', 'zabezpečení', 'kybernetick'],
        'Soft Skills': ['soft skill', 'etika', 'etiquette', 'emotional intelligence', 'měkké dovednosti', 'empatie', 'codex', 'decorum'],
        'Sales': ['sales', 'selling', 'customer', 'crm', 'prodej', 'zákazník'],
        'Marketing': ['marketing', 'branding', 'social media', 'značka', 'reklama'],
        'Finance': ['finance', 'accounting', 'budget', 'účetnictví', 'finanční', 'rozpočet'],
    }
    
    labeled_data = []
    
    for course in all_courses:
        course_text = course['course_text'].lower()
        matched_skills = []
        
        for skill, keywords in skill_patterns.items():
            for keyword in keywords:
                if keyword.lower() in course_text:
                    matched_skills.append(skill)
                    break
        
        # If no match, assign generic skill
        if not matched_skills:
            matched_skills = ['Professional Development']
        
        # Add one entry per skill
        for skill in matched_skills:
            labeled_data.append({
                'course_id': course['course_id'],
                'course_text': course['course_text'],
                'skill_name': skill
            })
    
    print(f"   ✓ Created {len(labeled_data)} course-skill mappings")
    print(f"   ✓ Covering {len(set([x['skill_name'] for x in labeled_data]))} unique skills")
    
    # Show skill distribution
    from collections import Counter
    skill_counts = Counter([x['skill_name'] for x in labeled_data])
    print(f"\n   Top skills:")
    for skill, count in skill_counts.most_common(10):
        print(f"     • {skill}: {count} courses")
    
    # Step 4: Train the AI
    print(f"\n🎓 Step 4: Training AI model...")
    
    # Prepare training data
    X_texts = [item['course_text'] for item in labeled_data]
    y_labels = [item['skill_name'] for item in labeled_data]
    
    # Create and train model
    skill_ai = SkillMatchingAI()
    X = skill_ai.vectorizer.fit_transform(X_texts)
    skill_ai.skill_encoder = LabelEncoder()
    y = skill_ai.skill_encoder.fit_transform(y_labels)
    
    # Train
    results = skill_ai.train(X, y)
    
    # Step 5: Save model
    print(f"\n💾 Step 5: Saving model...")
    os.makedirs('models', exist_ok=True)
    skill_ai.save_model('models')
    
    # Step 6: Test the model
    print(f"\n🧪 Step 6: Testing trained model...")
    test_courses = [
        "Python Programming for Data Science",
        "Advanced Excel and Power BI",
        "Leadership and Team Management",
        "Cloud Computing with AWS"
    ]
    
    for test in test_courses:
        predictions = skill_ai.predict_skills_for_course(test, top_k=2)
        print(f"\n   '{test}'")
        for skill, conf in predictions:
            print(f"      → {skill}: {conf:.0%}")
    
    print(f"\n{'='*70}")
    print("✅ TRAINING COMPLETE!")
    print("="*70)
    print(f"\n📊 Results:")
    print(f"   • Training accuracy: {results['train_acc']:.1%}")
    print(f"   • Validation accuracy: {results['val_acc']:.1%}")
    print(f"   • Total examples: {len(labeled_data)}")
    print(f"   • Model saved to: models/")
    print(f"\n🚀 Your AI is ready to use!")
    
    return True


if __name__ == "__main__":
    import sys
    
    # Get parameters
    data_folder = sys.argv[1] if len(sys.argv) > 1 else 'data'
    num_courses = int(sys.argv[2]) if len(sys.argv) > 2 else 500
    
    print(f"\nTraining with {num_courses} courses from {data_folder}/\n")
    
    success = extract_and_train_from_data_folder(data_folder, num_courses)
    
    if success:
        print("\n✨ Done! Run this to test:")
        print("   python -c 'from ai_training import SkillMatchingAI; ai = SkillMatchingAI(); ai.load_model(\"models\"); print(ai.predict_skills_for_course(\"Excel Data Analysis\"))'")
    else:
        print("\n❌ Training failed. Check your data folder.")
