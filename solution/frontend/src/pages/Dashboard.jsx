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
import EmployeeSkillDashboard from '../components/dashboards/EmployeeSkillDashboard';
import CourseHistoryDashboard from '../components/dashboards/CourseHistoryDashboard';
import CareerPathDashboard from '../components/dashboards/CareerPathDashboard';

const Dashboard = () => {
  const { isHR, isManager, selectedUser, setSelectedUser, currentViewingUser } = useAuth();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState(0);

  const handleBackToUsers = () => {
    setSelectedUser(null);
    navigate('/users');
  };

  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue);
  };

  // Determine which employee ID to use - prioritize personalNumber (database field)
  // Strip any suffix like ":1" that might be appended
  const getEmployeeId = () => {
    // Check selectedUser first (for HR/Manager viewing another user)
    // Prioritize personalNumber as it maps to the database personal_number field
    let id = selectedUser?.personalNumber || selectedUser?.id;
    if (!id || id === 'id' || id === 'undefined') {
      // Fallback to currentViewingUser
      id = currentViewingUser?.personalNumber || currentViewingUser?.id;
      if (!id || id === 'id' || id === 'undefined') {
        id = currentViewingUser?.cardId;
        if (!id || id === 'id' || id === 'undefined') {
          id = currentViewingUser?.username;
          if (!id || id === 'id' || id === 'undefined') {
            id = 'PN-000001'; // Default fallback
          }
        }
      }
    }
    
    // Convert to string and remove any suffix after colon (e.g., "6249:1" -> "6249")
    const cleanId = id.toString().split(':')[0].trim();
    
    // Final validation - ensure we don't have "id" as the value
    if (!cleanId || cleanId === 'id' || cleanId === 'undefined') {
      console.error('Dashboard: Invalid employeeId detected:', { selectedUser, currentViewingUser, cleanId });
      return 'PN-000001'; // Safe fallback
    }
    
    console.log('Dashboard: Using employeeId:', cleanId, 'from:', { 
      selectedUser: selectedUser ? { id: selectedUser.id, personalNumber: selectedUser.personalNumber } : null,
      currentViewingUser: currentViewingUser ? { id: currentViewingUser.id, personalNumber: currentViewingUser.personalNumber } : null
    });
    
    return cleanId;
  };
  const employeeId = getEmployeeId();

  // Define tabs based on user role
  const employeeTabs = [
    { label: 'My Skills', value: 0 },
    { label: 'History Course', value: 1 },
    { label: 'Career Path', value: 2 },
  ];

  const tabs = employeeTabs;

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
          {activeTab === 0 && <EmployeeSkillDashboard employeeId={employeeId} />}
          {activeTab === 1 && <CourseHistoryDashboard employeeId={employeeId} />}
          {activeTab === 2 && (
            <CareerPathDashboard 
              employeeId={employeeId} 
              targetRole={selectedUser?.plannedPosition || currentViewingUser?.plannedPosition || 'Senior Engineer'}
            />
          )}
        </Box>
      </Container>
    </Box>
  );
};

export default Dashboard;

