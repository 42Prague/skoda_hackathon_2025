import pandas as pd
import psycopg2
from psycopg2.extras import execute_batch
import os
from dotenv import load_dotenv
import time
import math
from io import StringIO
import traceback

load_dotenv()
# -------------------
# PostgreSQL CONNECTION
# -------------------
DATABASE_URL = os.getenv("DATABASE_URL") or ""
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

# -------------------
# EXECUTE CREATE TABLES
# ------------------

# -------------------
# COLUMN MAPPINGS
# -------------------
mappings = {
    "employees": {
        "personal_number": "personal_number",
        "ob1": "ob1",
        "ob2": "ob2",
        "ob3": "ob3",
        "ob5": "ob5",
        "ob8": "ob8",
        "coordinator_group_id": "coordinator_group_id",
        "profession_id": "profession_id",
        "profession": "profession",
        "planned_profession_id": "planned_profession_id",
        "planned_profession": "planned_profession",
        "planned_position_id": "planned_position_id",
        "planned_position": "planned_position",
        "basic_branch_of_education_group": "education_branch_group",
        "basic_branch_of_education_grou2": "education_branch_group2",
        "basic_branch_of_education_id": "education_branch_id",
        "basic_branch_of_education_name": "education_branch_name",
        "education_category_id": "education_category_id",
        "education_category_name": "education_category_name",
        "field_of_study_id": "field_of_study_id",
        "field_of_study_name": "field_of_study_name",
        "field_of_stude_code_ispv": "field_of_study_code_ispv",
        "user_name": "user_name"
    },

    "course_participation": {
        "Typ akce": "event_type",
        "Označení typu akce": "event_name",
        "IDOBJ": "course_id",
        "Datum zahájení": "start_date",
        "Datum ukončení": "end_date",
        "ID účastníka": "personal_number"
    },

    "skill_mapping": {
        "ID objektu": "course_id",
        "Zkratka objektu": "course_shortcut",
        "Označení objektu": "course_name",
        "Počát.datum": "start_date",
        "Koncové datum": "end_date",
        "Katalog": "catalog",
        "Téma": "topic",
        "Skupina": "group_name",
        "ID skillu": "skill_id",
        "Skill v EN": "skill_name"
    },

    "skills": {
        "Skill (EN)": "skill_name",
        "Skill ID": "skill_id"
    },

    "degreed_learning": {
        "Completed Date": "completed_date",
        "Employee ID": "employee_id",
        "Content ID": "content_id",
        "Content Title": "content_title",
        "Content Type": "content_type",
        "Content Provider": "content_provider",
        "Completion is Verified": "completion_verified",
        "Completion User Rating": "completion_rating",
        "Completion Points": "completion_points",
        "Content URL": "content_url",
        "Verified Learning Minutes": "verified_learning_minutes",
        "Estimated Learning Minutes": "estimated_learning_minutes"
    },
    # "courses_catalog": {
    #     "Content ID": "content_id",
    #     "Title": "title",
    #     "Provider": "provider",
    #     "URL": "url",
    #     "Estimated Learning Minutes": "duration",
    #     "Summary": "description"
    # },
    "courses_catalog": {
        "course_id": "content_id",
        "title": "title",
        "original.provider": "provider",
        "original.url": "url",
        "original.duration": "duration",
        "original.description": "description"
    },
    # objid,paren,short,stxtc,stxtd,stxte
    "organization": {
        "objid": "object_id",
        "paren": "parent_id",
        "short": "short_name",
        "stxtc": "name_cz",
        "stxtd": "name_de",
        "stxte": "name_en"
    }
}


