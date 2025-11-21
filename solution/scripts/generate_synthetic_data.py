import pandas as pd
import random
from datetime import datetime, timedelta
from faker import Faker
import uuid
import os

# Initialize Faker with English locale
fake = Faker('en_US')

# Set random seed for reproducibility
Faker.seed(42)
random.seed(42)

# Generate synthetic data for each table

def generate_interdfiace_data(num_records=100):
    """Generate data for Interdfiace.com.cz table - main educational path tracking"""
    data = []
    start_years = ['2023', '2024', '2025']
    
    for i in range(num_records):
        personal_number = f"PN-{str(i+1).zfill(6)}"
        start_year = random.choice(start_years)
        
        record = {
            "personal_number": personal_number,  # Unique personal identifier
            "personal_start_month(2023,2024,2025)": start_year,  # Educational start year
            "personal_start_month.profession_id": f"PROF-{random.randint(100, 999)}",  # Current profession code
            "personal_start_month.planned_profession_id": f"PL-PROF-{random.randint(100, 999)}",  # Target profession code
            "personal_start_month.planned_position_id": f"POS-{random.choice(['MANAGER', 'ENGINEER', 'ANALYST', 'CONSULTANT', 'SPECIALIST'])}-{random.randint(10, 99)}",  # Target position code
            "personal_start_month.basic_branch_education_group_id": f"GRP-{random.choice(['TECH', 'BUS', 'MED', 'LAW', 'SCI'])}",  # Education branch group
            "personal_start_month.basic_branch_education_category_id": f"CAT-{random.choice(['UNDERGRAD', 'GRAD', 'DOCTORAL', 'CERTIFICATION'])}",  # Education category
            "personal_start_month.field_of_study_id": f"FIELD-{random.randint(1000, 9999)}",  # Field of study ID
            "personal_start_month.field_of_study_name": random.choice([  # Field of study name in English
                "Computer Science", "Business Administration", "Electrical Engineering", 
                "Data Analytics", "Project Management", "Cybersecurity", "Artificial Intelligence",
                "Finance", "Marketing", "Human Resources"
            ]),
            "personal_start_month.field_of_study_code_laps": f"CODE-{random.randint(100, 999)}-{random.choice(['A', 'B', 'C', 'D'])}",  # Study code with LAPS classification
            "data_pocet_a_kvalifikace_od_2013_do_srpen_2025": f"Historical qualification data from 2013 to August 2025 for person {personal_number}",  # Historical data description
            "data_metod_aktualizace_do_roku_2025": "Automated data synchronization with HR systems"  # Update methodology
        }
        data.append(record)
    
    return pd.DataFrame(data)

def generate_doklad_kvalifikace_kandydat_data(interdfiace_df, num_records=150):
    """Generate data for Doklad_kvalifikace_Kandydat table - candidate qualification documents"""
    data = []
    qualification_codes = [
        "CERT-CS-001", "CERT-PM-002", "CERT-DS-003", "CERT-AI-004", "CERT-SEC-005",
        "CERT-FIN-006", "CERT-MKT-007", "CERT-HR-008", "CERT-ENG-009", "CERT-LAW-010"
    ]
    
    personal_numbers = interdfiace_df["personal_number"].tolist()
    
    for i in range(num_records):
        osobni_cislo = random.choice(personal_numbers)
        record = {
            "ID_objektu_(PK)": i + 1,  # Unique object ID
            "Osobni_cislo": osobni_cislo,  # Personal number (Czech: Osobni_cislo)
            "Kod_kvalifikace": random.choice(qualification_codes),  # Qualification code
            "Datum_ziskani": fake.date_between(start_date='-5y', end_date='today'),  # Date obtained (Czech: Datum_ziskani)
            "personel_number": osobni_cislo  # Personnel number (redundant for system compatibility)
        }
        data.append(record)
    
    return pd.DataFrame(data)

