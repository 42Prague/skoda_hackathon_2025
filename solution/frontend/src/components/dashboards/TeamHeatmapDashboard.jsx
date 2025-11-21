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
import { useAuth } from '../../context/AuthContext';
import { analyticsAPI } from '../../services/api';

const TeamHeatmapDashboard = ({ teamId, memberIds = [] }) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const isTablet = useMediaQuery(theme.breakpoints.down('md'));
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [heatmapData, setHeatmapData] = useState(null);

  useEffect(() => {
    const fetchTeamHeatmap = async () => {
      setLoading(true);
      setError(null);
      
      try {
        // If memberIds is provided, use it; otherwise try to get from teamId
        let idsToUse = memberIds;
        
        if (!idsToUse || idsToUse.length === 0) {
          // If no member IDs provided, we can't fetch heatmap
          throw new Error('Member IDs are required for team heatmap');
        }
        
        // Clean member IDs
        const cleanMemberIds = idsToUse.map(id => String(id).split(':')[0].trim());
        
        // Fetch team heatmap from API
        const heatmapData = await analyticsAPI.getTeamHeatmap(teamId || 'team-1', cleanMemberIds);
        
        setHeatmapData(heatmapData);
      } catch (err) {
        setError(err.message || 'Failed to fetch team heatmap');
        console.error('Error fetching team heatmap:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchTeamHeatmap();
  }, [teamId, memberIds]);

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
        Error loading team heatmap: {error}
      </Alert>
    );
  }

  if (!heatmapData) {
    return (
      <Alert severity="info" sx={{ mb: 2 }}>
        No team data available.
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

  // Check if this is organization-level (all SKODA employees)
  const isOrganizationLevel = teamId === 'skoda-organization' || teamId?.includes('organization');

  return (
    <Box>
      <Typography 
        variant="h4" 
        component="h2" 
        sx={{ 
          mb: isOrganizationLevel ? 1 : 4,
          color: 'text.primary',
          fontWeight: 600
        }}
      >
        {isOrganizationLevel ? 'ŠKODA Organization Heatmap' : 'Team Skills Heatmap'}
      </Typography>
      {isOrganizationLevel && (
        <Typography 
          variant="body1" 
          color="text.secondary"
          sx={{ mb: 4 }}
        >
          Skills overview across all ŠKODA employees
        </Typography>
      )}

      {/* Heatmap Chart */}
      <Card 
        sx={{ 
          mb: 4,
          p: 3,
          backgroundColor: 'background.paper',
          boxShadow: 2
        }}
      >
        <Typography 
          variant="h6" 
          component="h3" 
          sx={{ mb: 2, color: 'text.primary' }}
        >
          Skills Distribution Across Team
        </Typography>
        {heatmapMatrix.length > 0 && skills.length > 0 ? (
          <Box sx={{ 
            width: '100%', 
            overflow: 'auto',
            border: 1,
            borderColor: 'divider',
            borderRadius: 1
          }}>
            <TableContainer>
              <Table size="small" sx={{ minWidth: Math.max(600, skills.length * 100) }}>
                <TableHead>
                  <TableRow>
                    <TableCell 
                      sx={{ 
                        position: 'sticky', 
                        left: 0, 
                        zIndex: 2,
                        backgroundColor: 'background.paper',
                        fontWeight: 600,
                        color: 'text.primary',
                        borderRight: 1,
                        borderColor: 'divider'
                      }}
                    >
                      Team Member
                    </TableCell>
                    {skills.map((skill, index) => (
                      <TableCell
                        key={index}
                        align="center"
                        sx={{
                          fontWeight: 600,
                          color: 'text.primary',
                          minWidth: 120,
                          padding: '16px 20px',
                          writingMode: { xs: 'horizontal-tb', md: 'vertical-rl' },
                          textOrientation: 'mixed',
                          height: { xs: 'auto', md: 150 }
                        }}
                      >
                        {typeof skill === 'string' ? skill.substring(0, 20) : (skill.name || skill).substring(0, 20)}
                      </TableCell>
                    ))}
                  </TableRow>
                </TableHead>
                <TableBody>
                  {members.map((member, memberIndex) => (
                    <TableRow key={memberIndex}>
                      <TableCell
                        sx={{
                          position: 'sticky',
                          left: 0,
                          zIndex: 1,
                          backgroundColor: 'background.paper',
                          fontWeight: 600,
                          borderRight: 1,
                          borderColor: 'divider',
                          padding: '16px 20px',
                          minWidth: 180
                        }}
                      >
                        {typeof member === 'string' ? member : (member.name || `Member ${memberIndex + 1}`)}
                      </TableCell>
                      {heatmapMatrix[memberIndex]?.map((value, skillIndex) => (
                        <Tooltip
                          key={skillIndex}
                          title={`${typeof member === 'string' ? member : member.name || 'Member'}: ${typeof skills[skillIndex] === 'string' ? skills[skillIndex] : skills[skillIndex]?.name || 'Skill'} - Level ${value}/5`}
                          arrow
                        >
                          <TableCell
                            align="center"
                            sx={{
                              backgroundColor: (theme) => getHeatmapColor(value, theme),
                              color: (theme) => getTextColor(value, theme),
                              fontWeight: value > 0 ? 600 : 400,
                              minWidth: 120,
                              padding: '20px 24px',
                              fontSize: '1.1rem',
                              cursor: 'pointer',
                              transition: 'all 0.2s ease',
                              '&:hover': {
                                opacity: 0.8,
                                transform: 'scale(1.05)'
                              }
                            }}
                          >
                            {value > 0 ? value : '-'}
                          </TableCell>
                        </Tooltip>
                      ))}
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
            {/* Legend */}
            <Box sx={{ mt: 2, display: 'flex', gap: 2, flexWrap: 'wrap', alignItems: 'center' }}>
              <Typography variant="caption" sx={{ fontWeight: 600, color: 'text.secondary' }}>
                Skill Level:
              </Typography>
              {[0, 1, 2, 3, 4, 5].map((level) => (
                <Box key={level} sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                  <Box
                    sx={{
                      width: 20,
                      height: 20,
                      backgroundColor: (theme) => getHeatmapColor(level, theme),
                      border: 1,
                      borderColor: 'divider',
                      borderRadius: 0.5
                    }}
                  />
                  <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                    {level === 0 ? 'None' : level}
                  </Typography>
                </Box>
              ))}
            </Box>
          </Box>
        ) : (
          <Alert severity="info">No heatmap data available.</Alert>
        )}
      </Card>

      {/* Team List Table */}
      <Card 
        sx={{ 
          p: 3,
          backgroundColor: 'background.paper',
          boxShadow: 2
        }}
      >
        <Typography 
          variant="h6" 
          component="h3" 
          sx={{ mb: 2, color: 'text.primary' }}
        >
          Team Members
        </Typography>
        <TableContainer component={Paper} variant="outlined">
          <Table>
            <TableHead>
              <TableRow>
                <TableCell sx={{ fontWeight: 600, color: 'text.primary' }}>Name</TableCell>
                <TableCell sx={{ fontWeight: 600, color: 'text.primary' }}>ID</TableCell>
                <TableCell sx={{ fontWeight: 600, color: 'text.primary' }}>Skills Count</TableCell>
                <TableCell sx={{ fontWeight: 600, color: 'text.primary' }}>Average Level</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {members.map((member, index) => {
                const memberSkills = heatmapMatrix[index] || [];
                const skillCount = memberSkills.filter(v => v > 0).length;
                const avgLevel = memberSkills.length > 0
                  ? (memberSkills.reduce((a, b) => a + b, 0) / memberSkills.length).toFixed(1)
                  : 0;
                
                const memberName = typeof member === 'string' ? member : (member.name || `Member ${index + 1}`);
                const memberId = memberIds?.[index] || `ID-${index + 1}`;
                
                return (
                  <TableRow key={memberId || index}>
                    <TableCell>{memberName}</TableCell>
                    <TableCell>{memberId}</TableCell>
                    <TableCell>{skillCount}</TableCell>
                    <TableCell>{avgLevel}</TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </TableContainer>
      </Card>
    </Box>
  );
};

export default TeamHeatmapDashboard;

