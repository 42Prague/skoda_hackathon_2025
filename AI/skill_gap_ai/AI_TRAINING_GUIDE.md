# AI Training Guide

## Quick Start: Training Your AI Models

You now have a **trainable AI system** with machine learning capabilities!

## 🎯 What You Can Train

1. **Skill Matching AI** - Learns to automatically map courses to skills
2. **Readiness Prediction AI** - Predicts employee job readiness scores

---

## 📋 Step-by-Step Training Process

### Step 1: Prepare Your Training Data

You have **3 options**:

#### Option A: Use the Template (Recommended for first-time users)
```bash
source venv/bin/activate
python train_ai.py
# Choose option 1: Create training data template
```

This creates `training_data_template.xlsx` with sample data. Replace it with your real data.

#### Option B: Extract from Existing Data
```bash
python train_ai.py
# Choose option 2: Extract training data from existing Excel files
```

This automatically extracts course-skill mappings from your existing data files.

#### Option C: Full Automated Workflow
```bash
python train_ai.py
# Choose option 4: Full workflow (extract + train)
```

---

### Step 2: Label Your Data

The AI needs **labeled training data**:

#### For Skill Matching:
- **course_id**: Course identifier
- **course_text**: Course title + description  
- **skill_name**: What skill does this course teach?

Example:
```
course_id  | course_text                    | skill_name
C001       | Python Programming Basics      | Python
C001       | Python Programming Basics      | Programming
C002       | SQL Database Management        | SQL
```

#### For Readiness Prediction:
- **employee_id**: Employee identifier
- **readiness_score**: Actual score from performance review (0-100)

Example:
```
employee_id | readiness_score | notes
0001689     | 85.0           | Ready for senior role
0001690     | 72.5           | Needs more leadership training
```

**⚠️ IMPORTANT**: You must manually fill in `readiness_score` based on:
- Performance reviews
- Manager assessments
- Actual promotions/transitions
- Skills assessments

---

### Step 3: Train the Models

Once your training data is ready:

```bash
source venv/bin/activate
python train_ai.py
# Choose option 3: Train AI models
```

The system will:
1. Load your training data
2. Split into training/validation sets
3. Train machine learning models
4. Evaluate accuracy
5. Save trained models to `models/` folder

---

### Step 4: Use Trained Models

After training, integrate into your main system by updating `main.py`:

```python
from ai_training import SkillMatchingAI

# Load trained model
skill_ai = SkillMatchingAI()
skill_ai.load_model('models')

# Use for predictions
course_text = "Advanced Python for Data Science"
predicted_skills = skill_ai.predict_skills_for_course(course_text, top_k=3)

for skill_name, confidence in predicted_skills:
    print(f"  {skill_name}: {confidence:.2%} confidence")
```

---

## 💡 Training Data Requirements

### Minimum Requirements:
- **At least 10 course-skill pairs** for Skill Matching AI
- **At least 10 employees with scores** for Readiness Prediction AI

### Recommended:
- **50+ course-skill pairs** for better accuracy
- **30+ employee scores** for reliable predictions
- **Diverse examples** covering different skills and levels

---

## 🔄 Workflow Examples

### Example 1: You have existing data files
```bash
# 1. Extract training data from your Excel files
python train_ai.py  # Choose option 2

# 2. Open my_training_data.xlsx and fill in readiness scores

# 3. Train the models
python train_ai.py  # Choose option 3
```

### Example 2: Starting from scratch
```bash
# 1. Create template
python train_ai.py  # Choose option 1

# 2. Fill in training_data_template.xlsx with your data

# 3. Train
python train_ai.py  # Choose option 3
```

---

## 📊 Model Performance

After training, you'll see:

```
🎓 Training Skill Matching AI...
  ✓ Training Accuracy: 0.923
  ✓ Validation Accuracy: 0.857

  Classification Report:
              precision    recall  f1-score   support
    Python       0.89      0.92      0.90        24
    SQL          0.85      0.88      0.87        17
    ...

💾 Models saved to: models/
```

**Good performance**: Validation accuracy > 80%
**Needs more data**: Validation accuracy < 70%

---

## 🚀 Next Steps

1. **Collect more training data** - The more data, the better the AI
2. **Retrain periodically** - As you get new courses/employees
3. **A/B test** - Compare AI recommendations vs manual mappings
4. **Fine-tune** - Adjust model parameters in `ai_training.py`

---

## 📁 Files Created

```
skill_gap_ai/
├── ai_training.py              # AI model definitions
├── train_ai.py                 # Training script
├── models/                     # Saved trained models
│   ├── skill_matching_model.pkl
│   └── readiness_prediction_model.pkl
├── training_data_template.xlsx # Template for training data
└── my_training_data.xlsx       # Your actual training data
```

---

## 🆘 Troubleshooting

**"Not enough training data"**
- You need at least 10 examples. Add more course-skill pairs.

**"readiness_score column is empty"**
- Fill in actual scores from performance reviews before training.

**"Low validation accuracy"**
- Add more diverse training examples
- Check for labeling errors
- Ensure data quality

**"Model file not found"**
- Train models first using `train_ai.py`

---

## 🎓 Understanding the AI

### Skill Matching AI
- Uses **TF-IDF vectorization** + **Random Forest classifier**
- Learns patterns between course descriptions and skills
- Can predict skills for new courses automatically

### Readiness Prediction AI  
- Uses **Gradient Boosting Regressor**
- Learns from employee features (skills, courses, hours)
- Predicts readiness scores for employees

Both models use **supervised learning** - they learn from labeled examples you provide.

---

## 📞 Need Help?

Run the interactive training wizard:
```bash
python train_ai.py
```

Follow the prompts to set up your training pipeline!