def generate_doklad_kvalifikace_komplet_data(interdfiace_df, num_records=200):
    """Generate data for Doklad_kvalifikace_Komplet table - complete qualification records"""
    data = []
    qualification_codes = [
        "COMP-CS-101", "COMP-PM-202", "COMP-DS-303", "COMP-AI-404", "COMP-SEC-505",
        "COMP-FIN-606", "COMP-MKT-707", "COMP-HR-808", "COMP-ENG-909", "COMP-LAW-010"
    ]
    
    personal_numbers = interdfiace_df["personal_number"].tolist()
    
    for i in range(num_records):
        osobni_cislo = random.choice(personal_numbers)
        start_date = fake.date_between(start_date='-7y', end_date='-1y')
        
        record = {
            "ID_objektu_(PK)": i + 1,  # Unique object ID
            "Osobni_cislo": osobni_cislo,  # Personal number
            "Kod_kvalifikace": random.choice(qualification_codes),  # Qualification code
            "Datum_ziskani": start_date,  # Start date of qualification
            "Datum_ukonceni": fake.date_between(start_date=start_date, end_date='today'),  # End date of qualification (Czech: Datum_ukonceni)
            "personel_number": osobni_cislo  # Personnel number
        }
        data.append(record)
    
    return pd.DataFrame(data)

def generate_skill_mapping_data(num_records=50):
    """Generate data for Skill_mapping/mapping table - core skills competency mapping"""
    data = []
    skill_themes = [
        "Technical", "Business", "Communication", "Leadership", "Analytical",
        "Creative", "Project Management", "Data Science", "Security", "Cloud Computing"
    ]
    
    expertise_levels = ["Beginner", "Intermediate", "Advanced", "Expert", "Master"]
    
    for i in range(num_records):
        skill_name = fake.job()
        record = {
            "ID_Skillu": i + 1,  # Unique skill ID
            "Dovednost": skill_name,  # Skill name (English content, Czech field name)
            "Název": f"{skill_name} Certification",  # Official skill name (Czech: Název)
            "Téma": random.choice(skill_themes),  # Skill theme/category (Czech: Téma)
            "Odbornost": random.choice(expertise_levels),  # Expertise level (Czech: Odbornost)
            "Počet_denum": random.randint(1, 100),  # Count of days/occurrences (Czech: Počet_denum)
            "koncové_datum": fake.date_between(start_date='today', end_date='+2y'),  # End date (Czech: koncové_datum)
            "SKILL_v_RCE": f"RCE-{random.randint(1000, 9999)}-{skill_name[:3].upper()}"  # RCE system reference ID
        }
        data.append(record)
    
    return pd.DataFrame(data)

def generate_testovani_pisemne_dovednosti_data(skill_mapping_df, num_records=75):
    """Generate data for Testování_písemné_&_Dovednosti table - written and skills assessments"""
    data = []
    
    for i in range(num_records):
        record = {
            "ID_objektu_(ID_Dovednost)": i + 1,  # Unique object ID linked to skill
            "Počet_datum": fake.date_between(start_date='-3y', end_date='today'),  # Test date (Czech: Počet_datum)
            "Koncové_datum": fake.date_between(start_date='-2y', end_date='+1y'),  # End date (Czech: Koncové_datum)
            "Variabilní_pole_ID": f"VAR-{uuid.uuid4().hex[:8].upper()}",  # Variable field ID (Czech: Variabilní_pole_ID)
            "photonote": f"Assessment completed successfully. Score: {random.randint(75, 100)}/100. " + fake.text(max_nb_chars=100)  # Assessment notes with photo reference
        }
        data.append(record)
    
    return pd.DataFrame(data)

def generate_test_skupina_data(num_records=30):
    """Generate data for Test_skupina table - test groups/assessment categories"""
    data = []
    
    for i in range(num_records):
        record = {
            "ID_skupiny_(ID_Dovednost)": i + 1,  # Unique group ID
            "Počet_datum": fake.date_between(start_date='-3y', end_date='today'),  # Group test date
            "Koncové_datum": fake.date_between(start_date='-2y', end_date='+1y'),  # Group end date
            "Variabilní_pole_ID": f"VAR-{uuid.uuid4().hex[:8].upper()}",  # Variable field ID
            "Var_pole_uložit.dat": fake.text(max_nb_chars=150)  # Variable field save data
        }
        data.append(record)
    
    return pd.DataFrame(data)

