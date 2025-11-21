import pandas as pd
import numpy as np
import ast  # built-in

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
import umap.umap_ as umap

# --------------------------------------------------
# 1. File paths – adjust to your actual filenames
# --------------------------------------------------

degreed_path = "../data/Degreed.xlsx"
sap_courses_path = "../data/ZHRPD_VZD_STA_007.xlsx"
sap_quals_path = "../data/ZHRPD_VZD_STA_016_RE_RHRHAZ00.xlsx"
skill_map_path = "../data/skill_mapping_with_predicted_skills.csv"

# --------------------------------------------------
# 2. Load input data
# --------------------------------------------------

print("Loading files...")

degreed_df = pd.read_excel(degreed_path)
sap_courses_df = pd.read_excel(sap_courses_path)
sap_quals_df = pd.read_excel(sap_quals_path)
skill_map_df = pd.read_csv(skill_map_path)

print("Degreed columns:", degreed_df.columns.tolist())
print("SAP courses columns:", sap_courses_df.columns.tolist())
print("SAP qualifications columns:", sap_quals_df.columns.tolist())
print("Skill mapping columns:", skill_map_df.columns.tolist())

# --------------------------------------------------
# 3. Clean and aggregate skill mapping
# --------------------------------------------------

def safe_parse_list_from_string(x):
    """
    For the raw CSV column predicted_skills which is stored as a string
    representation of a list, parse it to a Python list.
    """
    if isinstance(x, list):
        return x
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return []
    try:
        return ast.literal_eval(str(x))
    except Exception:
        return []

# Parse raw predicted_skills from CSV (string -> list)
skill_map_df["predicted_skills"] = skill_map_df["predicted_skills"].apply(safe_parse_list_from_string)

# Aggregate by course ID (ID Kurzu)
skill_map_agg = (
    skill_map_df
    .groupby("ID Kurzu")["predicted_skills"]
    .apply(lambda lists: sorted(set(s for lst in lists for s in lst if isinstance(s, str) and s.strip())))
    .reset_index()
)

# Normalize ID types
skill_map_agg["ID Kurzu"] = skill_map_agg["ID Kurzu"].astype(str)

print("Aggregated skill mapping shape:", skill_map_agg.shape)
print("Sample aggregated skill mapping:")
print(skill_map_agg.head())

# --------------------------------------------------
# 4. SAP courses (ZHRPD_VZD_STA_007) → employee × course × skills
# --------------------------------------------------

# Columns:
# "Typ akce", "Označení typu akce", "IDOBJ", "Datum zahájení", "Datum ukončení", "ID účastníka"

sap_courses_df = sap_courses_df.rename(columns={
    "Typ akce": "Course_ID",
    "ID účastníka": "Employee_ID_SAP"
})

sap_courses_df["Course_ID"] = sap_courses_df["Course_ID"].astype(str)

sap_courses_skills = sap_courses_df.merge(
    skill_map_agg,
    left_on="Course_ID",
    right_on="ID Kurzu",
    how="left"
)

# --------------------------------------------------
# 5. SAP qualifications (ZHRPD_VZD_STA_016_RE_RHRHAZ00) → employee × qual × skills
# --------------------------------------------------

# Columns:
# "ID P", "Počát.datum", "Koncové datum", "ID Q", "Název Q"

sap_quals_df = sap_quals_df.rename(columns={
    "ID P": "Employee_ID_SAP",
    "ID Q": "Qual_ID"
})

sap_quals_df["Qual_ID"] = sap_quals_df["Qual_ID"].astype(str)

# Assume Qual_ID also maps to ID Kurzu in skill_map_agg
sap_quals_skills = sap_quals_df.merge(
    skill_map_agg,
    left_on="Qual_ID",
    right_on="ID Kurzu",
    how="left"
)

# --------------------------------------------------
# 6. Build unified employee-skill rows from SAP (courses + qualifications)
# --------------------------------------------------

emp_skill_rows = []

