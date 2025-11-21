"""
Auto-generate skill labels from course titles using keyword matching
This helps create training data when skills aren't pre-labeled
"""
import pandas as pd
import re

def auto_label_skills_from_titles(input_file='my_training_data.xlsx', output_file='my_training_data_labeled.xlsx'):
    """
    Auto-generate skill labels from course titles using keyword patterns
    """
    print("="*70)
    print("AUTO-LABELING SKILLS FROM COURSE TITLES")
    print("="*70)
    
    # Load data
    df = pd.read_excel(input_file, sheet_name='course_skills')
    print(f"\n✓ Loaded {len(df)} course mappings")
    
    # Define skill patterns (keywords that indicate specific skills)
    skill_patterns = {
        'Excel': ['excel', 'tabulk', 'spreadsheet', 'kontingenční'],
        'PowerPoint': ['powerpoint', 'ppt', 'prezentace', 'presentation'],
        'Word': ['word', 'dokument', 'document'],
        'Microsoft 365': ['microsoft 365', 'm365', 'office 365', 'ekosystém microsoft'],
        'Cloud': ['cloud', 'soubory v cloudu', 'onedrive', 'sharepoint'],
        'Email': ['email', 'outlook', 'zero inbox', 'e-mail'],
        'Data Analysis': ['data', 'analýz', 'analytics', 'práce s daty'],
        'Project Management': ['projekt', 'jira', 'agile', 'scrum'],
        'AI': ['ai', 'artificial intelligence', 'umělá inteligence'],
        'Communication': ['komunikace', 'communication', 'prezentace'],
        'Leadership': ['leadership', 'vedení', 'management', 'lídr'],
        'Programming': ['python', 'java', 'kód', 'programming', 'develop'],
        'SQL': ['sql', 'databáz', 'database'],
        'Design': ['design', 'canva', 'photoshop', 'graphics'],
        'Collaboration': ['teams', 'collaboration', 'spoluprác'],
        'Security': ['security', 'zabezpečení', 'kybernetick'],
        'Soft Skills': ['soft skill', 'etika', 'etiquette', 'codex', 'decorum'],
    }
    
    labeled_rows = []
    
    print("\n🔍 Analyzing course titles...")
    
    for _, row in df.iterrows():
        course_id = row['course_id']
        course_text = str(row['course_text']).lower()
        
        # Find matching skills
        matched_skills = []
        
        for skill, keywords in skill_patterns.items():
            for keyword in keywords:
                if keyword.lower() in course_text:
                    matched_skills.append(skill)
                    break
        
        # If no match, assign a generic skill
        if not matched_skills:
            # Try to extract meaningful words
            if any(word in course_text for word in ['kurz', 'školení', 'training']):
                matched_skills = ['General Training']
            else:
                matched_skills = ['Professional Development']
        
        # Create a row for each matched skill
        for skill in matched_skills:
            labeled_rows.append({
                'course_id': course_id,
                'course_text': row['course_text'],
                'skill_name': skill
            })
    
    # Create new dataframe
    labeled_df = pd.DataFrame(labeled_rows)
    
    print(f"  ✓ Generated {len(labeled_df)} course-skill mappings")
    print(f"  ✓ From {labeled_df['course_id'].nunique()} unique courses")
    print(f"  ✓ Covering {labeled_df['skill_name'].nunique()} different skills")
    
    print(f"\n📊 Skills distribution:")
    skill_counts = labeled_df['skill_name'].value_counts()
    for skill, count in skill_counts.head(15).items():
        print(f"  {skill}: {count} courses")
    
    # Load employee data
    emp_df = pd.read_excel(input_file, sheet_name='employee_readiness')
    
    # Save to new file
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        labeled_df.to_excel(writer, sheet_name='course_skills', index=False)
        emp_df.to_excel(writer, sheet_name='employee_readiness', index=False)
    
    print(f"\n✅ Auto-labeled data saved to: {output_file}")
    print(f"\n🚀 Ready to train! Run:")
    print(f"   python train_ai.py")
    print(f"   Choose option 3")
    print(f"   Enter: {output_file}")
    
    return output_file


if __name__ == "__main__":
    auto_label_skills_from_titles()
