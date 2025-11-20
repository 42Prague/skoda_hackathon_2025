import React, { useState, useEffect } from 'react'
import Plot from 'react-plotly.js'
import axios from 'axios'
import './ClusteringVisualization.css'

const API_BASE = '/api/v1/skills'

function ClusteringVisualization() {
  const [clusteringData, setClusteringData] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [selectedCluster, setSelectedCluster] = useState(null)
  const [hoveredEmployee, setHoveredEmployee] = useState(null)

  useEffect(() => {
    fetchClusteringData()
  }, [])

  const fetchClusteringData = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await axios.get(`${API_BASE}/clustering/data`)
      if (response.data.success) {
        setClusteringData(response.data.data || [])
      } else {
        setError(response.data.message || 'Failed to load clustering data')
      }
    } catch (err) {
      setError(err.response?.data?.message || err.message || 'Failed to load clustering data')
      console.error('Error fetching clustering data:', err)
    } finally {
      setLoading(false)
    }
  }

  // Group data by cluster
  const clusters = {}
  clusteringData.forEach(emp => {
    const cluster = emp.cluster_kmeans || 'unknown'
    if (!clusters[cluster]) {
      clusters[cluster] = []
    }
    clusters[cluster].push(emp)
  })

  // Prepare plot data
  const plotData = Object.keys(clusters).map((clusterId, idx) => {
    const clusterEmps = clusters[clusterId]
    const colors = [
      '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
      '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
    ]
    const color = colors[idx % colors.length]

    return {
      x: clusterEmps.map(e => e.x),
      y: clusterEmps.map(e => e.y),
      mode: 'markers',
      type: 'scatter',
      name: `Cluster ${clusterId}`,
      text: clusterEmps.map(e => 
        `Employee: ${e.employee_id}<br>` +
        `Skills: ${e.skill?.split(' ').slice(0, 5).join(', ') || 'N/A'}`
      ),
      hovertemplate: '%{text}<extra></extra>',
      marker: {
        size: 8,
        color: color,
        opacity: selectedCluster === null || selectedCluster === clusterId ? 0.7 : 0.2,
        line: {
          width: 1,
          color: 'rgba(0,0,0,0.3)'
        }
      }
    }
  })

  // Filter data by selected cluster
  const filteredData = selectedCluster
    ? clusteringData.filter(e => e.cluster_kmeans === selectedCluster)
    : clusteringData

  // Get top skills for selected cluster
  const getClusterTopSkills = (clusterId) => {
    const clusterEmps = clusteringData.filter(e => e.cluster_kmeans === clusterId)
    const skillCounts = {}
    
    clusterEmps.forEach(emp => {
      if (emp.top_skills && Array.isArray(emp.top_skills)) {
        emp.top_skills.forEach(([skill, score]) => {
          if (!skillCounts[skill]) {
            skillCounts[skill] = { count: 0, totalScore: 0 }
          }
          skillCounts[skill].count++
          skillCounts[skill].totalScore += score || 0
        })
      }
    })

    return Object.entries(skillCounts)
      .map(([skill, data]) => ({
        skill,
        count: data.count,
        avgScore: data.totalScore / data.count
      }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 10)
  }

  const layout = {
    title: {
      text: 'Employee Skill Clusters (UMAP + K-Means)',
      font: { size: 20, color: '#333' }
    },
    xaxis: {
      title: 'UMAP Dimension 1',
      showgrid: true,
      gridcolor: '#f0f0f0'
    },
    yaxis: {
      title: 'UMAP Dimension 2',
      showgrid: true,
      gridcolor: '#f0f0f0'
    },
    hovermode: 'closest',
    plot_bgcolor: 'white',
    paper_bgcolor: 'white',
    legend: {
      orientation: 'v',
      x: 1.02,
      y: 1
    },
    margin: { l: 60, r: 150, t: 60, b: 60 }
  }

  if (loading) {
    return <div className="loading">Loading clustering data...</div>
  }

  if (error) {
    return (
      <div className="error">
        <p>{error}</p>
        <button onClick={fetchClusteringData}>Retry</button>
      </div>
    )
  }

  if (clusteringData.length === 0) {
    return (
      <div className="no-data">
        <p>No clustering data available. Please run the employee_skill_model.py script first.</p>
      </div>
    )
  }

  const topSkills = selectedCluster ? getClusterTopSkills(selectedCluster) : []

  return (
    <div className="clustering-visualization">
      <div className="dashboard-header">
        <h2>Employee Skill Clustering</h2>
        <p>Visualize employee skill similarities using UMAP and K-Means clustering</p>
      </div>

      <div className="cluster-controls">
        <div className="cluster-filter">
          <label>Filter by Cluster:</label>
          <select
            value={selectedCluster || ''}
            onChange={(e) => setSelectedCluster(e.target.value || null)}
          >
            <option value="">All Clusters</option>
            {Object.keys(clusters).sort().map(clusterId => (
              <option key={clusterId} value={clusterId}>
                Cluster {clusterId} ({clusters[clusterId].length} employees)
              </option>
            ))}
          </select>
        </div>
        <div className="cluster-stats">
          <span>Total Employees: {clusteringData.length}</span>
          <span>Clusters: {Object.keys(clusters).length}</span>
          {selectedCluster && (
            <span>Selected: {filteredData.length} employees</span>
          )}
        </div>
      </div>

      <div className="visualization-container">
        <div className="plot-container">
          <Plot
            data={plotData}
            layout={layout}
            style={{ width: '100%', height: '600px' }}
            config={{
              responsive: true,
              displayModeBar: true,
              modeBarButtonsToRemove: ['lasso2d', 'select2d']
            }}
            onUpdate={(figure) => {
              // Handle plot updates if needed
            }}
          />
        </div>

        {selectedCluster && topSkills.length > 0 && (
          <div className="cluster-details">
            <h3>Top Skills in Cluster {selectedCluster}</h3>
            <div className="top-skills-list">
              {topSkills.map((item, idx) => (
                <div key={idx} className="skill-item">
                  <span className="skill-name">{item.skill}</span>
                  <span className="skill-count">
                    {item.count} employees (avg score: {item.avgScore.toFixed(2)})
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      <div className="info-section">
        <h3>About This Visualization</h3>
        <p>
          This visualization uses UMAP (Uniform Manifold Approximation and Projection) to reduce
          the dimensionality of employee skill vectors and K-Means clustering to group similar employees.
          Each point represents an employee, and colors indicate different skill clusters.
        </p>
        <ul>
          <li><strong>UMAP Dimension 1 & 2:</strong> Reduced dimensional representation of skill vectors</li>
          <li><strong>Clusters:</strong> Groups of employees with similar skill profiles</li>
          <li><strong>Hover:</strong> See employee ID and top skills</li>
          <li><strong>Filter:</strong> Click on a cluster in the dropdown to focus on it</li>
        </ul>
      </div>
    </div>
  )
}

export default ClusteringVisualization