def generate_test_predmetu_data(num_records=45):
    """Generate data for Test_předmětu table - individual test subjects"""
    data = []
    
    for i in range(num_records):
        record = {
            "ID_předmětu_(ID_Dovednost)": i + 1,  # Unique subject ID
            "Počet_datum": fake.date_between(start_date='-3y', end_date='today'),  # Subject test date
            "Koncové_datum": fake.date_between(start_date='-2y', end_date='+1y'),  # Subject end date
            "Variabilní_pole_ID": f"VAR-{uuid.uuid4().hex[:8].upper()}",  # Variable field ID
            "Var_pole_uložit.dat": fake.text(max_nb_chars=150)  # Variable field save data
        }
        data.append(record)
    
    return pd.DataFrame(data)

def generate_degreed_data_data(interdfiace_df, num_records=200):
    """Generate data for Degreed.data table - learning platform integration"""
    data = []
    completion_statuses = ["Completed", "In Progress", "Not Started", "Failed"]
    
    personal_numbers = interdfiace_df["personal_number"].tolist()
    
    for i in range(num_records):
        employee_id = random.choice(personal_numbers)
        completion_status = random.choice(completion_statuses)
        
        record = {
            "ID": i + 1,  # Unique learning record ID
            "Completed_Date": fake.date_between(start_date='-2y', end_date='today') if completion_status == "Completed" else None,  # Completion date
            "Employee_ID": employee_id,  # Employee identifier
            "Content_ID": f"CONT-{random.randint(10000, 99999)}",  # Content identifier
            "Content_Title": fake.catch_phrase(),  # Content title in English
            "Completion_Status": completion_status,  # Learning status
            "URL": fake.url(),  # Content URL
            "Estimated_Learning_Minutes": random.randint(15, 360)  # Estimated completion time
        }
        data.append(record)
    
    return pd.DataFrame(data)

def generate_degreed_content_catalog_data(num_records=100):
    """Generate data for Degreed_Content_Catalog.data table - learning content catalog"""
    data = []
    content_types = ["Course", "Video", "Article", "Podcast", "Workshop", "Webinar", "Tutorial"]
    providers = [
        "Coursera", "edX", "Udemy", "LinkedIn Learning", "Pluralsight", 
        "Skillsoft", "HarvardX", "MIT OpenCourseWare", "Google", "Microsoft"
    ]
    
    for i in range(num_records):
        content_id = f"CONT-{random.randint(10000, 99999)}"
        record = {
            "Content_ID": content_id,  # Unique content ID
            "Title": fake.catch_phrase(),  # Content title
            "Type": random.choice(content_types),  # Content type
            "Internal/External_Content": random.choice(["Internal", "External"]),  # Content source
            "URL": fake.url(),  # Content URL
            "Provider": random.choice(providers),  # Content provider
            "Estimated_Learning_Minutes": random.randint(15, 480)  # Estimated learning time
        }
        data.append(record)
    
    return pd.DataFrame(data)

def generate_degreed_skill_listing_data(skill_mapping_df, num_records=75):
    """Generate data for Degreed_skill_listing table - skills taxonomy from Degreed"""
    data = []
    sources = ["Degreed", "Internal", "External Certification", "University", "Industry Standard"]
    skill_level_groups = ["Entry Level", "Mid Level", "Senior Level", "Expert Level", "Leadership Level"]
    
    for i in range(num_records):
        skill_name = fake.job()
        record = {
            "skill": skill_name.lower().replace(" ", "_"),  # Skill identifier (snake_case)
            "Description": fake.text(max_nb_chars=200),  # Skill description
            "Name": skill_name,  # Skill display name
            "Source": random.choice(sources),  # Skill source
            "skillVersionOrg": f"v{random.randint(1, 5)}.{random.randint(0, 9)}",  # Skill version
            "Endorsed": random.choice([True, False]),  # Endorsement status
            "SkillLevelGroup": random.choice(skill_level_groups)  # Skill level classification
        }
        data.append(record)
    
    return pd.DataFrame(data)

