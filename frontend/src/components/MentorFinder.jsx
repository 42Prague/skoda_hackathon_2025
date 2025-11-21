import React, { useState, useEffect } from 'react'
import axios from 'axios'
import './MentorFinder.css'

const API_BASE = '/api/v1/skills'

function MentorFinder() {
  const [mentors, setMentors] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [filters, setFilters] = useState({
    mentee_id: '',
    same_org_only: false,
    same_cluster_only: false,
    cluster_radius: '',
    target_position_id: '',
    min_qual_match_fraction: 0.0,
    min_skill_depth: '',
    min_job_coverage: '',
    max_skill_gap: '',
    min_recent_learning: '',
    skill_keywords: '',
    top_n: 20
  })

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({
      ...prev,
      [key]: value
    }))
  }

  const handleSearch = async () => {
    if (!filters.mentee_id) {
      setError('Please enter a mentee ID')
      return
    }

    try {
      setLoading(true)
      setError(null)

      // Prepare request data
      const requestData = {
        mentee_id: filters.mentee_id,
        same_org_only: filters.same_org_only,
        same_cluster_only: filters.same_cluster_only,
        target_position_id: filters.target_position_id || undefined,
        min_qual_match_fraction: parseFloat(filters.min_qual_match_fraction) || 0.0,
        min_skill_depth: filters.min_skill_depth ? parseFloat(filters.min_skill_depth) : undefined,
        min_job_coverage: filters.min_job_coverage ? parseFloat(filters.min_job_coverage) : undefined,
        max_skill_gap: filters.max_skill_gap ? parseFloat(filters.max_skill_gap) : undefined,
        min_recent_learning: filters.min_recent_learning ? parseFloat(filters.min_recent_learning) : undefined,
        skill_keywords: filters.skill_keywords 
          ? filters.skill_keywords.split(',').map(k => k.trim()).filter(k => k)
          : undefined,
        top_n: parseInt(filters.top_n) || 20,
        cluster_radius: filters.cluster_radius ? parseFloat(filters.cluster_radius) : undefined
      }

      const response = await axios.post(`${API_BASE}/mentors/find`, requestData)
      
      if (response.data.success) {
        setMentors(response.data.data || [])
      } else {
        setError(response.data.message || 'Failed to find mentors')
      }
    } catch (err) {
      setError(err.response?.data?.message || err.message || 'Failed to find mentors')
      console.error('Error finding mentors:', err)
      setMentors([])
    } finally {
      setLoading(false)
    }
  }

  const resetFilters = () => {
    setFilters({
      mentee_id: '',
      same_org_only: false,
      same_cluster_only: false,
      cluster_radius: '',
      target_position_id: '',
      min_qual_match_fraction: 0.0,
      min_skill_depth: '',
      min_job_coverage: '',
      max_skill_gap: '',
      min_recent_learning: '',
      skill_keywords: '',
      top_n: 20
    })
    setMentors([])
    setError(null)
  }

  const FilterSection = ({ title, children }) => (
    <div className="filter-section">
      <h3>{title}</h3>
      {children}
    </div>
  )

  const MentorCard = ({ mentor, rank }) => (
    <div className="mentor-card">
      <div className="mentor-header">
        <div className="mentor-rank">#{rank}</div>
        <div className="mentor-info">
          <h3>Employee {mentor.employee_id}</h3>
          {mentor.organization && (
            <span className="mentor-org">Organization: {mentor.organization}</span>
          )}
          {mentor.position_id && (
            <span className="mentor-position">Position: {mentor.position_id}</span>
          )}
        </div>
        <div className="mentor-score">
          <span className="score-label">Mentor Score</span>
          <span className="score-value">
            {mentor.mentor_score ? mentor.mentor_score.toFixed(2) : 'N/A'}
          </span>
        </div>
      </div>
      
      <div className="mentor-metrics">
        <div className="metric">
          <label>Cluster</label>
          <value>{mentor.cluster_kmeans || 'N/A'}</value>
        </div>
        <div className="metric">
          <label>Skill Depth</label>
          <value>{mentor.skill_depth ? mentor.skill_depth.toFixed(2) : 'N/A'}</value>
        </div>
        <div className="metric">
          <label>Skill Breadth</label>
          <value>{mentor.skill_breadth ? mentor.skill_breadth.toFixed(2) : 'N/A'}</value>
        </div>
        <div className="metric">
          <label>Job Coverage</label>
          <value>{mentor.job_requirement_coverage ? mentor.job_requirement_coverage.toFixed(2) : 'N/A'}</value>
        </div>
        <div className="metric">
          <label>Qualification Strength</label>
          <value>{mentor.qualification_strength ? mentor.qualification_strength.toFixed(2) : 'N/A'}</value>
        </div>
        <div className="metric">
          <label>Learning Intensity</label>
          <value>{mentor.learning_intensity ? mentor.learning_intensity.toFixed(2) : 'N/A'}</value>
        </div>
        <div className="metric">
          <label>Recent Learning</label>
          <value>{mentor.recent_learning_index ? mentor.recent_learning_index.toFixed(2) : 'N/A'}</value>
        </div>
        <div className="metric">
          <label>Skill Gap</label>
          <value>{mentor.skill_gap_index ? mentor.skill_gap_index.toFixed(2) : 'N/A'}</value>
        </div>
        {mentor.qual_match_fraction !== undefined && (
          <div className="metric">
            <label>Qual Match</label>
            <value>{(mentor.qual_match_fraction * 100).toFixed(1)}%</value>
          </div>
        )}
      </div>

      {mentor.top_skills_short && (
        <div className="mentor-skills">
          <label>Top Skills:</label>
          <span>{mentor.top_skills_short}</span>
        </div>
      )}
    </div>
  )

  return (
    <div className="mentor-finder">
      <div className="dashboard-header">
        <h2>Find Mentors</h2>
        <p>Search for suitable mentors based on various criteria</p>
      </div>

      <div className="filters-panel">
        <div className="filters-header">
          <h3>Search Filters</h3>
          <div className="filter-actions">
            <button onClick={handleSearch} className="search-button" disabled={loading}>
              {loading ? 'Searching...' : '🔍 Search Mentors'}
            </button>
            <button onClick={resetFilters} className="reset-button">
              🔄 Reset
            </button>
          </div>
        </div>

        <div className="filters-grid">
          <FilterSection title="Basic Information">
            <div className="filter-group">
              <label>Mentee ID *</label>
              <input
                type="text"
                value={filters.mentee_id}
                onChange={(e) => handleFilterChange('mentee_id', e.target.value)}
                placeholder="Enter employee ID"
                required
              />
            </div>
            <div className="filter-group">
              <label>Target Position ID</label>
              <input
                type="text"
                value={filters.target_position_id}
                onChange={(e) => handleFilterChange('target_position_id', e.target.value)}
                placeholder="Optional: position ID for qualification matching"
              />
            </div>
            <div className="filter-group">
              <label>Max Results</label>
              <input
                type="number"
                value={filters.top_n}
                onChange={(e) => handleFilterChange('top_n', e.target.value)}
                min="1"
                max="100"
              />
            </div>
          </FilterSection>

          <FilterSection title="Organization & Cluster Filters">
            <div className="filter-checkbox">
              <label>
                <input
                  type="checkbox"
                  checked={filters.same_org_only}
                  onChange={(e) => handleFilterChange('same_org_only', e.target.checked)}
                />
                Same Organization Only
              </label>
            </div>
            <div className="filter-checkbox">
              <label>
                <input
                  type="checkbox"
                  checked={filters.same_cluster_only}
                  onChange={(e) => handleFilterChange('same_cluster_only', e.target.checked)}
                />
                Same Skill Cluster Only
              </label>
            </div>
            <div className="filter-group">
              <label>Cluster Radius (UMAP distance)</label>
              <input
                type="number"
                value={filters.cluster_radius}
                onChange={(e) => handleFilterChange('cluster_radius', e.target.value)}
                placeholder="Optional: max distance in skill space"
                step="0.1"
              />
            </div>
          </FilterSection>

          <FilterSection title="Skill & Qualification Filters">
            <div className="filter-group">
              <label>Min Skill Depth</label>
              <input
                type="number"
                value={filters.min_skill_depth}
                onChange={(e) => handleFilterChange('min_skill_depth', e.target.value)}
                placeholder="0-10"
                min="0"
                max="10"
                step="0.1"
              />
            </div>
            <div className="filter-group">
              <label>Min Job Coverage</label>
              <input
                type="number"
                value={filters.min_job_coverage}
                onChange={(e) => handleFilterChange('min_job_coverage', e.target.value)}
                placeholder="0-10"
                min="0"
                max="10"
                step="0.1"
              />
            </div>
            <div className="filter-group">
              <label>Max Skill Gap</label>
              <input
                type="number"
                value={filters.max_skill_gap}
                onChange={(e) => handleFilterChange('max_skill_gap', e.target.value)}
                placeholder="0-10"
                min="0"
                max="10"
                step="0.1"
              />
            </div>
            <div className="filter-group">
              <label>Min Recent Learning</label>
              <input
                type="number"
                value={filters.min_recent_learning}
                onChange={(e) => handleFilterChange('min_recent_learning', e.target.value)}
                placeholder="0-10"
                min="0"
                max="10"
                step="0.1"
              />
            </div>
            <div className="filter-group">
              <label>Min Qualification Match Fraction</label>
              <input
                type="number"
                value={filters.min_qual_match_fraction}
                onChange={(e) => handleFilterChange('min_qual_match_fraction', e.target.value)}
                placeholder="0.0-1.0"
                min="0"
                max="1"
                step="0.1"
              />
            </div>
            <div className="filter-group">
              <label>Skill Keywords (comma-separated)</label>
              <input
                type="text"
                value={filters.skill_keywords}
                onChange={(e) => handleFilterChange('skill_keywords', e.target.value)}
                placeholder="e.g., python, ai, cloud"
              />
            </div>
          </FilterSection>
        </div>
      </div>

      {error && (
        <div className="error-message">
          <p>{error}</p>
        </div>
      )}

      {loading && (
        <div className="loading-message">
          <p>Searching for mentors...</p>
        </div>
      )}

      {!loading && mentors.length > 0 && (
        <div className="results-section">
          <div className="results-header">
            <h3>Found {mentors.length} Mentor Candidates</h3>
            <p>Sorted by mentor score (highest first)</p>
          </div>
          <div className="mentors-grid">
            {mentors.map((mentor, idx) => (
              <MentorCard key={mentor.employee_id || idx} mentor={mentor} rank={idx + 1} />
            ))}
          </div>
        </div>
      )}

      {!loading && mentors.length === 0 && !error && (
        <div className="no-results">
          <p>Enter a mentee ID and click "Search Mentors" to find suitable mentors.</p>
        </div>
      )}
    </div>
  )
}

export default MentorFinder

