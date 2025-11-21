import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# --------------------------------------------------
# 1. Load data (robust to encoding and Excel/CSV)
# --------------------------------------------------

# Adjust these to your actual file names and extensions
deg_path = "degree_content_catalog.xlsx"   # or "degree_content_catalog.xlsx"
skill_map_path = "skill_mapping.xlsx"      # or "skill_mapping.xlsx"

def safe_read_table(path):
    """
    Try to read Excel if .xlsx, otherwise read CSV with common encodings.
    """
    if path.lower().endswith(".xlsx") or path.lower().endswith(".xls"):
        return pd.read_excel(path)
    else:
        # CSV: try utf-8, then latin-1
        try:
            return pd.read_csv(path, encoding="utf-8")
        except UnicodeDecodeError:
            print(f"Warning: UTF-8 decode failed for {path}, trying latin-1...")
            return pd.read_csv(path, encoding="latin-1")

degrees_df = safe_read_table(deg_path)
skill_mapping_df = safe_read_table(skill_map_path)

print("degree_content_catalog columns:", degrees_df.columns.tolist())
print("skill_mapping columns:", skill_mapping_df.columns.tolist())

# --------------------------------------------------
# 2. Extract and clean skills from degree_content_catalog (Category 1–15)
# --------------------------------------------------

# Column names from your sample: "Category 1", "Category 2", ... "Category 15"
category_cols = [c for c in degrees_df.columns if c.strip().lower().startswith("category")]

if not category_cols:
    raise ValueError("No 'Category' columns found in degree_content_catalog. Check column names.")

# Melt into long format: one row = one (Content ID, skill) pair
skills_long = degrees_df.melt(
    id_vars=["Content ID", "Title", "Summary"],  # from your sample
    value_vars=category_cols,
    var_name="category_slot",
    value_name="skill"
)

skills_long["skill"] = skills_long["skill"].astype(str).str.strip()
skills_long = skills_long[
    skills_long["skill"].notna()
    & (skills_long["skill"] != "")
    & (skills_long["skill"].str.lower() != "nan")
]

skills_long["skill_norm"] = skills_long["skill"].str.lower()
unique_skills = sorted(skills_long["skill_norm"].unique())

skills_df = pd.DataFrame({
    "skill_name_norm": unique_skills
})
skills_df["skill_display"] = skills_df["skill_name_norm"].str.title()

print("Number of unique skills (from Category 1–15):", len(skills_df))

# --------------------------------------------------
# 3. Build text representation for each degree
# --------------------------------------------------

degrees_df["Title"] = degrees_df["Title"].fillna("").astype(str)
degrees_df["Summary"] = degrees_df["Summary"].fillna("").astype(str)
degrees_df["course_text"] = degrees_df["Title"].str.strip() + ". " + degrees_df["Summary"].str.strip()

# --------------------------------------------------
# 4. Load embedding model and compute embeddings
# --------------------------------------------------

print("Loading embedding model...")
model = SentenceTransformer("all-MiniLM-L6-v2")

print("Encoding skills...")
skill_texts = skills_df["skill_name_norm"].tolist()
skill_embeddings = model.encode(skill_texts, show_progress_bar=True)
skills_df["embedding"] = list(skill_embeddings)

print("Encoding degree contents...")
degree_texts = degrees_df["course_text"].tolist()
degree_embeddings = model.encode(degree_texts, show_progress_bar=True)
degrees_df["embedding"] = list(degree_embeddings)

skill_emb_matrix = np.vstack(skills_df["embedding"].values)

# --------------------------------------------------
# 5. Suggest skills for arbitrary text
# --------------------------------------------------

def suggest_skills_for_text(text, top_n=5):
    if not isinstance(text, str) or text.strip() == "":
        return []
    text_emb = model.encode([text])[0]
    sims = cosine_similarity(text_emb.reshape(1, -1), skill_emb_matrix)[0]
    top_idx = sims.argsort()[::-1][:top_n]
    results = []
    for idx in top_idx:
        skill_name = skills_df.iloc[idx]["skill_name_norm"]
        score = float(sims[idx])
        results.append((skill_name, score))
    return results

# Sanity check
if len(degrees_df) > 0:
    example_row = degrees_df.iloc[0]
    print("\nExample from degree_content_catalog:")
    print("Title:", example_row["Title"])
    print("Summary:", example_row["Summary"])
    print("Existing categories:", [example_row[c] for c in category_cols if pd.notna(example_row[c])])

    example_suggestions = suggest_skills_for_text(example_row["course_text"], top_n=10)
    print("\nModel suggested skills for this course:")
    for s, sc in example_suggestions:
        print(f"  {s} ({sc:.3f})")

# --------------------------------------------------
# 6. Use the model for skill_mapping (the puzzle)
# --------------------------------------------------

# Build text from "Název D" + "Téma"
if "Název D" not in skill_mapping_df.columns or "Téma" not in skill_mapping_df.columns:
    raise ValueError("Skill mapping file must contain columns 'Název D' and 'Téma'.")

skill_mapping_df["Název D"] = skill_mapping_df["Název D"].fillna("").astype(str)
skill_mapping_df["Téma"] = skill_mapping_df["Téma"].fillna("").astype(str)
skill_mapping_df["course_text"] = skill_mapping_df["Název D"].str.strip() + ". " + skill_mapping_df["Téma"].str.strip()

def suggest_skills_for_skill_mapping_row(row, top_n=5, min_score=None):
    text = row["course_text"]
    suggestions = suggest_skills_for_text(text, top_n=top_n)
    if min_score is not None:
        suggestions = [(s, sc) for s, sc in suggestions if sc >= min_score]
    return suggestions

predictions = []
for idx, row in skill_mapping_df.iterrows():
    sugg = suggest_skills_for_skill_mapping_row(row, top_n=5)
    skill_names = [s for s, sc in sugg]
    skill_scores = [float(sc) for s, sc in sugg]
    predictions.append({
        "ID Kurzu": row.get("ID Kurzu"),
        "Zkratka D": row.get("Zkratka D"),
        "Název D": row.get("Název D"),
        "Téma": row.get("Téma"),
        "predicted_skills": skill_names,
        "predicted_scores": skill_scores
    })

pred_df = pd.DataFrame(predictions)
print("\nSample predictions for skill_mapping:")
print(pred_df.head())

output_file = "skill_mapping_with_predicted_skills.csv"
pred_df.to_csv(output_file, index=False)
print(f"\nPredictions saved to: {output_file}")
