# Frontend Setup Guide

This guide will help you set up and run the frontend application for the Skoda Skill Coach system.

## Prerequisites

1. **Backend Server**: Make sure the Flask backend is running on port 5000
2. **Node.js**: Version 18 or higher
3. **npm**: Comes with Node.js

## Quick Start

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Start Development Server

```bash
npm run dev
```

The frontend will be available at `http://localhost:3000`

### 3. Start Backend Server

In a separate terminal:

```bash
cd srcs/server
python run.py
```

The backend should be running on `http://localhost:5000`

## Features

### 1. Employee Indicators Dashboard
- View all employees with their skill indicators
- Search and filter employees
- Visual progress bars for each metric

### 2. Skill Clustering Visualization
- Interactive 2D visualization of employee skill clusters
- Filter by cluster
- View top skills per cluster
- Requires `employee_skill_positions.csv` (run `employee_skill_model.py` first)

### 3. Mentor Finder
- Advanced search with multiple filters
- Find suitable mentors based on:
  - Organization and cluster
  - Skill depth, breadth, coverage
  - Qualification matching
  - Recent learning activity
- Requires data files from `mentor_filter.py`

## Data Requirements

For full functionality, you need to generate the following data files:

1. **For Clustering Visualization**:
   ```bash
   cd srcs/server/data_scripts
   python employee_skill_model.py
   ```
   This generates `employee_skill_positions.csv`

2. **For Mentor Finder**:
   - `employee_skill_positions.csv` (from above)
   - `employee_diagrams.csv` (needs to be generated)
   - `ZHRPD_VZD_STA_016_RE_RHRHAZ00.xlsx` (SAP qualifications)
   - `ZPE_KOM_KVAL.xlsx` (Position requirements)

## Troubleshooting

### CORS Errors
If you see CORS errors, make sure:
- Flask-CORS is installed: `pip install flask-cors`
- Backend is running on port 5000
- Frontend is running on port 3000

### Missing Data Files
- Check that required CSV/Excel files exist
- Run the data generation scripts first
- Check file paths in the backend API routes

### API Connection Issues
- Verify backend is running: `curl http://localhost:5000/api/v1/skills/diagrams/export`
- Check browser console for errors
- Verify proxy settings in `vite.config.js`

## Production Build

To create a production build:

```bash
cd frontend
npm run build
```

The built files will be in the `dist/` directory.

## Project Structure

```
frontend/
├── src/
│   ├── components/          # React components
│   │   ├── EmployeeIndicatorsDashboard.jsx
│   │   ├── ClusteringVisualization.jsx
│   │   └── MentorFinder.jsx
│   ├── App.jsx             # Main app component
│   └── main.jsx            # Entry point
├── package.json
└── vite.config.js          # Vite configuration
```

## API Endpoints Used

- `GET /api/v1/skills/diagrams/export` - All employee indicators
- `GET /api/v1/skills/diagram/<id>` - Single employee diagram
- `GET /api/v1/skills/clustering/data` - Clustering visualization data
- `POST /api/v1/skills/mentors/find` - Find mentors with filters

## Notes

- The frontend uses Vite for fast development
- Plotly.js is used for interactive visualizations
- All API calls are proxied through Vite dev server
- The UI is responsive and works on mobile devices

