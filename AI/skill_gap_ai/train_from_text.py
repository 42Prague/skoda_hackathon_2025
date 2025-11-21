"""
Train AI models directly from .txt files
Supports various text formats for training data
"""
import os
import json
import re
from typing import List, Dict, Tuple
from ai_training import SkillMatchingAI, ReadinessPredictionAI, AITrainingPipeline
import pandas as pd


class TextDataLoader:
    """Load training data from various text file formats"""
    
    @staticmethod
    def load_course_skills_from_text(file_path: str, format_type: str = 'auto') -> List[Dict]:
        """
        Load course-skill mappings from text file
        
        Supported formats:
        1. JSON format (.json)
        2. CSV format (.csv or .txt)
        3. Custom format (one per line): course_id|course_text|skill_name
        4. Free-form text with pattern matching
        """
        _, ext = os.path.splitext(file_path)
        
        if format_type == 'auto':
            # Auto-detect format
            if ext == '.json':
                return TextDataLoader._load_json_format(file_path)
            elif ext == '.csv':
                return TextDataLoader._load_csv_format(file_path)
            else:
                # Try to detect pattern in .txt file
                return TextDataLoader._load_text_format(file_path)
        
        elif format_type == 'json':
            return TextDataLoader._load_json_format(file_path)
        elif format_type == 'csv':
            return TextDataLoader._load_csv_format(file_path)
        elif format_type == 'pipe':
            return TextDataLoader._load_pipe_delimited(file_path)
        elif format_type == 'freeform':
            return TextDataLoader._load_freeform_text(file_path)
        else:
            raise ValueError(f"Unknown format: {format_type}")
    
    @staticmethod
    def _load_json_format(file_path: str) -> List[Dict]:
        """
        Load from JSON format:
        [
          {"course_id": "C001", "course_text": "Python Basics", "skill_name": "Python"},
          ...
        ]
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Validate format
        required_fields = ['course_id', 'course_text', 'skill_name']
        for item in data:
            if not all(field in item for field in required_fields):
                raise ValueError(f"JSON must have fields: {required_fields}")
        
        return data
    
    @staticmethod
    def _load_csv_format(file_path: str) -> List[Dict]:
        """
        Load from CSV/TSV format:
        course_id,course_text,skill_name
        C001,Python Programming Basics,Python
        C001,Python Programming Basics,Programming
        """
        # Try different delimiters
        with open(file_path, 'r', encoding='utf-8') as f:
            first_line = f.readline()
        
        # Detect delimiter
        if '\t' in first_line:
            delimiter = '\t'
        elif ',' in first_line:
            delimiter = ','
        elif ';' in first_line:
            delimiter = ';'
        else:
            delimiter = ','
        
        df = pd.read_csv(file_path, delimiter=delimiter)
        
        # Ensure required columns exist
        required_cols = ['course_id', 'course_text', 'skill_name']
        if not all(col in df.columns for col in required_cols):
            raise ValueError(f"CSV must have columns: {required_cols}\nFound: {df.columns.tolist()}")
        
        return df[required_cols].to_dict('records')
    
    @staticmethod
    def _load_pipe_delimited(file_path: str) -> List[Dict]:
        """
        Load from pipe-delimited format:
        C001|Python Programming Basics|Python
        C001|Python Programming Basics|Programming
        C002|SQL Database Management|SQL
        """
        results = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line or line.startswith('#'):  # Skip empty lines and comments
                    continue
                
                parts = line.split('|')
                if len(parts) >= 3:
                    results.append({
                        'course_id': parts[0].strip(),
                        'course_text': parts[1].strip(),
                        'skill_name': parts[2].strip()
                    })
                else:
                    print(f"  ⚠️  Skipping malformed line {line_num}: {line}")
        
        return results
    
    @staticmethod
    def _load_text_format(file_path: str) -> List[Dict]:
        """
        Auto-detect format from .txt file
        Tries multiple patterns
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Try JSON first
        try:
            data = json.loads(content)
            if isinstance(data, list):
                return data
        except:
            pass
        
        # Try pipe-delimited
        if '|' in content:
            return TextDataLoader._load_pipe_delimited(file_path)
        
        # Try comma/tab separated
        try:
            return TextDataLoader._load_csv_format(file_path)
        except:
            pass
        
        # Fall back to freeform
        return TextDataLoader._load_freeform_text(file_path)
    
    @staticmethod
    def _load_freeform_text(file_path: str) -> List[Dict]:
        """
        Load from free-form text using pattern matching
        
        Patterns recognized:
        - "Course: <name> teaches <skill>"
        - "Course <id>: <text> -> Skills: <skill1>, <skill2>"
        - "<course_name> covers: <skill1>, <skill2>"
        """
        results = []
        course_counter = 1
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Pattern 1: "Course: Python Basics teaches Python, Programming"
        pattern1 = r'Course:\s*(.+?)\s+teaches\s+(.+?)(?:\n|$)'
        for match in re.finditer(pattern1, content, re.IGNORECASE | re.MULTILINE):
            course_text = match.group(1).strip()
            skills = [s.strip() for s in match.group(2).split(',')]
            
            course_id = f"C{course_counter:04d}"
            for skill in skills:
                if skill:
                    results.append({
                        'course_id': course_id,
                        'course_text': course_text,
                        'skill_name': skill
                    })
            course_counter += 1
        
        # Pattern 2: "Python Programming -> Skills: Python, Programming, OOP"
        pattern2 = r'(.+?)\s*->\s*Skills?:\s*(.+?)(?:\n|$)'
        for match in re.finditer(pattern2, content, re.IGNORECASE | re.MULTILINE):
            course_text = match.group(1).strip()
            skills = [s.strip() for s in match.group(2).split(',')]
            
            course_id = f"C{course_counter:04d}"
            for skill in skills:
                if skill:
                    results.append({
                        'course_id': course_id,
                        'course_text': course_text,
                        'skill_name': skill
                    })
            course_counter += 1
        
        # Pattern 3: "Course_ID: course_text (Skills: skill1, skill2)"
        pattern3 = r'(\w+):\s*(.+?)\s*\(Skills?:\s*(.+?)\)'
        for match in re.finditer(pattern3, content, re.IGNORECASE):
            course_id = match.group(1).strip()
            course_text = match.group(2).strip()
            skills = [s.strip() for s in match.group(3).split(',')]
            
            for skill in skills:
                if skill:
                    results.append({
                        'course_id': course_id,
                        'course_text': course_text,
                        'skill_name': skill
                    })
        
        return results
    
    @staticmethod
    def load_employee_readiness_from_text(file_path: str, format_type: str = 'auto') -> List[Dict]:
        """
        Load employee readiness scores from text file
        
        Formats:
        1. JSON: [{"employee_id": "001", "readiness_score": 85}, ...]
        2. CSV: employee_id,readiness_score,notes
        3. Pipe: 001|85|Ready for promotion
        4. Free-form: "Employee 001 has readiness score of 85"
        """
        _, ext = os.path.splitext(file_path)
        
        if format_type == 'auto':
            if ext == '.json':
                return TextDataLoader._load_employee_json(file_path)
            elif ext == '.csv':
                return TextDataLoader._load_employee_csv(file_path)
            else:
                return TextDataLoader._load_employee_text(file_path)
        
        elif format_type == 'json':
            return TextDataLoader._load_employee_json(file_path)
        elif format_type == 'csv':
            return TextDataLoader._load_employee_csv(file_path)
        elif format_type == 'pipe':
            return TextDataLoader._load_employee_pipe(file_path)
        else:
            return TextDataLoader._load_employee_text(file_path)
    
    @staticmethod
    def _load_employee_json(file_path: str) -> List[Dict]:
        """Load employee data from JSON"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        required_fields = ['employee_id', 'readiness_score']
        for item in data:
            if not all(field in item for field in required_fields):
                raise ValueError(f"JSON must have fields: {required_fields}")
        
        return data
    
    @staticmethod
    def _load_employee_csv(file_path: str) -> List[Dict]:
        """Load employee data from CSV"""
        df = pd.read_csv(file_path)
        
        required_cols = ['employee_id', 'readiness_score']
        if not all(col in df.columns for col in required_cols):
            raise ValueError(f"CSV must have columns: {required_cols}")
        
        return df.to_dict('records')
    
    @staticmethod
    def _load_employee_pipe(file_path: str) -> List[Dict]:
        """Load from pipe-delimited: employee_id|score|notes"""
        results = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                parts = line.split('|')
                if len(parts) >= 2:
                    results.append({
                        'employee_id': parts[0].strip(),
                        'readiness_score': float(parts[1].strip()),
                        'notes': parts[2].strip() if len(parts) > 2 else ''
                    })
        
        return results
    
    @staticmethod
    def _load_employee_text(file_path: str) -> List[Dict]:
        """Load from free-form text using pattern matching"""
        results = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Pattern: "Employee <id> has readiness score of <score>"
        pattern = r'Employee\s+(\w+)\s+.*?(?:readiness|score).*?(\d+(?:\.\d+)?)'
        for match in re.finditer(pattern, content, re.IGNORECASE):
            results.append({
                'employee_id': match.group(1).strip(),
                'readiness_score': float(match.group(2))
            })
        
        return results


def train_from_text_files(course_skills_file: str, employee_readiness_file: str = None):
    """
    Train AI models directly from text files
    
    Args:
        course_skills_file: Path to file with course-skill mappings
        employee_readiness_file: Optional path to file with employee scores
    """
    print("="*70)
    print("TRAINING AI FROM TEXT FILES")
    print("="*70)
    
    # Load course-skill data
    print(f"\n📄 Loading course-skill data from: {course_skills_file}")
    try:
        course_skills_data = TextDataLoader.load_course_skills_from_text(course_skills_file)
        print(f"  ✓ Loaded {len(course_skills_data)} course-skill mappings")
        
        # Show sample
        if course_skills_data:
            print(f"\n  Sample data:")
            for item in course_skills_data[:3]:
                print(f"    {item['course_id']}: {item['course_text']} -> {item['skill_name']}")
    except Exception as e:
        print(f"  ❌ Error loading course-skill data: {e}")
        print(f"\n  💡 Tip: Check the format examples below")
        show_format_examples()
        return False
    
    # Check if we have enough data
    if len(course_skills_data) < 10:
        print(f"\n  ⚠️  Warning: Only {len(course_skills_data)} examples found.")
        print(f"      Need at least 10 for training. Add more data!")
        return False
    
    # Train Skill Matching AI
    print("\n" + "-"*70)
    print("Training Skill Matching AI")
    print("-"*70)
    
    skill_ai = SkillMatchingAI()
    
    # Prepare data
    X_texts = [item['course_text'] for item in course_skills_data]
    y_labels = [item['skill_name'] for item in course_skills_data]
    
    # Vectorize
    from sklearn.preprocessing import LabelEncoder
    X = skill_ai.vectorizer.fit_transform(X_texts)
    skill_ai.skill_encoder = LabelEncoder()
    y = skill_ai.skill_encoder.fit_transform(y_labels)
    
    # Train
    results = skill_ai.train(X, y)
    
    # Save model
    os.makedirs('models', exist_ok=True)
    skill_ai.save_model('models')
    
    print("\n✅ Skill Matching AI trained and saved successfully!")
    
    # Test the model
    print("\n🧪 Testing trained model...")
    test_text = "Advanced Python Programming with Data Science"
    predictions = skill_ai.predict_skills_for_course(test_text, top_k=3)
    print(f"\n  Input: '{test_text}'")
    print(f"  Predicted skills:")
    for skill, confidence in predictions:
        print(f"    • {skill}: {confidence:.1%} confidence")
    
    # Train employee readiness if data provided
    if employee_readiness_file and os.path.exists(employee_readiness_file):
        print("\n" + "-"*70)
        print("Training Readiness Prediction AI")
        print("-"*70)
        print(f"📄 Loading employee readiness data from: {employee_readiness_file}")
        
        try:
            employee_data = TextDataLoader.load_employee_readiness_from_text(employee_readiness_file)
            print(f"  ✓ Loaded {len(employee_data)} employee records")
            
            if len(employee_data) >= 10:
                # Note: Full training requires Employee objects with features
                print("  ℹ️  Employee readiness training requires full employee data")
                print("      Use main.py for complete readiness prediction training")
            else:
                print(f"  ⚠️  Only {len(employee_data)} employees. Need at least 10.")
        except Exception as e:
            print(f"  ⚠️  Could not load employee data: {e}")
    
    print("\n" + "="*70)
    print("TRAINING COMPLETE!")
    print("="*70)
    print("\n✅ Models saved to: models/")
    print("🚀 You can now use the trained AI in your main system")
    
    return True


def show_format_examples():
    """Show examples of supported text formats"""
    print("\n" + "="*70)
    print("SUPPORTED TEXT FILE FORMATS")
    print("="*70)
    
    print("\n1️⃣  JSON FORMAT (.json):")
    print("-" * 40)
    print("""[
  {
    "course_id": "C001",
    "course_text": "Python Programming Basics",
    "skill_name": "Python"
  },
  {
    "course_id": "C001",
    "course_text": "Python Programming Basics",
    "skill_name": "Programming"
  }
]""")
    
    print("\n2️⃣  CSV FORMAT (.csv or .txt):")
    print("-" * 40)
    print("""course_id,course_text,skill_name
