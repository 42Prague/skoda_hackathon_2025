# 📄 Training AI from Text Files

## ✅ You Can Now Train Directly from .txt Files!

No need to use Excel - train your AI with plain text files in multiple formats.

---

## 🚀 Quick Start

### Option 1: Use Templates

```bash
source venv/bin/activate
python train_from_text.py
# Choose option 1: Create templates
```

This creates:
- `training_courses_skills.txt` - Course-skill mappings
- `training_employee_readiness.txt` - Employee scores

**Edit these files with your data**, then train:

```bash
python train_from_text.py
# Choose option 2: Train from text files
```

---

### Option 2: Use Your Existing .txt Files

```bash
python train_from_text.py
# Choose option 2
# Enter your file paths when prompted
```

---

## 📝 Supported Text Formats

### 1. **Pipe-Delimited** (Simplest!)

**File: `my_courses.txt`**
```
C001|Python Programming Basics|Python
C001|Python Programming Basics|Programming
C002|SQL Database Management|SQL
C003|Leadership for Managers|Leadership
```

Format: `course_id|course_text|skill_name`

---

### 2. **JSON Format**

**File: `my_courses.json`**
```json
[
  {
    "course_id": "C001",
    "course_text": "Python Programming Basics",
    "skill_name": "Python"
  },
  {
    "course_id": "C002",
    "course_text": "SQL Database Management",
    "skill_name": "SQL"
  }
]
```

---

### 3. **CSV Format**

**File: `my_courses.csv`**
```
course_id,course_text,skill_name
C001,Python Programming Basics,Python
C001,Python Programming Basics,Programming
C002,SQL Database Management,SQL
```

---

### 4. **Free-Form Text** (Most Flexible!)

**File: `my_courses.txt`**
```
Course: Python Programming Basics teaches Python, Programming
Course: SQL Database Management teaches SQL, Database Design
Python for Data Science -> Skills: Python, Data Analysis, Statistics
```

The AI auto-detects patterns like:
- `Course: <name> teaches <skills>`
- `<name> -> Skills: <skills>`
- `<id>: <name> (Skills: <skills>)`

---

## 📊 Employee Readiness Files

### Pipe-Delimited:
```
0001689|85.0|Ready for promotion
0001690|72.5|Needs more training
0001691|90.0|Excellent candidate
```

Format: `employee_id|readiness_score|notes`

### JSON:
```json
[
  {"employee_id": "0001689", "readiness_score": 85.0},
  {"employee_id": "0001690", "readiness_score": 72.5}
]
```

---

## 🎯 Complete Workflow

```bash
# 1. Activate environment
source venv/bin/activate

# 2. Prepare your text file
# Format: course_id|course_text|skill_name
nano my_training_data.txt

# 3. Train AI
python train_from_text.py

# 4. Choose option 2 and enter your file path
# Enter: my_training_data.txt

# 5. Models saved to models/ folder!
```

---

## 💡 Real Example

### Your Text File: `company_courses.txt`

```
# Our company training courses
PROG101|Introduction to Python Programming|Python
PROG101|Introduction to Python Programming|Programming
PROG101|Introduction to Python Programming|Coding
DB201|Advanced SQL for Data Analysis|SQL
DB201|Advanced SQL for Data Analysis|Database
DB201|Advanced SQL for Data Analysis|Data Analysis
LEAD301|Leadership Essentials|Leadership
LEAD301|Leadership Essentials|Management
LEAD301|Leadership Essentials|Communication
```

### Train with it:

```bash
python train_from_text.py
# Option 2
# Course file: company_courses.txt
# Employee file: (press Enter to skip)
```

### Output:
```
✓ Loaded 9 course-skill mappings
Training Accuracy: 0.95
Validation Accuracy: 0.88
✅ Model saved to models/
```

---

## 🔍 What the Script Does

1. **Auto-detects format** - JSON, CSV, pipe-delimited, or free-form
2. **Loads your data** - Parses course-skill pairs
3. **Trains ML model** - Using scikit-learn
4. **Saves model** - To `models/` folder
5. **Tests predictions** - Shows sample results

---

## 📋 Minimum Requirements

- **At least 10 course-skill pairs** for training
- One skill per line (same course can appear multiple times)
- Valid format (see examples above)

---

## 🆘 Troubleshooting

### "Not enough training data"
➜ Add more lines to your text file (need at least 10)

### "Error loading data"
➜ Run: `python train_from_text.py` → Option 3 to see format examples

### "File not found"
➜ Check file path, use full path: `/home/user/data/courses.txt`

### Format not recognized
➜ Use pipe-delimited (simplest): `id|text|skill`

---

## 🎨 Mix & Match Formats

You can have:
- Course data in `.txt`
- Employee data in `.json`
- Or all in the same format

The script auto-detects each file's format!

---

## ⚡ Quick Commands

### See all supported formats:
```bash
python train_from_text.py
# Choose option 3
```

### Create templates:
```bash
python train_from_text.py
# Choose option 1
```

### Train AI:
```bash
python train_from_text.py
# Choose option 2
```

---

## 🎉 Benefits of Text Files

✅ **Easy to edit** - Use any text editor  
✅ **Version control** - Track changes in git  
✅ **Scripts friendly** - Generate from databases  
✅ **No Excel needed** - Plain text only  
✅ **Multiple formats** - Choose what works for you

---

## 🚀 Next Step

**Create your first training file:**

```bash
# Create a simple text file
cat > my_courses.txt << 'EOF'
C001|Python Basics|Python
C001|Python Basics|Programming
C002|SQL Fundamentals|SQL
C003|Project Management|PM
C004|Leadership Skills|Leadership
EOF

# Train AI with it
python train_from_text.py
```

**You're ready to train!** 🎯
