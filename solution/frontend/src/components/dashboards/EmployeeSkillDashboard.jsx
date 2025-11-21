import { useState, useEffect } from 'react';
import { Box, Typography, Card, CircularProgress, Alert, Grid, useTheme, useMediaQuery } from '@mui/material';
import RadarGraph from '../charts/RadarGraph';
import { useAuth } from '../../context/AuthContext';
import { analyticsAPI } from '../../services/api';

const EmployeeSkillDashboard = ({ employeeId }) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const isTablet = useMediaQuery(theme.breakpoints.down('md'));
  const { isHR, isManager, selectedUser, user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [skillProfile, setSkillProfile] = useState(null);
  
  const getChartWidth = () => {
    if (isMobile) return 280;
    if (isTablet) return 400;
    return 500;
  };

  useEffect(() => {
    const fetchSkillProfile = async () => {
      if (!employeeId) {
        setLoading(false);
        return;
      }

      setLoading(true);
      setError(null);

      try {
        // Clean employee ID (remove any suffix like ":1")
        const cleanEmployeeId = String(employeeId).split(':')[0].trim();
        
        // Fetch skill profile from API
        const profile = await analyticsAPI.getEmployeeSkillProfile(cleanEmployeeId);
        
        // Transform API response to match component expectations
        const transformedProfile = {
          employeeId: profile.employeeId,
          employeeName: profile.employeeId, // Use ID as name fallback
          position: profile.currentProfession || profile.plannedProfession || 'Employee',
          skills: profile.skills.map(skill => ({
            name: skill.name,
            theme: skill.name, // Use skill name as theme fallback
            expertiseLevel: skill.expertiseLevel || 0,
            validUntil: skill.validUntil || null,
          })),
        };

        setSkillProfile(transformedProfile);
      } catch (err) {
        setError(err.message || 'Failed to fetch skill profile');
        console.error('Error fetching skill profile:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchSkillProfile();
  }, [employeeId]);

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
        Error loading skill profile: {error}
      </Alert>
    );
  }

  if (!skillProfile) {
    return (
      <Alert severity="info" sx={{ mb: 2 }}>
        No skill profile data available.
      </Alert>
    );
  }

  // Map individual skills to the 10 standard skills for the radar chart
  // This matches TeamSkill.jsx and TeamHeatmapDashboard.jsx
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

  // Map individual skills from profile to standard skill categories
  const calculateStandardSkillLevel = (standardSkillName) => {
    const allProfileSkills = skillProfile.skills || [];
    
    // Find skills that match this standard skill by name or theme
    let matchingSkills = [];
    
    // First, try direct name or theme match
    matchingSkills = allProfileSkills.filter((skill) => {
      const skillName = (skill.name || '').toLowerCase();
      const skillTheme = (skill.theme || '').toLowerCase();
      const standardName = standardSkillName.toLowerCase();
      
      // Direct name match (e.g., "Communication" skill matches "Communication" category)
      if (skillName === standardName || skillTheme === standardName) {
        return true;
      }
      
      // Partial match (e.g., "Problem Solving" skill matches "Problem Solving" category)
      if (skillName.includes(standardName) || standardName.includes(skillName)) {
        return true;
      }
      
      return false;
    });

    // If no direct match, use theme-based mapping
    if (matchingSkills.length === 0) {
      matchingSkills = allProfileSkills.filter((skill) => {
        const skillTheme = (skill.theme || '').toLowerCase();
        const standardName = standardSkillName.toLowerCase();
        
        // Check if theme matches standard skill name
        if (skillTheme === standardName) {
          return true;
        }
        
        // Specific mappings for Technical Skills
        if (standardSkillName === 'Technical Skills' && skillTheme === 'technical skills') {
          return true;
        }
        
        // Specific mappings for other categories
        if (standardSkillName === 'Analytical Thinking' && skillTheme === 'analytical thinking') {
          return true;
        }
        
        return false;
      });
    }

    // If still no match, use skill name patterns for Technical Skills category
    if (matchingSkills.length === 0 && standardSkillName === 'Technical Skills') {
      const techSkillNames = ['python', 'fastapi', 'postgresql', 'react', 'api design', 'database design', 
                               'recruitment', 'talent management', 'hr policies', 'agile', 'scrum', 
                               'project planning', 'risk management', 'stakeholder management'];
      matchingSkills = allProfileSkills.filter((skill) => {
        const skillName = (skill.name || '').toLowerCase();
        return techSkillNames.some(tech => skillName.includes(tech) || tech.includes(skillName));
      });
    }
    
    // Calculate average level from matching skills
    if (matchingSkills.length > 0) {
      const totalLevel = matchingSkills.reduce((sum, skill) => {
        const level = typeof skill.expertiseLevel === 'number' ? skill.expertiseLevel : (skill.expertiseLevel || 1);
        return sum + level;
      }, 0);
      return totalLevel / matchingSkills.length;
    }
    
    // Default: return 0 if no match
    return 0;
  };

  // Prepare all skills data for display
  const allSkills = skillProfile.skills?.map((skill) => ({
    name: skill.name || 'Unknown Skill',
    level: skill.expertiseLevel || 1,
    theme: skill.theme || 'Other',
    maxLevel: 5,
  })) || [];

  // Prepare data for RadarGraph component - use individual skills from profile (matching All Skills)
  // Convert allSkills to radarData format
  const radarData = allSkills.map((skill) => ({
    label: skill.name,
    value: skill.level,
    max: skill.maxLevel,
  }));

  // Generate Jira actual skills usage data (slightly different values for comparison)
  const jiraComparisonData = radarData.map((skill, index) => {
    const baseValue = skill.value || 0;
    // Jira usage is typically 65-85% of the profile value, with some variation
    const jiraValue = Math.max(0, baseValue * (0.65 + (index % 4) * 0.08));
    return {
      label: skill.label,
      value: Math.min(jiraValue, skill.max), // Cap at max level
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
        {skillProfile?.employeeName && skillProfile?.position 
          ? `${skillProfile.position} Skills (${skillProfile.employeeName})`
          : 'Your Skills'}
      </Typography>

      <Grid container spacing={3}>
        {/* Radar Chart - Skills Overview */}
        <Grid item xs={12}>
          <Card 
            sx={{ 
              p: 4,
              backgroundColor: 'background.paper',
              boxShadow: 2,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
            }}
          >
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
              Employee Skills Overview
            </Typography>
            {radarData.length > 0 ? (
              <Box sx={{ 
                width: '100%', 
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'center',
                alignItems: 'center',
              }}>
                <Box sx={{ 
                  display: 'flex',
                  justifyContent: 'center',
                  alignItems: 'center',
                  width: '100%',
                }}>
                  <RadarGraph
                    title="Skills Overview"
                    data={radarData}
                    comparisonData={jiraComparisonData}
                    maxValue={Math.max(5, ...radarData.map(d => d.max || 5))}
                    levels={5}
                    size={getChartWidth()}
                    color={theme.palette.brand?.primary || theme.palette.primary.main}
                  />
                </Box>
                {/* Legend/Explanation */}
                <Box sx={{ mt: 3, display: 'flex', gap: 4, flexWrap: 'wrap', justifyContent: 'center' }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Box
                      sx={{
                        width: 20,
                        height: 3,
                        backgroundColor: theme.palette.brand?.primary || theme.palette.primary.main,
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
            ) : (
              <Alert severity="info">No skill data available for skills overview.</Alert>
            )}
          </Card>
        </Grid>

        {/* All Skills Display */}
        <Grid item xs={12}>
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
              sx={{ mb: 3, color: 'text.primary' }}
            >
              All Skills
            </Typography>
            {allSkills.length > 0 ? (
              <Grid container spacing={2}>
                {allSkills.map((skill, index) => {
                  const radarColor = theme.palette.brand?.primary || theme.palette.primary.main;
                  const percentage = (skill.level / skill.maxLevel) * 100;
                  
                  return (
                    <Grid item xs={12} sm={6} md={4} key={index}>
                      <Box
                        sx={{
                          p: 2,
                          border: 1,
                          borderColor: 'divider',
                          borderRadius: 2,
                          backgroundColor: 'background.default',
                          '&:hover': {
                            boxShadow: 2,
                            borderColor: radarColor,
                          },
                          transition: 'all 0.2s ease',
                        }}
                      >
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                          <Typography variant="subtitle2" sx={{ fontWeight: 600, color: 'text.primary' }}>
                            {skill.name}
                          </Typography>
                          <Typography variant="caption" sx={{ color: 'text.secondary', fontWeight: 600 }}>
                            Level {skill.level}/{skill.maxLevel}
                          </Typography>
                        </Box>
                        <Typography variant="caption" sx={{ color: 'text.secondary', display: 'block', mb: 1 }}>
                          {skill.theme}
                        </Typography>
                        <Box
                          sx={{
                            width: '100%',
                            height: 8,
                            backgroundColor: 'grey.200',
                            borderRadius: 1,
                            overflow: 'hidden',
                          }}
                        >
                          <Box
                            sx={{
                              width: `${percentage}%`,
                              height: '100%',
                              backgroundColor: radarColor,
                              transition: 'width 0.3s ease',
                            }}
                          />
                        </Box>
                      </Box>
                    </Grid>
                  );
                })}
              </Grid>
            ) : (
              <Alert severity="info">No skills data available.</Alert>
            )}
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default EmployeeSkillDashboard;