C001,Python Programming Basics,Python
C001,Python Programming Basics,Programming
C002,SQL Database Management,SQL""")
    
    print("\n3️⃣  PIPE-DELIMITED (.txt):")
    print("-" * 40)
    print("""C001|Python Programming Basics|Python
C001|Python Programming Basics|Programming
C002|SQL Database Management|SQL""")
    
    print("\n4️⃣  FREE-FORM TEXT (.txt):")
    print("-" * 40)
    print("""Course: Python Programming Basics teaches Python, Programming
Course: SQL Database Management teaches SQL, Database Design
Python for Data Science -> Skills: Python, Data Analysis, Statistics""")
    
    print("\n5️⃣  EMPLOYEE READINESS - JSON:")
    print("-" * 40)
    print("""[
  {"employee_id": "0001689", "readiness_score": 85.0},
  {"employee_id": "0001690", "readiness_score": 72.5}
]""")
    
    print("\n6️⃣  EMPLOYEE READINESS - CSV:")
    print("-" * 40)
    print("""employee_id,readiness_score,notes
0001689,85.0,Ready for promotion
0001690,72.5,Needs more training""")
    
    print("\n" + "="*70)


def create_text_templates():
    """Create sample text files in different formats"""
    print("📝 Creating text file templates...")
    
    # JSON format
    json_data = [
        {"course_id": "C001", "course_text": "Python Programming Fundamentals", "skill_name": "Python"},
        {"course_id": "C001", "course_text": "Python Programming Fundamentals", "skill_name": "Programming"},
        {"course_id": "C002", "course_text": "SQL Database Management", "skill_name": "SQL"},
        {"course_id": "C003", "course_text": "Leadership Skills for Managers", "skill_name": "Leadership"},
    ]
    
    with open('training_courses_skills.json', 'w') as f:
        json.dump(json_data, f, indent=2)
    print("  ✓ Created: training_courses_skills.json")
    
    # Pipe-delimited format
    with open('training_courses_skills.txt', 'w') as f:
        f.write("# Course-Skill Training Data\n")
        f.write("# Format: course_id|course_text|skill_name\n\n")
        f.write("C001|Python Programming Fundamentals|Python\n")
        f.write("C001|Python Programming Fundamentals|Programming\n")
        f.write("C002|SQL Database Management|SQL\n")
        f.write("C003|Leadership Skills for Managers|Leadership\n")
        f.write("C004|Project Management Professional|Project Management\n")
    print("  ✓ Created: training_courses_skills.txt")
    
    # Employee readiness
    with open('training_employee_readiness.txt', 'w') as f:
        f.write("# Employee Readiness Scores\n")
        f.write("# Format: employee_id|readiness_score|notes\n\n")
        f.write("0001689|85.0|Ready for senior role\n")
        f.write("0001690|72.5|Needs more leadership training\n")
        f.write("0001691|90.0|Excellent candidate\n")
        f.write("0001692|45.0|Significant skill gaps\n")
    print("  ✓ Created: training_employee_readiness.txt")
    
    print("\n✅ Template files created! Fill them with your actual data.")


def main():
    """Main function for text-based training"""
    print("="*70)
    print("TRAIN AI FROM TEXT FILES")
    print("="*70)
    
    print("\nOptions:")
    print("1. Create text file templates")
    print("2. Train from existing text files")
    print("3. Show format examples")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == '1':
        create_text_templates()
        print("\n💡 Edit the template files with your data, then run option 2")
        
    elif choice == '2':
        course_file = input("\nEnter course-skills file path: ").strip()
        employee_file = input("Enter employee readiness file (optional, press Enter to skip): ").strip()
        
        if not os.path.exists(course_file):
            print(f"❌ File not found: {course_file}")
            return
        
        train_from_text_files(
            course_file,
            employee_file if employee_file else None
        )
        
    elif choice == '3':
        show_format_examples()
    
    else:
        print("Invalid choice")


if __name__ == "__main__":
    main()
