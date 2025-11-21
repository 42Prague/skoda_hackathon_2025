# 🤖 n8n Automation Guide - Skill DNA Auto-Upload & Categorization

## Overview

Automate skill data ingestion with intelligent categorization using n8n workflows. The backend now auto-categorizes skills based on keywords and patterns.

## 🎯 Features

✅ **Auto-Categorization** - Automatically assigns skills to:
- `legacy_engineering` - CAD, Mechanical Design, Manufacturing, etc.
- `software_cloud` - Python, React, AWS, Docker, Kubernetes, etc.
- `e_mobility` - Battery Systems, Electric Powertrain, Charging, etc.
- `ai_emerging` - Machine Learning, TensorFlow, NLP, Computer Vision, etc.

✅ **Multi-Format Support** - Handles CSV, Excel, Parquet, JSON
✅ **Anomaly Detection** - Validates data quality before database insertion
✅ **Webhook Ready** - n8n-compatible endpoints for workflow automation

---

## 📡 API Endpoints

### 1. `/api/automation/upload` - Full Automated Upload

**Purpose**: Upload files with complete processing pipeline (parse → categorize → validate → persist)

**Method**: `POST`
**Content-Type**: `multipart/form-data`

**Request**:
```bash
curl -X POST https://backend-long-resonance-8576.fly.dev/api/automation/upload \
  -F "file=@skills_data.csv"
```

**Response**:
```json
{
  "success": true,
  "status": "success",
  "message": "Processed 638 rows",
  "details": {
    "filename": "skills_data.csv",
    "format_detected": "HR_SYSTEM",
    "rows_processed": 638,
    "auto_categorized": true,
    "category_distribution": {
      "software_cloud": 5,
      "legacy_engineering": 4,
      "e_mobility": 3,
      "ai_emerging": 2,
      "General": 150
    },
    "anomaly_report": {
      "overall_status": "pass",
      "anomaly_count": 0,
      "checks": {...}
    },
    "skills_added": 164
  }
}
```

---

### 2. `/api/automation/categorize-csv` - CSV Categorization Only

**Purpose**: Upload CSV, receive categorized CSV (no database insertion)

**Method**: `POST`
**Content-Type**: `multipart/form-data`

**Request**:
```bash
curl -X POST https://backend-long-resonance-8576.fly.dev/api/automation/categorize-csv \
  -F "file=@skills.csv"
```

**Input CSV** (category optional):
```csv
skill,year,popularity
Python,2024,92.1
React,2024,106.2
CAD,2024,50.2
```

**Response**:
```json
{
  "success": true,
  "categorized_csv": "skill,year,popularity,category\nPython,2024,92.1,software_cloud\nReact,2024,106.2,software_cloud\nCAD,2024,50.2,legacy_engineering\n",
  "category_distribution": {
    "software_cloud": 2,
    "legacy_engineering": 1
  },
  "total_skills": 3,
  "total_rows": 3
}
```

**Use Case**: Pre-process CSV files before manual review

---

### 3. `/api/automation/category-keywords` - View Categorization Logic

**Purpose**: Get all category keywords for reference

**Method**: `GET`

**Request**:
```bash
curl https://backend-long-resonance-8576.fly.dev/api/automation/category-keywords
```

**Response**:
```json
{
  "success": true,
  "categories": {
    "software_cloud": ["python", "javascript", "react", "aws", "docker", ...],
    "legacy_engineering": ["cad", "mechanical", "cnc", "manufacturing", ...],
    "e_mobility": ["battery", "powertrain", "charging", "ev", ...],
    "ai_emerging": ["machine learning", "tensorflow", "nlp", ...]
  },
  "example_categorizations": {
    "Python": "software_cloud",
    "CAD": "legacy_engineering",
    "Battery Systems": "e_mobility",
    "Machine Learning": "ai_emerging",
    "Unknown Skill": "General"
  }
}
```

---

## 🔧 n8n Workflow Templates

### Workflow 1: Auto-Upload from Google Drive

**Trigger**: New file added to Google Drive folder
**Flow**: Download → Upload to Skill DNA → Log results to Slack