def generate_specifikace_prisane_k_dovednosti_data(skill_mapping_df, num_records=40):
    """Generate data for Specifikace_přidané_k_Dovednosti table - skill specifications"""
    data = []
    
    for i in range(num_records):
        record = {
            "ID_objektu": i + 1,  # Unique specification ID
            "Počet_datum": fake.date_between(start_date='-2y', end_date='today'),  # Specification date
            "Koncové_datum": fake.date_between(start_date='-1y', end_date='+1y'),  # Specification end date
            "Variabilní_pole_ID": f"VAR-{uuid.uuid4().hex[:8].upper()}",  # Variable field ID
            "specifikation": f"Skill specification for {fake.job()}. Requirements: " + fake.text(max_nb_chars=200)  # Specification details
        }
        data.append(record)
    
    return pd.DataFrame(data)

def generate_doklad_kvalifikace_znamka_data(interdfiace_df, num_records=60):
    """Generate data for Doklad_kvalifikace_Znamka table - qualification grades"""
    data = []
    qualification_names = [
        "Bachelor of Science in Computer Science",
        "Master of Business Administration",
        "Project Management Professional (PMP)",
        "Certified Data Scientist",
        "AWS Certified Solutions Architect",
        "Google Cloud Professional",
        "Certified Information Security Manager",
        "Financial Analyst Certification",
        "Digital Marketing Specialist",
        "Human Resources Management Certificate"
    ]
    
    personal_numbers = interdfiace_df["personal_number"].tolist()
    
    for i in range(num_records):
        record = {
            "ID": i + 1,  # Unique grade record ID
            "personal_number": random.choice(personal_numbers),  # Personal number
            "ID_Q": f"Q-{random.randint(1000, 9999)}",  # Qualification ID
            "Název_Q": random.choice(qualification_names)  # Qualification name (English content)
        }
        data.append(record)
    
    return pd.DataFrame(data)

def save_to_csv(dataframes, output_dir="synthetic_data"):
    """Save all dataframes to CSV files with proper encoding"""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    for table_name, df in dataframes.items():
        # Clean table name for filename
        filename = table_name.replace("/", "_").replace(".", "_").replace(" ", "_") + ".csv"
        filepath = os.path.join(output_dir, filename)
        
        # Save to CSV with UTF-8 encoding
        df.to_csv(filepath, index=False, encoding='utf-8')
        print(f"Saved {table_name} to {filepath} ({len(df)} records)")

def main():
    """Main function to generate all synthetic data with relationships"""
    print("Generating synthetic data for educational qualification schema...")
    
    # Generate base data
    interdfiace_df = generate_interdfiace_data(100)
    skill_mapping_df = generate_skill_mapping_data(50)
    
    # Generate related data maintaining referential integrity
    dataframes = {
        "Interdfiace.com.cz": interdfiace_df,
        "Skill_mapping/mapping": skill_mapping_df,
        "Doklad_kvalifikace_Kandydat": generate_doklad_kvalifikace_kandydat_data(interdfiace_df, 150),
        "Doklad_kvalifikace_Komplet": generate_doklad_kvalifikace_komplet_data(interdfiace_df, 200),
        "Testování_písemné_&_Dovednosti": generate_testovani_pisemne_dovednosti_data(skill_mapping_df, 75),
        "Test_skupina": generate_test_skupina_data(30),
        "Test_předmětu": generate_test_predmetu_data(45),
        "Degreed.data": generate_degreed_data_data(interdfiace_df, 200),
        "Degreed_Content_Catalog.data": generate_degreed_content_catalog_data(100),
        "Degreed_skill_listing": generate_degreed_skill_listing_data(skill_mapping_df, 75),
        "Specifikace_přidané_k_Dovednosti": generate_specifikace_prisane_k_dovednosti_data(skill_mapping_df, 40),
        "Doklad_kvalifikace_Znamka": generate_doklad_kvalifikace_znamka_data(interdfiace_df, 60)
    }
    
    # Save all data to CSV files
    save_to_csv(dataframes)
    
    print("\nData generation complete!")
    print("Summary of generated records:")
    for table_name, df in dataframes.items():
        print(f"- {table_name}: {len(df)} records")
    print("\nFiles saved to 'synthetic_data' directory")

if __name__ == "__main__":
    # Check required packages
    try:
        import pandas as pd
        from faker import Faker
    except ImportError as e:
        print("Required packages not installed. Please install them first:")
        print("pip install pandas faker")
        print(f"Error: {e}")
        exit(1)
    
    main()