# -------------------
# IMPORT FUNCTION
# -------------------
def load_excel_to_postgres(filename, sheet, table, rename_map):
    print(f"Loading {filename} -> {table}", flush=True)

    df = pd.read_json(f"../data/csv_output/{filename}")
    # df = df.rename(columns=rename_map)
    # Build a flattened dataframe according to rename_map.
    # rename_map keys can be top-level keys (e.g. "course_id") or nested with dot notation (e.g. "original.description").
    def extract_value(obj, path):
        if obj is None:
            return None
        parts = path.split(".")
        v = obj
        for p in parts:
            if v is None:
                return None
            if isinstance(v, dict):
                v = v.get(p)
            else:
                # attempt index/key access for lists or pandas objects
                try:
                    v = v[p]
                except Exception:
                    return None
        return v

    flat = {}
    # for performance, we will operate per mapping and use row.to_dict() inside apply
    for src, dst in rename_map.items():
        # create column values by extracting nested values from each row
        flat[dst] = df.apply(lambda r: extract_value(r.to_dict(), src), axis=1)

    df = pd.DataFrame(flat)

    # Keep only columns that are mapped to target table columns to avoid unknown CSV headers
    mapped_targets = set(rename_map.values())
    cols_present = [c for c in df.columns if c in mapped_targets]
    removed = [c for c in df.columns if c not in mapped_targets]
    if removed:
        print(f"[{table}] Dropping {len(removed)} unmapped columns: {removed}", flush=True)
    df = df[cols_present]

    # If no columns remain after filtering, nothing to insert
    if df.shape[1] == 0:
        print(f"[{table}] No mapped columns found in {filename}, skipping.", flush=True)
        return

    # Convert dates automatically
    for col in df.columns:
        if "date" in col.lower():
            df[col] = pd.to_datetime(df[col], errors="coerce").dt.date

    # replace pandas missing values (NaN/NA) with Python None for psycopg2
    df = df.where(pd.notnull(df), None)

    total = len(df)
    if total == 0:
        print(f"[{table}] No rows to insert.", flush=True)
        return

    columns = list(df.columns)
    quoted_cols = ",".join([f'"{c}"' for c in columns])

    # Try fast path: COPY FROM STDIN using an in-memory CSV
    try:
        print(f"[{table}] Attempting COPY (fast path) for {total} rows...", flush=True)
        csv_buf = StringIO()
        # Use \N for NULLs and no header (we provide column list to COPY)
        df = df.drop_duplicates(['content_id'])
        df.to_csv(csv_buf, index=False, header=False, na_rep="\\N")
        csv_buf.seek(0)

        copy_sql = f"COPY {table} ({quoted_cols}) FROM STDIN WITH CSV NULL '\\N' DELIMITER ','"
        start_time = time.time()
        cur.copy_expert(copy_sql, csv_buf)
        conn.commit()
        elapsed = time.time() - start_time
        print(f"[{table}] COPY completed: inserted {total} rows in {elapsed:.1f}s", flush=True)
        return
    except Exception as e:
        conn.rollback()
        print(f"[{table}] COPY failed, falling back to batched inserts: {e}", flush=True)
        traceback.print_exc()

    # Fallback: batched inserts using execute_values (faster than execute_batch)
    from psycopg2.extras import execute_values

    insert_sql = f"INSERT INTO {table} ({quoted_cols}) VALUES %s"
    batch_size = int(os.getenv("PG_BATCH_SIZE", "5000"))
    values = df.values.tolist()
    num_batches = math.ceil(total / batch_size)

    start_time = time.time()
    rows_done = 0

    for b in range(num_batches):
        i = b * batch_size
        chunk = values[i:i + batch_size]
        # retry logic for transient failures
        retries = 3
        for attempt in range(1, retries + 1):
            batch_start = time.time()
            try:
                execute_values(cur, insert_sql, chunk, page_size=len(chunk))
                conn.commit()
                break
            except Exception as e:
                conn.rollback()
                print(f"[{table}] Batch {b+1}/{num_batches} attempt {attempt} failed: {e}", flush=True)
                traceback.print_exc()
                if attempt < retries:
                    sleep_for = 2 ** attempt
                    print(f"[{table}] Retrying after {sleep_for}s...", flush=True)
                    time.sleep(sleep_for)
                else:
                    raise

        batch_elapsed = time.time() - batch_start
        rows_done += len(chunk)
        elapsed = time.time() - start_time
        pct = rows_done / total * 100
        eta = (elapsed / rows_done) * (total - rows_done) if rows_done else float("inf")
        print(f"[{table}] inserted {rows_done}/{total} rows ({pct:.2f}%) - batch {b+1}/{num_batches} - batch_time {batch_elapsed:.1f}s - elapsed {elapsed:.1f}s - ETA {eta:.1f}s", flush=True)

        # Warn if a single batch is taking unexpectedly long
        if batch_elapsed > 60:
            print(f"[{table}] Warning: batch {b+1} took {batch_elapsed:.1f}s — consider reducing PG_BATCH_SIZE or using COPY", flush=True)

    total_time = time.time() - start_time
    print(f"[{table}] Completed inserting {total} rows in {total_time:.1f}s", flush=True)


# -------------------
# IMPORT EACH FILE
# -------------------
# load_excel_to_postgres("ERP_SK1.Start_month_-_SE.csv", 0,
#                        "employees", mappings["employees"])

# load_excel_to_postgres("ZHRPD_VZD_STA_007.csv", 0,
#                        "course_participation", mappings["course_participation"])

# load_excel_to_postgres("Skill_mapping__Mapping.csv", 0,
#                        "skill_mapping", mappings["skill_mapping"])

# load_excel_to_postgres("Skill_mapping__Skills_1.25.csv", 0,
#                        "skills", mappings["skills"])

# load_excel_to_postgres("Degreed.csv", 0,
                    #    "degreed_learning", mappings["degreed_learning"])
# load_excel_to_postgres("Degreed_Content_Catalog.csv", 0,
#                        "degreed_catalog", mappings["degreed_catalog"])
load_excel_to_postgres("metadata.json", 0,
                       "courses_catalog", mappings["courses_catalog"])


print("🎉 All data imported successfully into PostgreSQL!")