```
[Google Drive Trigger]
    ↓
[Download File]
    ↓
[HTTP Request: POST /api/automation/upload]
    ↓
[Slack: Send notification with results]
```

**n8n HTTP Request Node Config**:
```json
{
  "method": "POST",
  "url": "https://backend-long-resonance-8576.fly.dev/api/automation/upload",
  "bodyParameters": {
    "parameterType": "formData",
    "parameter": [
      {
        "name": "file",
        "value": "={{ $binary.data }}"
      }
    ]
  },
  "sendBinaryData": true
}
```

---

### Workflow 2: Categorize & Email Report

**Trigger**: Manual trigger or schedule
**Flow**: Upload CSV → Categorize → Email categorized CSV

```
[Manual Trigger / Schedule]
    ↓
[Read CSV from File/URL]
    ↓
[HTTP Request: POST /api/automation/categorize-csv]
    ↓
[Email: Send categorized CSV]
```

**n8n HTTP Request Node Config**:
```json
{
  "method": "POST",
  "url": "https://backend-long-resonance-8576.fly.dev/api/automation/categorize-csv",
  "bodyParameters": {
    "parameterType": "formData",
    "parameter": [
      {
        "name": "file",
        "value": "={{ $binary.data }}"
      }
    ]
  },
  "sendBinaryData": true
}
```

**Email Node Config**:
```json
{
  "toEmail": "hr@company.com",
  "subject": "Categorized Skills Report - {{ $now.format('YYYY-MM-DD') }}",
  "text": "Category Distribution:\n{{ JSON.stringify($json.category_distribution, null, 2) }}",
  "attachments": [
    {
      "name": "categorized_skills.csv",
      "content": "={{ $json.categorized_csv }}"
    }
  ]
}
```

---

### Workflow 3: Slack Bot Upload

**Trigger**: Slack command `/upload-skills`
**Flow**: User uploads file in Slack → Auto-process → Reply with results

```
[Slack Trigger: /upload-skills]
    ↓
[Extract file from Slack message]
    ↓
[HTTP Request: POST /api/automation/upload]
    ↓
[Slack: Reply to thread with results]
```

---

## 🎯 Auto-Categorization Logic

### Category Keywords

**Software & Cloud**:
- Languages: python, javascript, java, c++, c#
- Frameworks: react, angular, vue, django, spring
- DevOps: docker, kubernetes, aws, azure, ci/cd
- Databases: sql, mongodb, postgresql, redis

**Legacy Engineering**:
- CAD tools: cad, catia, autocad, solidworks
- Manufacturing: cnc, machining, welding, assembly
- Quality: quality control, inspection, testing

**E-Mobility**:
- battery, electric, powertrain, charging
- ev, hybrid, bms, inverter, motor control

**AI & Emerging**:
- machine learning, deep learning, tensorflow, pytorch
- nlp, computer vision, llm, transformers
- data science, analytics

**Fallback**: Skills not matching any keywords → `General`

---

## 📊 Integration Examples

### Example 1: Airtable Sync

**Use Case**: HR team manages skills in Airtable, auto-sync to Skill DNA

**Workflow**:
```
[Airtable Trigger: Record Updated]
    ↓
[Format Data as CSV]
    ↓
[HTTP Request: POST /api/automation/upload]
    ↓
[Update Airtable with category]
```

---

### Example 2: Scheduled HR Export

**Use Case**: Daily export from HR system → Auto-categorize → Persist

**Workflow**:
```
[Schedule: Daily 2 AM]
    ↓
[SFTP: Download HR export]
    ↓
[HTTP Request: POST /api/automation/upload]
    ↓
[Email: Success notification]
```

---

### Example 3: Employee Self-Service

**Use Case**: Employees upload skill profiles via web form

**Workflow**:
```
[Webhook: Form submission]
    ↓
[Extract uploaded file]
    ↓
[HTTP Request: POST /api/automation/upload]
    ↓
[Database: Log submission]
    ↓
[Email: Confirmation to employee]
```

---

## 🚀 Deployment to n8n Cloud

