"""
Diagnostic script - Check your data files and show what columns are available
This does NOT show any actual data - only column names and counts
"""
import pandas as pd
import os

def diagnose_data_files(data_folder='data'):
    """Check what's in your data files without showing actual data"""
    
    print("="*70)
    print("DATA FILE DIAGNOSTIC")
    print("="*70)
    
    if not os.path.exists(data_folder):
        print(f"\n❌ Folder '{data_folder}' does not exist!")
        print(f"   Create it and put your Excel files there.")
        return
    
    excel_files = [f for f in os.listdir(data_folder) if f.endswith('.xlsx')]
    
    if not excel_files:
        print(f"\n❌ No .xlsx files found in '{data_folder}' folder")
        return
    
    print(f"\n✓ Found {len(excel_files)} Excel file(s)")
    
    for file in excel_files:
        print(f"\n{'='*70}")
        print(f"File: {file}")
        print(f"{'='*70}")
        
        try:
            df = pd.read_excel(os.path.join(data_folder, file))
            
            print(f"  Rows: {len(df)}")
            print(f"  Columns: {len(df.columns)}")
            print(f"\n  Available columns:")
            for i, col in enumerate(df.columns, 1):
                print(f"    {i}. {col}")
            
            # Check for expected columns
            print(f"\n  Checking for expected columns:")
            
            required_for_courses = ['ID Kurzu', 'Kompetence / Skill']
            found_course_cols = [col for col in required_for_courses if col in df.columns]
            
            if found_course_cols:
                print(f"    ✓ Found course columns: {found_course_cols}")
            else:
                print(f"    ❌ Missing course columns: {required_for_courses}")
                print(f"       Your file needs 'ID Kurzu' and 'Kompetence / Skill' columns")
            
            required_for_employees = ['persstat_start_month.personal_number']
            if any(col in df.columns for col in required_for_employees):
                print(f"    ✓ Found employee ID column")
            else:
                print(f"    ❌ Missing employee column: {required_for_employees}")
            
        except Exception as e:
            print(f"  ❌ Error reading file: {e}")
    
    print(f"\n{'='*70}")
    print("WHAT THE SCRIPT NEEDS:")
    print("="*70)
    print("""
For training to work, your Excel files need these columns:

FOR COURSES:
  - 'ID Kurzu' (course ID)
  - 'Kompetence / Skill' (skills the course teaches)
  - 'Název D' OR 'Content Title' (course name/title)

FOR EMPLOYEES:
  - 'persstat_start_month.personal_number' (employee ID)

If your columns have DIFFERENT names, the extraction won't work.
    """)
    
    print("SOLUTIONS:")
    print("-" * 70)
    print("1. Use text file training instead (easier):")
    print("   python train_from_text.py")
    print("")
    print("2. Rename your Excel columns to match expected names")
    print("")
    print("3. Tell me what your column names are, and I'll update the script")

if __name__ == "__main__":
    diagnose_data_files('data')
