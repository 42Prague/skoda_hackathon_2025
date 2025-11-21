import { useState, useEffect } from 'react';
import { 
  Box, 
  Typography, 
  Card, 
  CircularProgress, 
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  useTheme,
  useMediaQuery,
  Tooltip
} from '@mui/material';
import { analyticsAPI } from '../../services/api';

const OrganizationHeatmapDashboard = () => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const isTablet = useMediaQuery(theme.breakpoints.down('md'));
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [heatmapData, setHeatmapData] = useState(null);

  useEffect(() => {
    const fetchOrganizationHeatmap = async () => {
      setLoading(true);
      setError(null);
      
      try {
        // Get all employees first
        const employees = await analyticsAPI.getEmployees();
        
        if (!employees || employees.length === 0) {
          throw new Error('No employees found');
        }
        
        // Get employee IDs for heatmap
        const employeeIds = employees.map(emp => emp.personal_number);
        
        // Fetch organization heatmap using team endpoint with all employees
        const heatmapData = await analyticsAPI.getTeamHeatmap('skoda-organization', employeeIds);
        
        // Transform members to include employee info
        const membersWithInfo = employees.map((emp, index) => ({
          id: emp.personal_number,
          name: emp.name,
          department: 'General', // Could be enhanced with employee details
          userName: emp.name,
        }));
        
        setHeatmapData({
          organizationId: 'skoda-organization',
          skills: heatmapData.skills || [],
          members: membersWithInfo,
          heatmapMatrix: heatmapData.heatmapMatrix || [],
        });
      } catch (err) {
        setError(err.message || 'Failed to fetch organization heatmap');
        console.error('Error fetching organization heatmap:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchOrganizationHeatmap();
  }, []);

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 400 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 2 }}>
        Error loading organization heatmap: {error}
      </Alert>
    );
  }

  if (!heatmapData) {
    return (
      <Alert severity="info" sx={{ mb: 2 }}>
        No organization data available.
      </Alert>
    );
  }

  const { skills = [], members = [], heatmapMatrix = [] } = heatmapData;

  // Helper function to get color based on skill level (0-5)
  const getHeatmapColor = (value, theme) => {
    if (value === 0) return theme.palette.onSurface?.os100 || theme.palette.grey[100];
    if (value <= 1) return theme.palette.warning?.light || theme.palette.warning.light;
    if (value <= 2) return theme.palette.info?.light || theme.palette.info.light;
    if (value <= 3) return theme.palette.success?.light || theme.palette.success.light;
    if (value <= 4) return theme.palette.success?.main || theme.palette.success.main;
    return theme.palette.success?.dark || theme.palette.success.dark;
  };

  // Helper function to get text color based on background
  const getTextColor = (value, theme) => {
    if (value === 0) return theme.palette.text.secondary;
    return theme.palette.text.primary;
  };

  return (
    <Box>
      <Typography 
        variant="h4" 
        component="h2" 
        sx={{ 
          mb: 1,
          color: 'text.primary',
          fontWeight: 600
        }}
      >
        ŠKODA Organization Heatmap
      </Typography>
      <Typography 
        variant="body1" 
        color="text.secondary"
        sx={{ mb: 4 }}
      >
        Skills overview across all ŠKODA employees
      </Typography>

      <Card sx={{ p: 3, backgroundColor: 'background.paper', boxShadow: 2 }}>
        <Box sx={{ mb: 3 }}>
          <Typography variant="h6" sx={{ mb: 2, color: 'text.primary', fontWeight: 600 }}>
            Skills Overview
          </Typography>
          <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', mb: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Box sx={{ width: 20, height: 20, backgroundColor: theme.palette.grey[100], border: 1, borderColor: 'divider' }} />
              <Typography variant="caption">No Skill (0)</Typography>
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Box sx={{ width: 20, height: 20, backgroundColor: theme.palette.warning?.light || theme.palette.warning.light }} />
              <Typography variant="caption">Beginner (1)</Typography>
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Box sx={{ width: 20, height: 20, backgroundColor: theme.palette.info?.light || theme.palette.info.light }} />
              <Typography variant="caption">Basic (2)</Typography>
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Box sx={{ width: 20, height: 20, backgroundColor: theme.palette.success?.light || theme.palette.success.light }} />
              <Typography variant="caption">Intermediate (3)</Typography>
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Box sx={{ width: 20, height: 20, backgroundColor: theme.palette.success?.main || theme.palette.success.main }} />
              <Typography variant="caption">Advanced (4)</Typography>
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Box sx={{ width: 20, height: 20, backgroundColor: theme.palette.success?.dark || theme.palette.success.dark }} />
              <Typography variant="caption">Expert (5)</Typography>
            </Box>
          </Box>
        </Box>

        <TableContainer component={Paper} variant="outlined" sx={{ maxHeight: { xs: 600, md: 800 }, overflow: 'auto' }}>
          <Table stickyHeader>
            <TableHead>
              <TableRow sx={{ backgroundColor: 'background.default' }}>
                <TableCell sx={{ fontWeight: 600, color: 'text.primary', minWidth: 250, position: 'sticky', left: 0, zIndex: 3, backgroundColor: 'background.default' }}>
                  Department
                </TableCell>
                {skills.map((skill, index) => (
                  <TableCell
                    key={index}
                    align="center"
                    sx={{
                      fontWeight: 600,
                      color: 'text.primary',
                      minWidth: 120,
                      padding: '20px 24px',
                      fontSize: '1rem',
                    }}
                  >
                    <Tooltip title={skill} arrow>
                      <Box sx={{ cursor: 'help' }}>
                        {skill.length > 15 ? `${skill.substring(0, 15)}...` : skill}
                      </Box>
                    </Tooltip>
                  </TableCell>
                ))}
              </TableRow>
            </TableHead>
            <TableBody>
              {members.map((member, memberIndex) => (
                <TableRow key={member.id} hover>
                  <TableCell
                    sx={{
                      fontWeight: 600,
                      position: 'sticky',
                      left: 0,
                      zIndex: 2,
                      backgroundColor: 'background.paper',
                      minWidth: 250,
                      fontFamily: 'monospace',
                      fontSize: '0.9rem',
                    }}
                  >
                    {member.department || 'S SE SEA'}
                  </TableCell>
                  {skills.map((skill, skillIndex) => {
                    const value = heatmapMatrix[memberIndex]?.[skillIndex] || 0;
                    return (
                      <TableCell
                        key={skillIndex}
                        align="center"
                        sx={{
                          backgroundColor: (theme) => getHeatmapColor(value, theme),
                          color: (theme) => getTextColor(value, theme),
                          fontWeight: value > 0 ? 600 : 400,
                          minWidth: 120,
                          padding: '20px 24px',
                          cursor: 'pointer',
                          '&:hover': {
                            opacity: 0.8,
                            transition: 'opacity 0.2s ease-in-out',
                          },
                          fontSize: '1.1rem',
                        }}
                      >
                        {value > 0 ? value : '-'}
                      </TableCell>
                    );
                  })}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </Card>
    </Box>
  );
};

export default OrganizationHeatmapDashboard;

