import pandas as pd
import ast

import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px

# --------------------------------------------------
# 1. Load data
# --------------------------------------------------

file_path = "employee_skill_positions.csv"  # adjust path if needed
df = pd.read_csv(file_path)

print("Columns:", df.columns.tolist())
print(df.head())

# Expected columns:
# employee_id, skill, x, y, cluster_kmeans, top_skills_tfidf

# --------------------------------------------------
# 2. Parse top_skills_tfidf into a more readable form
# --------------------------------------------------

def parse_top_skills(cell, max_skills=5):
    """
    top_skills_tfidf is stored as a string like:
      "[('ai', 0.48), ('cloud', 0.28), ...]"
    This converts to a Python list and returns only the skill names,
    joined into a single string for display.
    """
    if pd.isna(cell):
        return ""
    try:
        lst = ast.literal_eval(str(cell))
        # lst is a list of (skill_name, weight)
        names = [s for s, w in lst[:max_skills] if isinstance(s, str)]
        return ", ".join(names)
    except Exception:
        return ""

df["top_skills_short"] = df["top_skills_tfidf"].apply(parse_top_skills)

# Also ensure cluster_kmeans is treated as categorical for plotting
df["cluster_kmeans"] = df["cluster_kmeans"].astype(str)

# --------------------------------------------------
# 3. Interactive scatter plot with Plotly
# --------------------------------------------------

def plot_interactive_scatter(dataframe):
    """
    2D scatter plot of employees:
    - x, y: UMAP coordinates
    - color: cluster_kmeans
    - hover: employee_id + top skills
    """
    fig = px.scatter(
        dataframe,
        x="x",
        y="y",
        color="cluster_kmeans",
        hover_name="employee_id",
        hover_data={
            "cluster_kmeans": True,
            "top_skills_short": True,
            "x": False,
            "y": False,
        },
        title="Employee Skill Clusters (UMAP + K-Means)",
        width=900,
        height=700
    )

    fig.update_traces(marker=dict(size=8, opacity=0.8))
    fig.update_layout(
        legend_title_text="Cluster (K-Means)",
        xaxis_title="UMAP 1",
        yaxis_title="UMAP 2",
    )
    fig.show()

plot_interactive_scatter(df)

# --------------------------------------------------
# 4. Static scatter plot with seaborn/matplotlib (optional)
# --------------------------------------------------

def plot_static_scatter(dataframe):
    plt.figure(figsize=(10, 8))
    sns.scatterplot(
        data=dataframe,
        x="x",
        y="y",
        hue="cluster_kmeans",
        palette="tab10",
        s=40,
        alpha=0.8,
        edgecolor=None
    )
    plt.title("Employee Skill Clusters (UMAP + K-Means)")
    plt.xlabel("UMAP 1")
    plt.ylabel("UMAP 2")
    plt.legend(title="Cluster", bbox_to_anchor=(1.05, 1), loc="upper left")
    plt.tight_layout()
    plt.show()

# Uncomment if you want a static plot:
# plot_static_scatter(df)

# --------------------------------------------------
# 5. Show top skills per cluster (bar chart)
# --------------------------------------------------

def build_skills_long(dataframe):
    """
    Expand the 'skill' column (space-separated skills) into a long dataframe:
      employee_id, cluster_kmeans, skill (one row per skill).
    """
    rows = []
    for _, row in dataframe.iterrows():
        emp_id = row["employee_id"]
        cluster = row["cluster_kmeans"]
        skills_str = str(row["skill"])
        # Split by whitespace (assuming each skill token is one "word")
        # If some skills have spaces, you may need a different separator.
        skill_tokens = skills_str.split()
        for s in skill_tokens:
            s_clean = s.strip().lower()
            if s_clean:
                rows.append({
                    "employee_id": emp_id,
                    "cluster_kmeans": cluster,
                    "skill": s_clean
                })
    return pd.DataFrame(rows)

skills_long = build_skills_long(df)

# Aggregate counts per cluster × skill
skill_counts = (
    skills_long
    .groupby(["cluster_kmeans", "skill"])
    .size()
    .reset_index(name="count")
)

def plot_top_skills_for_cluster(cluster_id, top_n=15):
    """
    Bar chart of top N most frequent skills in a given cluster.
    """
    subset = skill_counts[skill_counts["cluster_kmeans"] == str(cluster_id)]
    if subset.empty:
        print(f"No data for cluster {cluster_id}")
        return

    top_skills = subset.sort_values("count", ascending=False).head(top_n)

    plt.figure(figsize=(10, 6))
    sns.barplot(
        data=top_skills,
        x="count",
        y="skill",
        orient="h",
        palette="crest"
    )
    plt.title(f"Top {top_n} skills in cluster {cluster_id}")
    plt.xlabel("Count")
    plt.ylabel("Skill")
    plt.tight_layout()
    plt.show()

# Example: show top skills for cluster "2"
# (adjust cluster ID based on your output)
# plot_top_skills_for_cluster(cluster_id="2", top_n=20)

# --------------------------------------------------
# 6. Optional: Label a sample of points with employee_id on static plot
# --------------------------------------------------

def plot_static_with_labels_sample(dataframe, sample_size=30):
    """
    Static scatter plot with a random sample of employee IDs labeled
    to avoid clutter.
    """
    plt.figure(figsize=(10, 8))
    sns.scatterplot(
        data=dataframe,
        x="x",
        y="y",
        hue="cluster_kmeans",
        palette="tab10",
        s=40,
        alpha=0.5,
        edgecolor=None
    )

    sample = dataframe.sample(
        n=min(sample_size, len(dataframe)),
        random_state=42
    )

    for _, row in sample.iterrows():
        plt.text(
            row["x"] + 0.02,
            row["y"] + 0.02,
            str(row["employee_id"]),
            fontsize=8
        )

    plt.title("Employee Skill Clusters (sample labels)")
    plt.xlabel("UMAP 1")
    plt.ylabel("UMAP 2")
    plt.legend(title="Cluster", bbox_to_anchor=(1.05, 1), loc="upper left")
    plt.tight_layout()
    plt.show()

# Uncomment if you want a labeled static plot:
# plot_static_with_labels_sample(df, sample_size=30)