# From courses
for _, row in sap_courses_skills.iterrows():
    emp_id = row["Employee_ID_SAP"]
    skills = row.get("predicted_skills", [])
    if not isinstance(skills, (list, tuple)):
        skills = []
    for s in skills:
        if isinstance(s, str) and s.strip():
            emp_skill_rows.append({
                "employee_id": str(emp_id),
                "skill": s.strip().lower(),
                "source": "sap_course"
            })

# From qualifications
for _, row in sap_quals_skills.iterrows():
    emp_id = row["Employee_ID_SAP"]
    skills = row.get("predicted_skills", [])
    if not isinstance(skills, (list, tuple)):
        skills = []
    for s in skills:
        if isinstance(s, str) and s.strip():
            emp_skill_rows.append({
                "employee_id": str(emp_id),
                "skill": s.strip().lower(),
                "source": "sap_qualification"
            })

emp_skills_df = pd.DataFrame(emp_skill_rows)
print("Raw employee-skill rows (SAP only):", emp_skills_df.shape)

# Drop duplicates (same employee, same skill, same source)
emp_skills_df = emp_skills_df.drop_duplicates()
print("Unique employee-skill rows:", emp_skills_df.shape)

if emp_skills_df.empty:
    raise ValueError("No employee skills found from SAP courses/qualifications. Check mappings.")

# --------------------------------------------------
# 7. (Optional) Degreed structure (not yet mapped to skills)
# --------------------------------------------------

degreed_df = degreed_df.rename(columns={
    "Employee ID": "Employee_ID_DEG",
    "Content ID": "Degreed_Content_ID"
})

# TODO for later: map Degreed_Content_ID or Content Title to skills using NLP,
# then append to emp_skills_df with source="degreed".

# --------------------------------------------------
# 8. Build per-employee "skill sentence" and TF-IDF matrix
# --------------------------------------------------

emp_skill_sentences = (
    emp_skills_df
    .groupby("employee_id")["skill"]
    .apply(lambda skills: " ".join(sorted(set(skills))))
    .reset_index()
)

print("Employees with at least one skill:", emp_skill_sentences.shape[0])

# TF-IDF over skills
vectorizer = TfidfVectorizer(
    tokenizer=lambda x: x.split(),
    token_pattern=None,
    lowercase=False
)

skill_matrix = vectorizer.fit_transform(emp_skill_sentences["skill"])
skill_feature_names = vectorizer.get_feature_names_out()

print("Skill matrix shape (employees x skills):", skill_matrix.shape)

# --------------------------------------------------
# 9. Dimensionality reduction with UMAP (2D)
# --------------------------------------------------

print("Running UMAP...")
reducer = umap.UMAP(
    n_components=2,
    random_state=42,
    n_neighbors=15,
    min_dist=0.1,
    metric="cosine"
)

embedding_2d = reducer.fit_transform(skill_matrix)
print("UMAP embedding shape:", embedding_2d.shape)

# --------------------------------------------------
# 10. Clustering with K-Means
# --------------------------------------------------

print("Running K-Means clustering...")
K = 10  # tune this if needed
kmeans = KMeans(n_clusters=K, random_state=42, n_init="auto")
cluster_labels_kmeans = kmeans.fit_predict(skill_matrix)

# --------------------------------------------------
# 11. Build final employee profile table
# --------------------------------------------------

result_df = emp_skill_sentences.copy()
result_df["x"] = embedding_2d[:, 0]
result_df["y"] = embedding_2d[:, 1]
result_df["cluster_kmeans"] = cluster_labels_kmeans

# Top TF-IDF skills per employee
def top_skills_for_employee(row_index, top_n=10):
    row_vec = skill_matrix[row_index]
    arr = row_vec.toarray().ravel()
    top_idx = arr.argsort()[::-1][:top_n]
    skills = [(skill_feature_names[i], float(arr[i])) for i in top_idx if arr[i] > 0]
    return skills

top_skills_list = []
for i in range(result_df.shape[0]):
    top_skills_list.append(top_skills_for_employee(i, top_n=10))

result_df["top_skills_tfidf"] = top_skills_list

print("Final employee skill positioning (head):")
print(result_df.head())

output_file = "employee_skill_positions.csv"
result_df.to_csv(output_file, index=False)
print(f"Employee skill positions saved to {output_file}")
