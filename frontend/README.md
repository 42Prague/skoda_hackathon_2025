# Skoda Skill Coach - Frontend

A React-based frontend application for the Skoda Skill Coach backend system.

## Features

1. **Employee Indicators Dashboard** - View skill analysis for all employees with visual indicators
2. **Skill Clustering Visualization** - Interactive visualization of employee skill clusters using UMAP and K-Means
3. **Mentor Finder** - Advanced search tool to find suitable mentors based on various criteria

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- Backend server running on port 5000

### Installation

```bash
cd frontend
npm install
```

### Development

```bash
npm run dev
```

The app will be available at `http://localhost:3000`

### Build

```bash
npm run build
```

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── EmployeeIndicatorsDashboard.jsx
│   │   ├── EmployeeIndicatorsDashboard.css
│   │   ├── ClusteringVisualization.jsx
│   │   ├── ClusteringVisualization.css
│   │   ├── MentorFinder.jsx
│   │   └── MentorFinder.css
│   ├── App.jsx
│   ├── App.css
│   ├── main.jsx
│   └── index.css
├── index.html
├── package.json
├── vite.config.js
└── README.md
```

## API Endpoints

The frontend connects to the following backend endpoints:

- `GET /api/v1/skills/diagrams/export` - Get all employee skill diagrams
- `GET /api/v1/skills/diagram/<employee_id>` - Get skill diagram for specific employee
- `GET /api/v1/skills/clustering/data` - Get clustering data for visualization
- `POST /api/v1/skills/mentors/find` - Find mentors based on filters

## Features Overview

### Employee Indicators Dashboard

- View all employees with their skill indicators
- Search by employee ID or name
- Sort by various metrics (breadth, depth, job coverage, etc.)
- Visual progress bars for each indicator

### Skill Clustering Visualization

- Interactive Plotly.js visualization
- Filter by cluster
- View top skills for each cluster
- Hover to see employee details

### Mentor Finder

- Comprehensive filter system:
  - Basic information (mentee ID, target position)
  - Organization and cluster filters
  - Skill and qualification filters
- Real-time search results
- Detailed mentor cards with metrics

## Technologies Used

- React 18
- Vite
- Plotly.js for visualization
- Axios for API calls
- CSS3 for styling

