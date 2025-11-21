import React, { useState, useEffect } from 'react'
import axios from 'axios'
import './EmployeeIndicatorsDashboard.css'
import { parseCSV, downloadCSV } from '../utils/csv'

const API_BASE = '/api/v1/skills'

function EmployeeIndicatorsDashboard() {
  const [diagrams, setDiagrams] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [sortBy, setSortBy] = useState('employee_id')
  const [sortOrder, setSortOrder] = useState('asc')

  useEffect(() => {
    fetchDiagrams()
  }, [])

  const fetchDiagrams = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await axios.get(`${API_BASE}/diagram/export`)
      if (response.data.success) {
        const csvText = response.data.data?.csv || ''
        const parsed = parseCSV(csvText)
        setDiagrams(parsed)
      } else {
        setError(response.data.message || 'Failed to load diagrams')
      }
    } catch (err) {
      setError(err.response?.data?.message || err.message || 'Failed to load employee diagrams')
      console.error('Error fetching diagrams:', err)
    } finally {
      setLoading(false)
    }
  }

  const filteredDiagrams = diagrams.filter(d => 
    d.employee_id?.toString().toLowerCase().includes(searchTerm.toLowerCase()) ||
    d.employee_name?.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const sortedDiagrams = [...filteredDiagrams].sort((a, b) => {
    const aVal = a[sortBy] || 0
    const bVal = b[sortBy] || 0
    
    if (sortOrder === 'asc') {
      return aVal > bVal ? 1 : -1
    } else {
      return aVal < bVal ? 1 : -1
    }
  })

  const IndicatorCard = ({ label, value, maxValue = 10 }) => {
    const percentage = Math.min((value / maxValue) * 100, 100)
    const color = percentage >= 70 ? '#4caf50' : percentage >= 40 ? '#ff9800' : '#f44336'
    
    return (
      <div className="indicator-card">
        <div className="indicator-header">
          <span className="indicator-label">{label}</span>
          <span className="indicator-value">{value.toFixed(2)} / {maxValue}</span>
        </div>
        <div className="indicator-bar">
          <div 
            className="indicator-fill" 
            style={{ width: `${percentage}%`, backgroundColor: color }}
          />
        </div>
      </div>
    )
  }

  if (loading) {
    return <div className="loading">Loading employee indicators...</div>
  }

  if (error) {
    return (
      <div className="error">
        <p>{error}</p>
        <button onClick={fetchDiagrams}>Retry</button>
      </div>
    )
  }

  return (
    <div className="indicators-dashboard">
      <div className="dashboard-header">
        <h2>Employee Skill Indicators</h2>
        <p>View skill analysis for all employees</p>
      </div>

      <div className="dashboard-controls">
        <input
          type="text"
          placeholder="Search by employee ID or name..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="search-input"
        />
        <div className="sort-controls">
          <label>Sort by:</label>
          <select value={sortBy} onChange={(e) => setSortBy(e.target.value)}>
            <option value="employee_id">Employee ID</option>
            <option value="breadth">Breadth</option>
            <option value="depth">Depth</option>
            <option value="job_requirement_coverage">Job Coverage</option>
            <option value="qualification_strength">Qualification Strength</option>
          </select>
          <button 
            onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
            className="sort-button"
          >
            {sortOrder === 'asc' ? '↑' : '↓'}
          </button>
        </div>
        <button
          onClick={async () => {
            try {
              const response = await axios.get(`${API_BASE}/diagram/export`)
              if (response.data.success) {
                const csvText = response.data.data?.csv || ''
                if (csvText) downloadCSV(csvText)
              }
            } catch (err) {
              console.error('Download failed', err)
            }
          }}
          className="download-button"
        >Download CSV</button>
      </div>

      <div className="indicators-grid">
        {sortedDiagrams.map((diagram) => (
          <div key={diagram.employee_id} className="employee-card">
            <div className="employee-header">
              <h3>Employee {diagram.employee_id}</h3>
              {diagram.employee_name && (
                <span className="employee-name">{diagram.employee_name}</span>
              )}
            </div>
            <div className="indicators-list">
              <IndicatorCard label="Breadth" value={diagram.breadth || 0} />
              <IndicatorCard label="Depth" value={diagram.depth || 0} />
              <IndicatorCard label="Learning Intensity" value={diagram.learning_intensity || 0} />
              <IndicatorCard label="Qualification Strength" value={diagram.qualification_strength || 0} />
              <IndicatorCard label="Job Coverage" value={diagram.job_requirement_coverage || 0} />
              <IndicatorCard label="Skill Gap" value={diagram.skill_gap_index || 0} />
              <IndicatorCard label="Recent Learning" value={diagram.recent_learning_index || 0} />
            </div>
          </div>
        ))}
      </div>

      {sortedDiagrams.length === 0 && (
        <div className="no-results">
          <p>No employees found matching your search.</p>
        </div>
      )}

      <div className="dashboard-footer">
        <p>Showing {sortedDiagrams.length} of {diagrams.length} employees</p>
      </div>
    </div>
  )
}

export default EmployeeIndicatorsDashboard

