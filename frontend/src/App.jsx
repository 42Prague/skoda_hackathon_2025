import { useState, useEffect } from 'react'
import './App.css'

function App() {
  const [activeTab, setActiveTab] = useState('dashboard')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  
  // Dashboard state
  const [stats, setStats] = useState(null)
  
  // Employee profile state
  const [employeeId, setEmployeeId] = useState('')
  const [employeeProfile, setEmployeeProfile] = useState(null)
  
  // Skill search state
  const [skillQuery, setSkillQuery] = useState('')
  const [skillResults, setSkillResults] = useState([])
  
  // Learning path state
  const [learningPathId, setLearningPathId] = useState('')
  const [learningPath, setLearningPath] = useState(null)
  
  // AI Coach state
  const [coachQuestion, setCoachQuestion] = useState('')
  const [coachAnswer, setCoachAnswer] = useState('')
  const [chatHistory, setChatHistory] = useState([])

  // Load dashboard stats on mount
  useEffect(() => {
    if (activeTab === 'dashboard') {
      loadStats()
    }
  }, [activeTab])

  const loadStats = async () => {
    setLoading(true)
    setError('')
    try {
      const response = await fetch('/api/graph/stats')
      if (!response.ok) throw new Error('Failed to load statistics')
      const data = await response.json()
      setStats(data.stats)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const searchEmployee = async () => {
    if (!employeeId.trim()) return
    
    setLoading(true)
    setError('')
    setEmployeeProfile(null)
    
    try {
      const response = await fetch(`/api/skills/${employeeId}`)
      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Employee not found')
      }
      const data = await response.json()
      setEmployeeProfile(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const searchSkills = async () => {
    if (!skillQuery.trim()) return
    
    setLoading(true)
    setError('')
    setSkillResults([])
    
    try {
      const response = await fetch('/api/search/skills', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: skillQuery, top_k: 10 })
      })
      if (!response.ok) throw new Error('Search failed')
      const data = await response.json()
      setSkillResults(data.results || [])
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const generateLearningPath = async () => {
    if (!learningPathId.trim()) return
    
    setLoading(true)
    setError('')
    setLearningPath(null)
    
    try {
      const response = await fetch(`/api/coach/learning-path?personal_number=${encodeURIComponent(learningPathId)}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      })
      if (!response.ok) {
        const errorText = await response.text()
        let errorMsg = 'Failed to generate learning path'
        try {
          const errorData = JSON.parse(errorText)
          errorMsg = errorData.detail || errorMsg
        } catch {
          errorMsg = errorText || errorMsg
        }
        throw new Error(errorMsg)
      }
      const data = await response.json()
      setLearningPath(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const askCoach = async () => {
    if (!coachQuestion.trim()) return
    
    setLoading(true)
    setError('')
    
    // Add user question to chat
    const userMessage = { role: 'user', content: coachQuestion }
    setChatHistory(prev => [...prev, userMessage])
    
    try {
      const response = await fetch('/api/coach/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: coachQuestion })
      })
      if (!response.ok) throw new Error('Coach query failed')
      const data = await response.json()
      
      // Add coach response to chat
      const coachMessage = { role: 'assistant', content: data.answer }
      setChatHistory(prev => [...prev, coachMessage])
      setCoachAnswer(data.answer)
      setCoachQuestion('')
    } catch (err) {
      setError(err.message)
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

      <nav className="app-nav">
        <button 
          className={activeTab === 'dashboard' ? 'active' : ''}
          onClick={() => setActiveTab('dashboard')}
        >
          📊 Dashboard
        </button>
        <button 
          className={activeTab === 'profile' ? 'active' : ''}
          onClick={() => setActiveTab('profile')}
        >
          👤 Employee Profile
        </button>
        <button 
          className={activeTab === 'skills' ? 'active' : ''}
          onClick={() => setActiveTab('skills')}
        >
          🔍 Search Skills
        </button>
        <button 
          className={activeTab === 'learning' ? 'active' : ''}
          onClick={() => setActiveTab('learning')}
        >
          🎯 Learning Path
        </button>
        <button 
          className={activeTab === 'coach' ? 'active' : ''}
          onClick={() => setActiveTab('coach')}
        >
          💬 AI Coach
        </button>
      </nav>

      <main className="app-main">
        {error && (
          <div className="error-banner">
            ⚠️ {error}
          </div>
        )}

        {/* Dashboard Tab */}
        {activeTab === 'dashboard' && (
          <div className="tab-content">
            <h2>System Statistics</h2>
            {loading ? (
              <div className="loading">Loading statistics...</div>
            ) : stats ? (
              <div className="stats-grid">
                <div className="stat-card">
                  <h3>{stats.total_nodes || 0}</h3>
                  <p>Total Nodes</p>
                </div>
                <div className="stat-card">
                  <h3>{stats.total_edges || 0}</h3>
                  <p>Total Connections</p>
                </div>
                {stats.node_types && Object.entries(stats.node_types).map(([type, count]) => (
                  <div key={type} className="stat-card">
                    <h3>{count}</h3>
                    <p>{type.charAt(0).toUpperCase() + type.slice(1)}s</p>
                  </div>
                ))}
              </div>
            ) : (
              <div className="empty-state">
                <p>No statistics available. The system may still be initializing.</p>
                <button onClick={loadStats} className="btn-primary">Retry</button>
              </div>
            )}
          </div>
        )}

        {/* Employee Profile Tab */}
        {activeTab === 'profile' && (
          <div className="tab-content">
            <h2>Employee Profile Lookup</h2>
            <div className="search-section">
              <input
                type="text"
                value={employeeId}
                onChange={(e) => setEmployeeId(e.target.value)}
                placeholder="Enter employee ID (personal number)"
                onKeyPress={(e) => e.key === 'Enter' && searchEmployee()}
                disabled={loading}
              />
              <button 
                onClick={searchEmployee} 
                disabled={loading || !employeeId.trim()}
                className="btn-primary"
              >
                {loading ? 'Searching...' : 'Search'}
              </button>
            </div>

            {employeeProfile && (
              <div className="profile-results">
                <div className="profile-header">
                  <h3>Employee: {employeeProfile.personal_number}</h3>
                </div>

                <div className="profile-section">
                  <h4>Skills ({employeeProfile.skills?.length || 0})</h4>
                  {employeeProfile.skills && employeeProfile.skills.length > 0 ? (
                    <div className="items-list">
                      {employeeProfile.skills.map((skill, idx) => (
                        <div key={idx} className="item-card">
                          <strong>{skill.name || skill.skill_id}</strong>
                          {skill.description && <p>{skill.description}</p>}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="empty-text">No skills recorded</p>
                  )}
                </div>

                <div className="profile-section">
                  <h4>Qualifications ({employeeProfile.qualifications?.length || 0})</h4>
                  {employeeProfile.qualifications && employeeProfile.qualifications.length > 0 ? (
                    <div className="items-list">
                      {employeeProfile.qualifications.map((qual, idx) => (
                        <div key={idx} className="item-card">
                          <strong>{qual.name || qual.qualification_id}</strong>
                          {qual.start_date && <p className="date-info">Valid from: {qual.start_date}</p>}
                          {qual.end_date && <p className="date-info">Until: {qual.end_date}</p>}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="empty-text">No qualifications recorded</p>
                  )}
                </div>

                <div className="profile-section">
                  <h4>Missing Qualifications ({employeeProfile.missing_qualifications?.length || 0})</h4>
                  {employeeProfile.missing_qualifications && employeeProfile.missing_qualifications.length > 0 ? (
                    <div className="items-list warning">
                      {employeeProfile.missing_qualifications.map((qual, idx) => (
                        <div key={idx} className="item-card">
                          <strong>{qual.name || qual.qualification_id}</strong>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="empty-text success">All required qualifications obtained!</p>
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Skills Search Tab */}
        {activeTab === 'skills' && (
          <div className="tab-content">
            <h2>Search Skills</h2>
            <div className="search-section">
              <input
                type="text"
                value={skillQuery}
                onChange={(e) => setSkillQuery(e.target.value)}
                placeholder="Enter skill name or keyword..."
                onKeyPress={(e) => e.key === 'Enter' && searchSkills()}
                disabled={loading}
              />
              <button 
                onClick={searchSkills} 
                disabled={loading || !skillQuery.trim()}
                className="btn-primary"
              >
                {loading ? 'Searching...' : 'Search'}
              </button>
            </div>

            {skillResults.length > 0 && (
              <div className="results-section">
                <h3>Search Results ({skillResults.length})</h3>
                <div className="items-list">
                  {skillResults.map((skill, idx) => (
                    <div key={idx} className="item-card skill-card">
                      <strong>{skill.name || skill.skill_id}</strong>
                      {skill.description && <p>{skill.description}</p>}
                      {skill.similarity && (
                        <span className="similarity-badge">
                          {(skill.similarity * 100).toFixed(0)}% match
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Learning Path Tab */}
        {activeTab === 'learning' && (
          <div className="tab-content">
            <h2>Generate Learning Path</h2>
            <div className="search-section">
              <input
                type="text"
                value={learningPathId}
                onChange={(e) => setLearningPathId(e.target.value)}
                placeholder="Enter employee ID"
                onKeyPress={(e) => e.key === 'Enter' && generateLearningPath()}
                disabled={loading}
              />
              <button 
                onClick={generateLearningPath} 
                disabled={loading || !learningPathId.trim()}
                className="btn-primary"
              >
                {loading ? 'Generating...' : 'Generate'}
              </button>
            </div>

            {learningPath && (
              <div className="learning-path-results">
                <div className="path-header">
                  <h3>Learning Path for Employee: {learningPath.personal_number}</h3>
                  <p className="target-role">🎯 Target Role: {learningPath.target_role}</p>
                </div>

                <div className="path-section">
                  <h4>Current Skills</h4>
                  {learningPath.current_skills && learningPath.current_skills.length > 0 ? (
                    <div className="tags">
                      {learningPath.current_skills.map((skill, idx) => (
                        <span key={idx} className="tag success">{skill}</span>
                      ))}
                    </div>
                  ) : (
                    <p className="empty-text">No skills recorded</p>
                  )}
                </div>

                <div className="path-section">
                  <h4>Missing Qualifications</h4>
                  {learningPath.missing_qualifications && learningPath.missing_qualifications.length > 0 ? (
                    <div className="tags">
                      {learningPath.missing_qualifications.map((qual, idx) => (
                        <span key={idx} className="tag warning">{qual}</span>
                      ))}
                    </div>
                  ) : (
                    <p className="empty-text success">No missing qualifications</p>
                  )}
                </div>

                <div className="path-section">
                  <h4>Recommended Learning Path</h4>
                  <div className="learning-path-content">
                    {learningPath.learning_path}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* AI Coach Tab */}
        {activeTab === 'coach' && (
          <div className="tab-content coach-tab">
            <h2>AI Coach Assistant</h2>
            
            <div className="chat-container">
              <div className="chat-messages">
                {chatHistory.length === 0 ? (
                  <div className="empty-chat">
                    <p>👋 Hello! I'm your AI Skill Coach.</p>
                    <p>Ask me anything about skills, courses, or your learning path!</p>
                  </div>
                ) : (
                  chatHistory.map((message, idx) => (
                    <div 
                      key={idx} 
                      className={`chat-message ${message.role}`}
                    >
                      <div className="message-avatar">
                        {message.role === 'user' ? '👤' : '🤖'}
                      </div>
                      <div className="message-content">
                        {message.content}
                      </div>
                    </div>
                  ))
                )}
                {loading && (
                  <div className="chat-message assistant">
                    <div className="message-avatar">🤖</div>
                    <div className="message-content typing">Thinking...</div>
                  </div>
                )}
              </div>

              <div className="chat-input">
                <textarea
                  value={coachQuestion}
                  onChange={(e) => setCoachQuestion(e.target.value)}
                  placeholder="Ask me about skills, courses, or your learning path..."
                  rows={3}
                  disabled={loading}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault()
                      askCoach()
                    }
                  }}
                />
                <button 
                  onClick={askCoach} 
                  disabled={loading || !coachQuestion.trim()}
                  className="btn-primary"
                >
                  {loading ? '...' : 'Send'}
                </button>
              </div>
            </div>
          </div>
        )}
      </main>

      <footer className="app-footer">
        <p>Škoda AI Skill Coach v1.0.0 | Private & Secure</p>
      </footer>
    </div>
  )
}

export default App
