"""
Upload Automation Endpoints for n8n Integration
Automatically categorizes and processes uploaded skill data
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from typing import Dict, Any
import pandas as pd
import tempfile
import os

from parsers.multi_format_parser import MultiFormatParser
from parsers.validator import DataTransformer
from data.db_writer import persist_parsed_data_to_db
from data.skill_categorizer import SkillCategorizer
from data.anomaly_detection import IngestionAnomalyDetector, log_ingestion_event

router = APIRouter(prefix="/api/automation", tags=["automation"])


@router.post("/upload")
async def automated_upload(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Automated file upload with auto-categorization

    Perfect for n8n workflows:
    1. Upload CSV/Excel file
    2. Auto-detect format
    3. Auto-categorize skills
    4. Validate and persist to database
    5. Return detailed report

    Example n8n HTTP Request node config:
    - URL: https://backend.fly.dev/api/automation/upload
    - Method: POST
    - Body: multipart-form-data
    - File field: file
    """
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        # Step 1: Parse file (auto-detect format)
        parser = MultiFormatParser()
        parsed = parser.parse_file(tmp_path)

        if not parsed['success']:
            os.unlink(tmp_path)
            raise HTTPException(status_code=400, detail=parsed.get('error', 'Failed to parse file'))

        df = parsed['data']
        detected_format = parsed['format']

        # Step 2: Auto-categorize skills
        if 'skill_name' in df.columns or 'skill' in df.columns:
            skill_col = 'skill_name' if 'skill_name' in df.columns else 'skill'

            # Add category column if missing
            if 'category' not in df.columns or 'skill_category' not in df.columns:
                df['category'] = df[skill_col].apply(SkillCategorizer.categorize)
                df['skill_category'] = df['category']
                categorized = True
            else:
                # Auto-categorize only skills with missing/General category
                df['category'] = df.apply(
                    lambda row: SkillCategorizer.categorize(row[skill_col])
                    if row.get('category') in [None, '', 'General']
                    else row['category'],
                    axis=1
                )
                categorized = True
        else:
            categorized = False

        # Step 3: Transform to canonical format
        transformer = DataTransformer()
        canonical_df = transformer.transform_to_canonical(df, detected_format)

        # Step 4: Anomaly detection
        detector = IngestionAnomalyDetector()
        anomaly_report = detector.run_full_validation(
            canonical_df,
            source=detected_format,
            date_columns=['event_date', 'hire_date']
        )

        # Step 5: Persist to database (if no critical anomalies)
        if anomaly_report['overall_status'] != 'fail':
            persist_parsed_data_to_db(canonical_df, detected_format)
            status = 'success' if anomaly_report['overall_status'] == 'pass' else 'warning'
        else:
            status = 'failed'

        # Step 6: Log ingestion event
        log_ingestion_event(
            filename=file.filename,
            format_detected=detected_format,
            rows_processed=len(canonical_df),
            status=status,
            anomaly_report=anomaly_report,
            error_message=anomaly_report['summary'] if status == 'failed' else None
        )

        # Clean up
        os.unlink(tmp_path)

        # Step 7: Generate category statistics
        if categorized:
            category_stats = SkillCategorizer.get_category_stats(
                df[skill_col if skill_col in df.columns else 'skill_name'].unique()
            )
        else:
            category_stats = {}

        return {
            "success": True,
            "status": status,
            "message": f"Processed {len(canonical_df)} rows",
            "details": {
                "filename": file.filename,
                "format_detected": detected_format,
                "rows_processed": len(canonical_df),
                "auto_categorized": categorized,
                "category_distribution": category_stats,
                "anomaly_report": anomaly_report,
                "skills_added": len(df[skill_col].unique()) if skill_col in df.columns else 0
            }
        }

    except Exception as e:
        if 'tmp_path' in locals():
            os.unlink(tmp_path)
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.post("/categorize-csv")
async def categorize_csv_file(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Categorize CSV file and return categorized version

    For n8n: Upload CSV, receive categorized CSV back

    Input CSV columns: skill, year, popularity (category optional)
    Output CSV columns: skill, year, popularity, category
    """
    try:
        # Save uploaded file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        # Read CSV
        df = pd.read_csv(tmp_path)

        # Auto-categorize
        if 'skill' in df.columns:
            df['category'] = df['skill'].apply(SkillCategorizer.categorize)
        elif 'skill_name' in df.columns:
            df['category'] = df['skill_name'].apply(SkillCategorizer.categorize)
        else:
            raise ValueError("CSV must have 'skill' or 'skill_name' column")

        # Save categorized CSV
        output_path = tmp_path.replace('.csv', '_categorized.csv')
        df.to_csv(output_path, index=False)

        # Read categorized file content
        with open(output_path, 'r') as f:
            categorized_csv = f.read()

        # Category stats
        category_stats = SkillCategorizer.get_category_stats(
            df['skill' if 'skill' in df.columns else 'skill_name'].unique()
        )

        # Clean up
        os.unlink(tmp_path)
        os.unlink(output_path)

        return {
            "success": True,
            "categorized_csv": categorized_csv,
            "category_distribution": category_stats,
            "total_skills": len(df['skill' if 'skill' in df.columns else 'skill_name'].unique()),
            "total_rows": len(df)
        }

    except Exception as e:
        if 'tmp_path' in locals():
            try:
                os.unlink(tmp_path)
            except:
                pass
        raise HTTPException(status_code=500, detail=f"Categorization failed: {str(e)}")


@router.get("/category-keywords")
async def get_category_keywords() -> Dict[str, Any]:
    """
    Get all category keywords for reference
    Useful for understanding auto-categorization logic
    """
    return {
        "success": True,
        "categories": SkillCategorizer.CATEGORY_KEYWORDS,
        "example_categorizations": {
            "Python": SkillCategorizer.categorize("Python"),
            "CAD": SkillCategorizer.categorize("CAD"),
            "Battery Systems": SkillCategorizer.categorize("Battery Systems"),
            "Machine Learning": SkillCategorizer.categorize("Machine Learning"),
            "Unknown Skill": SkillCategorizer.categorize("Unknown Skill")
        }
    }
