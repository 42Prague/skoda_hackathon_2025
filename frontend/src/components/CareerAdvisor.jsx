import React, { useState } from 'react'
import axios from 'axios'
import './CareerAdvisor.css'

const API_BASE = '/api/v1/skills'

function CareerAdvisor() {
  const [employeeId, setEmployeeId] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [report, setReport] = useState(null)

  const fetchReport = async () => {
    if (!employeeId.trim()) return
    try {
      setLoading(true)
      setError(null)
      setReport(null)
      const res = await axios.get(`${API_BASE}/advisory/report/${employeeId.trim()}`)
      if (res.data.success) {
        setReport(res.data.data)
      } else {
        setError(res.data.message || 'Failed to get advisory report')
      }
    } catch (e) {
      setError(e.response?.data?.error || e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="career-advisor">
      <h2>🧭 Career Advisor</h2>
      <p>Generate an AI-driven skill assessment, pivot recommendations, and mentor suggestions.</p>

      <div className="advisor-controls">
        <input
          type="text"
          placeholder="Enter Employee ID..."
          value={employeeId}
          onChange={e => setEmployeeId(e.target.value)}
        />
        <button onClick={fetchReport} disabled={!employeeId || loading}>Generate Report</button>
      </div>

      {loading && <div className="loading">Analyzing employee...</div>}
      {error && <div className="error">{error}</div>}

      {report && (
        <div className="advisor-report">
          <section>
            <h3>Current Skill Assessment</h3>
            <p><strong>Cluster:</strong> {report.cluster_id}</p>
            <p><strong>Cluster Top Skills:</strong> {report.cluster_top_skills.map(([s,c])=>s).join(', ')}</p>
            <p><strong>Employee Top Skills:</strong> {report.employee_top_skills.join(', ') || 'N/A'}</p>
          </section>

          <section>
            <h3>Upskilling & Career Pivot</h3>
            {Object.entries(report.domains).map(([domainKey, info]) => (
              <div key={domainKey} className="domain-block">
                <h4>{domainKey.replace('_',' & ')}</h4>
                <p><strong>Target Skills:</strong> {info.target_skills.join(', ')}</p>
                <p><strong>Present:</strong> {info.present.join(', ') || 'None'}</p>
                <p><strong>Missing:</strong> {info.missing.join(', ') || 'None'}</p>
                {info.course_recommendations.length > 0 ? (
                  <div className="course-recs">
                    <p><strong>Recommended Courses:</strong></p>
                    <ul>
                      {info.course_recommendations.map((c,i)=>(
                        <li key={i}>
                          <span>{c.title || c.course_id}</span> — <em>{c.overlap_skills.join(', ')}</em>
                        </li>
                      ))}
                    </ul>
                  </div>
                ) : <p>No direct course matches for missing skills.</p>}
              </div>
            ))}
          </section>

          <section>
            <h3>Mentorship Matching</h3>
            {report.mentors.length > 0 ? (
              <ul>
                {report.mentors.map(m => (
                  <li key={m.employee_id}>ID {m.employee_id} (dist {m.distance}) overlap {m.overlap_skill_count} cluster {m.cluster}</li>
                ))}
              </ul>
            ) : <p>No nearby mentors found.</p>}
          </section>

          <section>
            <h3>Narrative Summary</h3>
            <pre className="narrative-block">{report.narrative}</pre>
          </section>
        </div>
      )}
    </div>
  )
}

export default CareerAdvisor
