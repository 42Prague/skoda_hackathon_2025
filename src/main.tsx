import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import './index.css'

// Import pages
import Landing from '@dashboard/pages/landing'
import Dashboard from '@dashboard/pages/dashboard'
import ManagerDashboard from '@dashboard/pages/manager_dashboard'
import MyQualifications from '@dashboard/pages/my_qualification'
import AIRecommendations from '@dashboard/pages/ai_recomandations'
import LearningPaths from '@dashboard/pages/learning_path'
import TeamSkillsOverview from '@dashboard/pages/team_skill_overview'
import Profile from '@dashboard/pages/profile'

// Import layout
import Layout from '@dashboard/layout.jsx'

// Page wrapper component
function PageWrapper({ children, pageName }: { children: React.ReactNode; pageName: string }) {
  return <Layout currentPageName={pageName}>{children}</Layout>
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/login" replace />} />
        <Route path="/login" element={
          <PageWrapper pageName="Login">
            <Landing />
          </PageWrapper>
        } />
        <Route path="/dashboard" element={
          <PageWrapper pageName="Dashboard">
            <Dashboard />
          </PageWrapper>
        } />
        <Route path="/manager-dashboard" element={
          <PageWrapper pageName="ManagerDashboard">
            <ManagerDashboard />
          </PageWrapper>
        } />
        <Route path="/my-qualifications" element={
          <PageWrapper pageName="MyQualifications">
            <MyQualifications />
          </PageWrapper>
        } />
        <Route path="/ai-recommendations" element={
          <PageWrapper pageName="AIRecommendations">
            <AIRecommendations />
          </PageWrapper>
        } />
        <Route path="/learning-paths" element={
          <PageWrapper pageName="LearningPaths">
            <LearningPaths />
          </PageWrapper>
        } />
        <Route path="/team-skills-overview" element={
          <PageWrapper pageName="TeamSkillsOverview">
            <TeamSkillsOverview />
          </PageWrapper>
        } />
        <Route path="/profile" element={
          <PageWrapper pageName="Profile">
            <Profile />
          </PageWrapper>
        } />
      </Routes>
    </BrowserRouter>
  </React.StrictMode>,
)
