import { useState } from 'react'
import './App.css'

function App() {
  const [question, setQuestion] = useState('')
  const [answer, setAnswer] = useState('')
  const [loading, setLoading] = useState(false)

  const askCoach = async () => {
    if (!question.trim()) return
    
    setLoading(true)
    try {
      const response = await fetch('/api/coach/ask', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ question })
      })
      
      const data = await response.json()
      setAnswer(data.answer || 'No response received')
    } catch (error) {
      setAnswer(`Error: ${error.message}`)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>🎓 Škoda AI Skill Coach</h1>
        <p>Your personal guide to skill development and career growth</p>
      </header>

      <main className="app-main">
        <div className="coach-interface">
          <div className="input-section">
            <textarea
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Ask me about skills, courses, or your learning path..."
              rows={4}
              disabled={loading}
            />
            <button 
              onClick={askCoach} 
              disabled={loading || !question.trim()}
              className="ask-button"
            >
              {loading ? 'Thinking...' : 'Ask Coach'}
            </button>
          </div>

          {answer && (
            <div className="answer-section">
              <h3>Coach's Response:</h3>
              <div className="answer-text">
                {answer}
              </div>
            </div>
          )}
        </div>

        <div className="info-section">
          <h3>Quick Actions</h3>
          <div className="action-cards">
            <div className="card">
              <h4>📊 View My Profile</h4>
              <p>See your skills, qualifications, and progress</p>
            </div>
            <div className="card">
              <h4>🎯 Learning Path</h4>
              <p>Get personalized course recommendations</p>
            </div>
            <div className="card">
              <h4>🔍 Explore Skills</h4>
              <p>Search and discover new skills</p>
            </div>
          </div>
        </div>
      </main>

      <footer className="app-footer">
        <p>Škoda AI Skill Coach v1.0.0 | Private & Secure</p>
      </footer>
    </div>
  )
}

export default App
