"""
Expand training data by extracting MORE courses from Degreed
"""
import pandas as pd

# Load Degreed data
print("Loading Degreed data...")
degreed_df = pd.read_excel('data/Degreed.xlsx')

print(f"Total courses available: {degreed_df['Content ID'].nunique()}")
print(f"\nExtracting top 500 most completed courses...")

# Get top courses by completion count
course_counts = degreed_df.groupby(['Content ID', 'Content Title']).size().reset_index(name='completions')
top_courses = course_counts.nlargest(500, 'completions')

print(f"✓ Extracted {len(top_courses)} courses")
print("\nSave to: expanded_training_courses.xlsx")
top_courses.to_excel('expanded_training_courses.xlsx', index=False)

print("\n🎯 Next steps:")
print("1. Open expanded_training_courses.xlsx")
print("2. Add a 'skill_name' column")
print("3. Label each course with 1-3 skills")
print("4. Save and use for retraining")
