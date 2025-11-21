# 🚀 Skill Gap AI - Web API & Demo

## ✅ Your AI is now running as a web service!

---

## 🌐 **What's Running:**

**API Server:** `http://localhost:5000`
- REST API that accepts course titles
- Returns predicted skills with confidence scores
- Supports both English and Czech

**Demo Website:** Open `demo.html` in your browser
- Beautiful interactive interface
- Live predictions
- Visual confidence scores

---

## 📡 **API Endpoints:**

### **1. Health Check**
```bash
curl http://localhost:5000/health
```

### **2. Predict Skills (Single Course)**
```bash
curl -X POST http://localhost:5000/predict \
  -H "Content-Type: application/json" \
  -d '{"course_title": "Python Programming for Data Science", "top_k": 5}'
```

Response:
```json
{
  "course_title": "Python Programming for Data Science",
  "predictions": [
    {"skill": "Programming", "confidence": 0.85},
    {"skill": "Data Analysis", "confidence": 0.72},
    {"skill": "Python", "confidence": 0.68}
  ]
}
```

### **3. Batch Prediction (Multiple Courses)**
```bash
curl -X POST http://localhost:5000/predict/batch \
  -H "Content-Type: application/json" \
  -d '{
    "courses": [
      "Python Programming",
      "Excel for Business",
      "Leadership Skills"
    ],
    "top_k": 3
  }'
```

### **4. Get Model Stats**
```bash
curl http://localhost:5000/stats
```

---

## 🖥️ **View the Demo:**

**Option 1: Open file directly**
```bash
# Open in your default browser
xdg-open demo.html
# or
firefox demo.html
```

**Option 2: Access via file path**
```
file:///home/mstefano/Documents/Projects/skill_gap_ai/demo.html
```

---

## 🔗 **Integrate into Your Website:**

### **JavaScript Example:**
```javascript
// Predict skills for a course
async function getSkills(courseTitle) {
    const response = await fetch('http://localhost:5000/predict', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            course_title: courseTitle,
            top_k: 5
        })
    });
    
    const data = await response.json();
    console.log(data.predictions);
    return data;
}

// Usage
getSkills("Python Programming for Data Science")
    .then(result => {
        result.predictions.forEach(pred => {
            console.log(`${pred.skill}: ${(pred.confidence * 100).toFixed(0)}%`);
        });
    });
```

### **React Example:**
```jsx
import React, { useState } from 'react';

function SkillPredictor() {
    const [course, setCourse] = useState('');
    const [predictions, setPredictions] = useState([]);

    const predictSkills = async () => {
        const response = await fetch('http://localhost:5000/predict', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ course_title: course, top_k: 5 })
        });
        const data = await response.json();
        setPredictions(data.predictions);
    };

    return (
        <div>
            <input 
                value={course} 
                onChange={(e) => setCourse(e.target.value)}
                placeholder="Enter course title"
            />
            <button onClick={predictSkills}>Predict Skills</button>
            
            {predictions.map(pred => (
                <div key={pred.skill}>
                    {pred.skill}: {(pred.confidence * 100).toFixed(0)}%
                </div>
            ))}
        </div>
    );
}
```

### **Python Example:**
```python
import requests

def predict_skills(course_title):
    response = requests.post('http://localhost:5000/predict', json={
        'course_title': course_title,
        'top_k': 5
    })
    return response.json()

# Usage
result = predict_skills("Python Programming for Data Science")
for pred in result['predictions']:
    print(f"{pred['skill']}: {pred['confidence']:.0%}")
```

---

## 🌍 **Deploy to Production:**

### **Option 1: Simple Production Server (Gunicorn)**
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 api:app
```

### **Option 2: Docker**
Create `Dockerfile`:
```dockerfile
FROM python:3.13
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "api:app"]
```

Build and run:
```bash
docker build -t skill-gap-ai .
docker run -p 5000:5000 skill-gap-ai
```

### **Option 3: Deploy to Cloud**
- **Heroku**: `git push heroku main`
- **AWS Lambda**: Use Zappa
- **Google Cloud Run**: Deploy container
- **Azure App Service**: Deploy Flask app

---

## 🔒 **Security (For Production):**

Add to `api.py`:
```python
from flask_limiter import Limiter

limiter = Limiter(app, key_func=lambda: request.remote_addr)

@app.route('/predict', methods=['POST'])
@limiter.limit("100 per hour")
def predict_skills():
    # ... existing code
```

---

## 📊 **Current API Status:**

✅ **Running on:** `http://localhost:5000`  
✅ **Model loaded:** Yes  
✅ **Skills available:** 21  
✅ **Training examples:** 26,033  
✅ **Accuracy:** 60.3%  

---

## 🎨 **Customize the Demo:**

Edit `demo.html`:
- Change colors in `<style>` section
- Add more example courses
- Customize layout
- Add your company logo

---

## 🛑 **Stop the Server:**

Press `Ctrl+C` in the terminal where the API is running.

---

## 🚀 **Next Steps:**

1. **Open demo.html** in browser to test
2. **Integrate API** into your website
3. **Deploy to production** when ready
4. **Monitor usage** and retrain with more data

---

## 💡 **Tips:**

- The API supports **both English and Czech** automatically
- Use **CORS** to allow requests from your domain
- Add **authentication** for production use
- **Cache predictions** for frequently queried courses
- **Monitor API** performance and errors

---

## 📞 **API Test Commands:**

```bash
# Test health
curl http://localhost:5000/health

# Test prediction
curl -X POST http://localhost:5000/predict \
  -H "Content-Type: application/json" \
  -d '{"course_title": "Excel Data Analysis"}'

# Test with Czech
curl -X POST http://localhost:5000/predict \
  -H "Content-Type: application/json" \
  -d '{"course_title": "Kontingenční tabulky v Excelu"}'
```

---

Your AI is live and ready to use! 🎉