### Step 1: Create Workflow

1. Log in to n8n.cloud
2. Create new workflow: **"Skill DNA Auto-Upload"**
3. Add nodes as shown in templates above

### Step 2: Configure Authentication

If backend requires auth (optional):
```json
{
  "authentication": "headerAuth",
  "credentialName": "SkillDNA-API",
  "headerAuth": {
    "name": "Authorization",
    "value": "Bearer YOUR_API_KEY"
  }
}
```

### Step 3: Test Workflow

1. Upload sample CSV file
2. Check n8n execution log
3. Verify database updated: `curl https://backend.fly.dev/api/insights`

### Step 4: Activate Trigger

- Enable workflow
- Set schedule (if cron trigger)
- Test with real HR data

---

## 🛠️ Customization

### Add Custom Categories

Edit `backend/data/skill_categorizer.py`:

```python
CATEGORY_KEYWORDS = {
    'legacy_engineering': [...],
    'software_cloud': [...],
    'e_mobility': [...],
    'ai_emerging': [...],

    # NEW CATEGORY
    'cybersecurity': [
        'penetration testing', 'firewall', 'encryption',
        'security audit', 'vulnerability', 'soc', 'siem'
    ]
}
```

Then update `backend/ai/timeseries.py`:

```python
category_map = {
    'legacy_engineering': 'Legacy',
    'software_cloud': 'Software',
    'e_mobility': 'EV',
    'ai_emerging': 'AI',
    'cybersecurity': 'Security'  # NEW
}
```

Redeploy:
```bash
fly deploy --ha=false
```

---

## 🎯 Testing

### Test Categorization Endpoint

```bash
curl https://backend-long-resonance-8576.fly.dev/api/automation/category-keywords | jq
```

### Test Upload with Sample CSV

```bash
echo "skill,year,popularity
Python,2024,92.1
React,2024,106.2
CAD,2024,50.2
Battery Systems,2024,98.5" > test.csv

curl -X POST https://backend-long-resonance-8576.fly.dev/api/automation/upload \
  -F "file=@test.csv" | jq
```

### Expected Output

```json
{
  "success": true,
  "status": "success",
  "details": {
    "auto_categorized": true,
    "category_distribution": {
      "software_cloud": 2,
      "legacy_engineering": 1,
      "e_mobility": 1
    }
  }
}
```

---

## 📈 Monitoring

### Check Upload History

```bash
curl https://backend-long-resonance-8576.fly.dev/api/upload-history
```

### View Categorization Stats

```bash
curl https://backend-long-resonance-8576.fly.dev/api/insights | jq .category_trends
```

### Watch Live Logs

```bash
fly logs --app backend-long-resonance-8576
```

---

## 🆘 Troubleshooting

### Problem: Skills categorized as "General"

**Cause**: Skill names don't match any keywords

**Solution**: Add keywords to `skill_categorizer.py` or manually specify category in CSV

---

### Problem: Upload fails with 400 error

**Cause**: CSV format not recognized

**Solution**: Ensure CSV has required columns (`skill_name` or `skill`, `year`, `popularity`)

---

### Problem: Anomaly report shows "fail"

**Cause**: Data quality issues (date drift, volume spike, malformed headers)

**Solution**: Check `anomaly_report` in response, fix data issues, re-upload

---

## 📞 Support

- **Backend API**: https://backend-long-resonance-8576.fly.dev
- **Frontend**: https://skill-dna-organizational-genome.vercel.app
- **Docs**: https://github.com/yourusername/skill-dna

---

## ✅ Quick Start Checklist

- [ ] Install n8n (cloud or self-hosted)
- [ ] Test `/api/automation/category-keywords` endpoint
- [ ] Create sample CSV file
- [ ] Test `/api/automation/upload` with sample file
- [ ] Create n8n workflow from template
- [ ] Configure trigger (schedule/webhook/file monitor)
- [ ] Test end-to-end workflow
- [ ] Enable workflow and monitor logs
- [ ] Customize categories if needed

---

**Congratulations! You now have fully automated skill data ingestion with intelligent categorization!** 🎉
