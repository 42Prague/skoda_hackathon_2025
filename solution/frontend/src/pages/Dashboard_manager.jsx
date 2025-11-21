import { useState } from 'react';
import { 
  Box, 
  Container, 
  Typography, 
  Alert, 
  Button, 
  Tabs, 
  Tab,
  Paper
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import { useAuth } from '../context/AuthContext';
import TeamSkill from '../components/dashboards/TeamSkill';
import LearningRecommendationDashboard from '../components/dashboards/LearningRecommendationDashboard';
import TeamHeatmapDashboard from '../components/dashboards/TeamHeatmapDashboard';
import OrganizationHeatmapDashboard from '../components/dashboards/OrganizationHeatmapDashboard';
import TeamsHeatmapDashboard from '../components/dashboards/TeamsHeatmapDashboard';
import CareerPathDashboard from '../components/dashboards/CareerPathDashboard';
import SkillTrendsDashboard from '../components/dashboards/SkillTrendsDashboard';
import EmployeesSkillsDashboard from '../components/dashboards/EmployeesSkillsDashboard';
import EmployeeSkillDashboard from '../components/dashboards/EmployeeSkillDashboard';
import FindMyJobDashboard from '../components/dashboards/FindMyJobDashboard';

const Dashboard = () => {
  const { isHR, isManager, selectedUser, setSelectedUser, currentViewingUser } = useAuth();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState(0);
  const [employeeStats, setEmployeeStats] = useState([]);

  const handleBackToUsers = () => {
    setSelectedUser(null);
    navigate('/users');
  };

  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue);
  };

  // Determine which employee ID to use - prioritize id field
  const employeeId = selectedUser?.id || currentViewingUser?.id || currentViewingUser?.cardId || currentViewingUser?.username || 'PN-000001';

  // Separate tabs for HR and Managers
  const hrTabs = [
    { label: 'Organization Heatmap', value: 0 },
    { label: 'Skill Trends', value: 1 },
    { label: 'Find My Job', value: 2 },
  ];

  const managerTabs = [
    { label: 'Teams Heatmap', value: 0 },
    { label: 'Skill Trends', value: 1 },
    { label: 'Employee Skills', value: 2 },
  ];

  // Use HR tabs if user is HR, otherwise use manager tabs
  const tabs = isHR ? hrTabs : managerTabs;

  return (
    <Box
      sx={{
        minHeight: 'calc(100vh - 64px)',
        backgroundColor: 'background.default',
        color: 'text.primary',
      }}
    >
      <Container maxWidth="xl" sx={{ py: 4 }}>
        {(isHR || isManager) && selectedUser && (
          <Alert 
            severity="info" 
            sx={{ mb: 3 }}
            action={
              <Button
                size="small"
                variant="outlined"
                startIcon={<ArrowBackIcon />}
                onClick={handleBackToUsers}
                aria-label="Back to user management"
              >
                Back to Users
              </Button>
            }
          >
            Viewing dashboard for: <strong>{selectedUser.name}</strong> ({selectedUser.id})
          </Alert>
        )}

        <Typography 
          variant="h4" 
          component="h1" 
          sx={{ 
            mb: 1,
            color: 'text.primary',
            fontWeight: 600
          }}
        >
          Analytics Dashboard{selectedUser ? ` - ${selectedUser.name}` : ''}
        </Typography>
        <Typography 
          variant="body1" 
          sx={{ 
            color: 'text.secondary', 
            mb: 4 
          }}
        >
          {selectedUser 
            ? `Viewing analytics and performance metrics for ${selectedUser.name}.`
            : 'View your analytics and performance metrics.'}
        </Typography>

        {/* Tab Navigation */}
        <Paper 
          sx={{ 
            mb: 3,
            backgroundColor: 'background.paper',
            boxShadow: 2
          }}
        >
          <Tabs
            value={activeTab}
            onChange={handleTabChange}
            variant="scrollable"
            scrollButtons="auto"
            sx={{
              borderBottom: 1,
              borderColor: 'divider',
              '& .MuiTab-root': {
                color: 'text.secondary',
                '&.Mui-selected': {
                  color: 'brand.primary',
                },
              },
            }}
          >
            {tabs.map((tab) => (
              <Tab key={tab.value} label={tab.label} />
            ))}
          </Tabs>
        </Paper>

        {/* Tab Content */}
        <Box sx={{ mt: 3 }}>
          {(isHR || isManager) ? (
            // HR/Manager Dashboard Views
            <>
              {activeTab === 0 && (isHR ? <OrganizationHeatmapDashboard /> : <TeamsHeatmapDashboard />)}
              {activeTab === 1 && <SkillTrendsDashboard />}
              {activeTab === 2 && (isHR ? <FindMyJobDashboard /> : <EmployeesSkillsDashboard />)}
              {activeTab === 3 && <LearningRecommendationDashboard employeeId={employeeId} />}
            </>
          ) : (
            // Employee Dashboard Views
            <>
              {activeTab === 0 && <TeamSkill employeeId={employeeId} />}
              {activeTab === 1 && <LearningRecommendationDashboard employeeId={employeeId} />}
              {activeTab === 2 && (
                <CareerPathDashboard 
                  employeeId={employeeId} 
                  targetRole={selectedUser?.plannedPosition || currentViewingUser?.plannedPosition || 'Senior Engineer'}
                />
              )}
            </>
          )}
        </Box>
      </Container>
    </Box>
  );
};

export default Dashboard;

