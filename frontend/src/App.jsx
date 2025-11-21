import React, { useState } from 'react'
import './App.css'
import EmployeeIndicatorsDashboard from './components/EmployeeIndicatorsDashboard'
import ClusteringVisualization from './components/ClusteringVisualization'
import MentorFinder from './components/MentorFinder'
import CareerAdvisor from './components/CareerAdvisor'

function App() {
  const [activeTab, setActiveTab] = useState('indicators')

  return (
    <div className="App">
      <header className="app-header">
        <h1>🚗 Skoda Skill Coach</h1>
        <p>Employee Skills Analyzer & Mentor Finder</p>
      </header>

      <nav className="app-nav">
        <button
          className={activeTab === 'indicators' ? 'active' : ''}
          onClick={() => setActiveTab('indicators')}
        >
          📊 Employee Indicators
        </button>
        <button
          className={activeTab === 'clustering' ? 'active' : ''}
          onClick={() => setActiveTab('clustering')}
        >
          🎯 Skill Clustering
        </button>
        <button
          className={activeTab === 'mentors' ? 'active' : ''}
          onClick={() => setActiveTab('mentors')}
        >
          👥 Find Mentors
        </button>
        <button
          className={activeTab === 'advisor' ? 'active' : ''}
          onClick={() => setActiveTab('advisor')}
        >
          🧭 Career Advisor
        </button>
      </nav>

      <main className="app-main">
        {activeTab === 'indicators' && <EmployeeIndicatorsDashboard />}
        {activeTab === 'clustering' && <ClusteringVisualization />}
        {activeTab === 'mentors' && <MentorFinder />}
        {activeTab === 'advisor' && <CareerAdvisor />}
      </main>
    </div>
  )
}

export default App

