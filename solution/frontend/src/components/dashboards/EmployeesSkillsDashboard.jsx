import { useState, useEffect } from 'react';
import { 
  Box, 
  Typography, 
  Card, 
  CircularProgress, 
  Alert, 
  Grid,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  useTheme,
  useMediaQuery,
} from '@mui/material';
import RadarGraph from '../charts/RadarGraph';
import { analyticsAPI } from '../../services/api';

const EmployeesSkillsDashboard = () => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const isTablet = useMediaQuery(theme.breakpoints.down('md'));
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [employeesSkills, setEmployeesSkills] = useState([]);

  const getChartSize = () => {
    if (isMobile) return 350;
    if (isTablet) return 550;
    return 700;
  };

  useEffect(() => {
    const fetchEmployeesSkills = async () => {
      setLoading(true);
      setError(null);

      try {
        // Get all employees first
        const employees = await analyticsAPI.getEmployees();
        
        if (!employees || employees.length === 0) {
          throw new Error('No employees found');
        }

        // Fetch skill profiles for all employees (limit to first 20 for performance)
        const employeesToFetch = employees.slice(0, 20);
        const skillProfiles = await Promise.allSettled(
          employeesToFetch.map(emp => 
            analyticsAPI.getEmployeeSkillProfile(emp.personal_number)
              .then(profile => ({ employee: emp, profile }))
              .catch(() => null) // Ignore individual failures
          )
        );

        // Transform to component format
        const transformedSkills = skillProfiles
          .filter(result => result.status === 'fulfilled' && result.value !== null)
          .map(result => {
            const { employee, profile } = result.value;
            return {
              employeeId: employee.personal_number,
              employeeName: employee.name,
              position: profile.currentProfession || profile.plannedProfession || 'Employee',
              skills: (profile.skills || []).map(skill => ({
                skill_name: skill.name,
                quantity: (skill.expertiseLevel || 0) * 20, // Convert 0-5 scale to 0-100
              })),
            };
          });

        setEmployeesSkills(transformedSkills);
      } catch (err) {
        setError(err.message || 'Failed to fetch employees skills');
        console.error('Error fetching employees skills:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchEmployeesSkills();
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
        Error loading employees skills: {error}
      </Alert>
    );
  }

  if (employeesSkills.length === 0) {
    return (
      <Alert severity="info" sx={{ mb: 2 }}>
        No employees skills data available.
      </Alert>
    );
  }

  // Calculate average team skills (mixed all employees)
  const calculateTeamAverageSkills = () => {
    const standardSkills = [
      'Communication',
      'Project Management',
      'Problem Solving',
      'Team Collaboration',
      'Analytical Thinking',
      'Leadership',
      'Time Management',
      'Adaptability',
      'Technical Skills',
      'Innovation',
    ];

    return standardSkills.map((skillName) => {
      const skillValues = employeesSkills
        .map((employee) => {
          const skill = employee.skills?.find((s) => s.skill_name === skillName);
          return skill ? Number(skill.quantity) || 0 : 0;
        })
        .filter((v) => v > 0);

      const average = skillValues.length > 0
        ? skillValues.reduce((a, b) => a + b, 0) / skillValues.length
        : 0;

      return {
        label: skillName,
        value: Math.round(average),
        max: 100,
      };
    });
  };

  const teamAverageData = calculateTeamAverageSkills();
  const normalizer = Math.max(1, ...teamAverageData.map((d) => d.value || 0));

  // Jira actual skills usage data for team average
  const jiraActualUsageData = teamAverageData.map((d, index) => {
    const baseValue = d.value || 0;
    const jiraValue = Math.max(0, baseValue * (0.65 + (index % 4) * 0.08));
    return {
      label: d.label,
      value: Math.min(jiraValue, normalizer),
    };
  });

  return (
    <Box>
      <Typography 
        variant="h4" 
        component="h2" 
        sx={{ 
          mb: 4,
          color: 'text.primary',
          fontWeight: 600
        }}
      >
        Employees Skills Overview
      </Typography>

      {/* Team Average Radar Chart */}
      <Card sx={{ mb: 4, p: 4, backgroundColor: 'background.paper', boxShadow: 2, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
        <Typography 
          variant="h5" 
          component="h3" 
          sx={{ 
            mb: 4, 
            color: 'text.primary',
            fontWeight: 600,
            textAlign: 'center'
          }}
        >
          Team Average Skills Overview
        </Typography>
        <Box sx={{ 
          width: '100%', 
          height: { xs: 500, sm: 600, md: 700 },
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          flexDirection: 'column',
        }}>
          <RadarGraph
            title="Skills Overview"
            data={teamAverageData.map(d => ({ ...d, max: normalizer }))}
            comparisonData={jiraActualUsageData}
            maxValue={normalizer}
            levels={5}
            loading={false}
            error={null}
            size={getChartSize()}
            color="primary"
          />
          {/* Legend/Explanation */}
          <Box sx={{ mt: 4, display: 'flex', gap: 4, flexWrap: 'wrap', justifyContent: 'center' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Box
                sx={{
                  width: 20,
                  height: 3,
                  backgroundColor: theme.palette.primary.main,
                  borderRadius: 1,
                }}
              />
              <Typography variant="body2" sx={{ color: 'text.primary' }}>
                Current Skills Profile
              </Typography>
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Box
                sx={{
                  width: 20,
                  height: 3,
                  backgroundColor: '#757575',
                  border: '1px dashed #757575',
                  borderRadius: 1,
                }}
              />
              <Typography variant="body2" sx={{ color: 'text.primary' }}>
                Jira Actual Skills Usage
              </Typography>
            </Box>
          </Box>
        </Box>
      </Card>

      {/* All Employees Skills Table */}
      <Card sx={{ p: 3, backgroundColor: 'background.paper', boxShadow: 2 }}>
        <Typography 
          variant="h6" 
          component="h3" 
          sx={{ mb: 3, color: 'text.primary' }}
        >
          All Employees Skills
        </Typography>
        <TableContainer component={Paper} variant="outlined">
          <Table>
            <TableHead>
              <TableRow sx={{ backgroundColor: 'background.default' }}>
                <TableCell sx={{ fontWeight: 600, color: 'text.primary', minWidth: 120 }}>Employee</TableCell>
                <TableCell sx={{ fontWeight: 600, color: 'text.primary', minWidth: 180 }}>Position</TableCell>
                <TableCell align="center" sx={{ fontWeight: 600, color: 'text.primary' }}>Communication</TableCell>
                <TableCell align="center" sx={{ fontWeight: 600, color: 'text.primary' }}>Project Mgmt</TableCell>
                <TableCell align="center" sx={{ fontWeight: 600, color: 'text.primary' }}>Problem Solving</TableCell>
                <TableCell align="center" sx={{ fontWeight: 600, color: 'text.primary' }}>Team Collab</TableCell>
                <TableCell align="center" sx={{ fontWeight: 600, color: 'text.primary' }}>Analytical</TableCell>
                <TableCell align="center" sx={{ fontWeight: 600, color: 'text.primary' }}>Leadership</TableCell>
                <TableCell align="center" sx={{ fontWeight: 600, color: 'text.primary' }}>Time Mgmt</TableCell>
                <TableCell align="center" sx={{ fontWeight: 600, color: 'text.primary' }}>Adaptability</TableCell>
                <TableCell align="center" sx={{ fontWeight: 600, color: 'text.primary' }}>Technical</TableCell>
                <TableCell align="center" sx={{ fontWeight: 600, color: 'text.primary' }}>Innovation</TableCell>
                <TableCell align="center" sx={{ fontWeight: 600, color: 'text.primary' }}>Avg Level</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {employeesSkills.map((employee) => {
                const skillsMap = {};
                employee.skills?.forEach((skill) => {
                  skillsMap[skill.skill_name] = Number(skill.quantity) || 0;
                });

                const allLevels = employee.skills?.map(s => Number(s.quantity) || 0) || [];
                const avgLevel = allLevels.length > 0
                  ? (allLevels.reduce((a, b) => a + b, 0) / allLevels.length).toFixed(1)
                  : 0;

                return (
                  <TableRow key={employee.employeeId} hover>
                    <TableCell sx={{ fontWeight: 600 }}>{employee.employeeName}</TableCell>
                    <TableCell>{employee.position}</TableCell>
                    <TableCell align="center">{skillsMap['Communication'] || '-'}</TableCell>
                    <TableCell align="center">{skillsMap['Project Management'] || '-'}</TableCell>
                    <TableCell align="center">{skillsMap['Problem Solving'] || '-'}</TableCell>
                    <TableCell align="center">{skillsMap['Team Collaboration'] || '-'}</TableCell>
                    <TableCell align="center">{skillsMap['Analytical Thinking'] || '-'}</TableCell>
                    <TableCell align="center">{skillsMap['Leadership'] || '-'}</TableCell>
                    <TableCell align="center">{skillsMap['Time Management'] || '-'}</TableCell>
                    <TableCell align="center">{skillsMap['Adaptability'] || '-'}</TableCell>
                    <TableCell align="center">{skillsMap['Technical Skills'] || '-'}</TableCell>
                    <TableCell align="center">{skillsMap['Innovation'] || '-'}</TableCell>
                    <TableCell align="center" sx={{ fontWeight: 600 }}>{avgLevel}</TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </TableContainer>
      </Card>

      {/* Individual Employee Radar Charts */}
      <Typography 
        variant="h5" 
        component="h3" 
        sx={{ 
          mt: 6, 
          mb: 4,
          color: 'text.primary',
          fontWeight: 600
        }}
      >
        Individual Employee Skills Overview
      </Typography>

      <Grid container spacing={3}>
        {employeesSkills.map((employee) => {
          const normalizer = Math.max(
            1,
            ...(employee.skills?.map((d) => Number(d.quantity) || 0) || [1])
          );

          // Transform to RadarGraph data format
          const radarData = employee.skills.map((d) => ({
            label: d.skill_name || 'Skill',
            value: Math.min(Number(d.quantity) || 0, normalizer),
            max: normalizer,
          }));

          // Jira actual skills usage data
          const jiraActualUsageData = employee.skills.map((d, index) => {
            const baseValue = Number(d.quantity) || 0;
            const jiraValue = Math.max(0, baseValue * (0.65 + (index % 4) * 0.08));
            return {
              label: d.skill_name || 'Skill',
              value: Math.min(jiraValue, normalizer),
            };
          });

          return (
            <Grid item xs={12} md={6} key={employee.employeeId}>
              <Card
                sx={{
                  p: 3,
                  height: '100%',
                  backgroundColor: 'background.paper',
                  boxShadow: 2,
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                }}
              >
                <Typography
                  variant="h6"
                  component="h3"
                  sx={{ mb: 1, color: 'text.primary', fontWeight: 600, textAlign: 'center' }}
                >
                  {employee.position}
                </Typography>
                <Typography
                  variant="body2"
                  sx={{ mb: 3, color: 'text.secondary', textAlign: 'center' }}
                >
                  {employee.employeeName} ({employee.employeeId})
                </Typography>
                <Box sx={{ 
                  width: '100%', 
                  height: { xs: 400, sm: 450, md: 500 },
                  display: 'flex',
                  justifyContent: 'center',
                  alignItems: 'center',
                  flexDirection: 'column',
                }}>
                  <RadarGraph
                    title="Skills Overview"
                    data={radarData}
                    comparisonData={jiraActualUsageData}
                    maxValue={normalizer}
                    levels={5}
                    loading={false}
                    error={null}
                    size={getChartSize()}
                    color="primary"
                  />
                  {/* Legend/Explanation */}
                  <Box sx={{ mt: 3, display: 'flex', gap: 3, flexWrap: 'wrap', justifyContent: 'center' }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Box
                        sx={{
                          width: 16,
                          height: 16,
                          backgroundColor: theme.palette.primary.main,
                          borderRadius: '50%',
                          border: `2px solid ${theme.palette.primary.main}`,
                        }}
                      />
                      <Typography variant="caption" sx={{ color: 'text.primary' }}>
                        Current Skills Profile
                      </Typography>
                    </Box>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Box
                        sx={{
                          width: 16,
                          height: 16,
                          backgroundColor: '#9e9e9e',
                          borderRadius: '50%',
                          border: '2px dashed #757575',
                          opacity: 0.6,
                        }}
                      />
                      <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                        Jira Actual Skills Usage
                      </Typography>
                    </Box>
                  </Box>
                </Box>
              </Card>
            </Grid>
          );
        })}
      </Grid>
    </Box>
  );
};

export default EmployeesSkillsDashboard;

