import { useState, useEffect } from 'react';
import { 
  Box, 
  Typography, 
  Card, 
  CircularProgress, 
  Alert,
  Grid,
  useTheme,
  useMediaQuery
} from '@mui/material';
import { LineChart } from '@mui/x-charts';
import { useAuth } from '../../context/AuthContext';
import { analyticsAPI } from '../../services/api';

const SkillTrendsDashboard = () => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const isTablet = useMediaQuery(theme.breakpoints.down('md'));
  const { isHR, isManager } = useAuth();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [trendsData, setTrendsData] = useState(null);

  useEffect(() => {
    const fetchTrends = async () => {
      setLoading(true);
      setError(null);
      
      try {
        // Fetch company skill trends from API
        const data = await analyticsAPI.getCompanySkillTrends();
        
        // Transform API response to match component expectations
        // API returns: { yearlySkillCounts, emergingSkills, obsoleteSkills }
        const transformedData = {
          emergingSkills: (data.emergingSkills || []).map(skill => ({
            name: skill.name || skill.skill_name || 'Unknown',
            growthRate: skill.growthRate || skill.growth_rate || 0,
            year: skill.year || new Date().getFullYear(),
          })),
          obsoleteSkills: (data.obsoleteSkills || []).map(skill => ({
            name: skill.name || skill.skill_name || 'Unknown',
            declineRate: skill.declineRate || skill.decline_rate || 0,
            year: skill.year || new Date().getFullYear(),
          })),
          yearlySkillCounts: (data.yearlySkillCounts || []).map(item => ({
            year: item.year || item.date || new Date().getFullYear(),
            count: item.count || item.skill_count || 0,
          })),
        };
        
        setTrendsData(transformedData);
      } catch (err) {
        setError(err.message || 'Failed to fetch skill trends');
        console.error('Error fetching skill trends:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchTrends();
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
        Error loading skill trends: {error}
      </Alert>
    );
  }

  if (!trendsData) {
    return (
      <Alert severity="info" sx={{ mb: 2 }}>
        No skill trends data available.
      </Alert>
    );
  }


  // Prepare data for multi-line chart showing 10 skills with different evolutions
  // The 10 skills from TeamSkill.jsx with different growth patterns
  const skillNames = [
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

  // Years to display
  const years = [2020, 2021, 2022, 2023, 2024, 2025];

  // HR-specific skill trends - focus on HR-related skills
  const hrSkillEvolutionData = {
    'Communication': [85, 88, 82, 90, 85, 92], // HR focus: High communication skills with growth
    'Recruitment Skills': [70, 75, 78, 80, 83, 88], // HR-specific: Growing recruitment capabilities
    'Talent Management': [65, 72, 75, 78, 82, 85], // HR-specific: Talent management trends
    'Employee Relations': [80, 83, 79, 87, 84, 90], // HR-specific: Employee relations focus
    'Leadership': [75, 80, 77, 85, 82, 88], // HR needs strong leadership
    'Team Collaboration': [88, 85, 90, 82, 92, 88], // HR: High collaboration
    'Training & Development': [68, 75, 72, 80, 77, 85], // HR-specific: Training trends
    'Analytical Thinking': [70, 73, 75, 78, 76, 80], // HR: Moderate analytical needs
    'Strategic Planning': [62, 68, 70, 75, 73, 78], // HR: Growing strategic role
    'Change Management': [58, 65, 68, 72, 70, 75], // HR: Emerging change management focus
  };

  // Manager-specific skill trends - focus on management and technical skills
  const managerSkillEvolutionData = {
    'Communication': [78, 82, 79, 85, 81, 87], // Manager: Strong communication
    'Project Management': [85, 88, 83, 90, 86, 92], // Manager: Core project management
    'Problem Solving': [80, 85, 82, 88, 84, 90], // Manager: High problem-solving
    'Team Collaboration': [82, 85, 80, 88, 83, 90], // Manager: Team focus
    'Analytical Thinking': [75, 78, 76, 82, 79, 85], // Manager: Analytical skills
    'Leadership': [88, 85, 90, 82, 92, 88], // Manager: Leadership is key
    'Time Management': [85, 88, 83, 90, 86, 92], // Manager: Time management critical
    'Adaptability': [78, 82, 79, 85, 81, 87], // Manager: Adaptability needed
    'Technical Skills': [70, 75, 72, 78, 74, 80], // Manager: Technical understanding
    'Innovation': [68, 72, 70, 76, 73, 79], // Manager: Innovation driving
  };

  // Determine which skill set to use based on role
  const skillEvolutionData = isHR ? hrSkillEvolutionData : managerSkillEvolutionData;
  
  // Update skill names based on role
  const displaySkillNames = isHR 
    ? [
        'Communication',
        'Recruitment Skills',
        'Talent Management',
        'Employee Relations',
        'Leadership',
        'Team Collaboration',
        'Training & Development',
        'Analytical Thinking',
        'Strategic Planning',
        'Change Management',
      ]
    : skillNames; // Use default skillNames for managers

  // Prepare series data for LineChart - one series per skill
  const skillTrendsSeries = displaySkillNames.map((skillName, index) => ({
    data: skillEvolutionData[skillName] || years.map(() => 70),
    label: skillName,
    curve: 'natural',
  }));

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
        {isHR ? 'HR Skill Trends' : 'Manager Team Skill Trends'}
      </Typography>
      <Typography 
        variant="body1" 
        color="text.secondary"
        sx={{ mb: 4 }}
      >
        {isHR 
          ? 'HR-specific skill evolution trends and capabilities' 
          : 'Team skill evolution trends across managed teams'}
      </Typography>

      <Grid container spacing={3}>
        {/* Skill Trends Over Time - Multi-line Chart with 10 Skills */}
        <Grid item xs={12}>
          <Card 
            sx={{ 
              p: 3,
              backgroundColor: 'background.paper',
              boxShadow: 2
            }}
          >
            <Typography 
              variant="h4" 
              component="h3" 
              sx={{ 
                mb: 2, 
                color: '#2e7d32', // Dark green
                textAlign: 'center',
                fontWeight: 600
              }}
            >
              {isHR ? 'HR Skill Trends Over Time' : 'Team Skill Trends Over Time'}
            </Typography>
            <Box sx={{ 
              width: '100%', 
              height: { xs: 350, sm: 400, md: 450 },
              display: 'flex',
              justifyContent: 'center',
              alignItems: 'center',
              overflow: 'auto'
            }}>
              <LineChart
                width={isMobile ? 300 : isTablet ? 600 : 900}
                height={isMobile ? 350 : isTablet ? 400 : 450}
                series={skillTrendsSeries.map((series, index) => ({
                  data: series.data,
                  label: series.label,
                  curve: series.curve,
                  color: [
                    theme.palette.primary.main,
                    theme.palette.secondary.main,
                    theme.palette.error.main,
                    theme.palette.warning.main,
                    theme.palette.info.main,
                    theme.palette.success.main,
                    '#9c27b0', // purple
                    '#f44336', // red
                    '#00bcd4', // cyan
                    '#ff9800', // orange
                  ][index % 10],
                }))}
                xAxis={[
                  {
                    data: years,
                    scaleType: 'point',
                    label: 'Year',
                    valueFormatter: (value) => value.toString(),
                    labelStyle: {
                      fill: theme.palette.text.primary,
                    },
                  },
                ]}
                yAxis={[
                  {
                    label: 'Skill Level',
                    min: 0,
                    max: 100,
                    labelStyle: {
                      fill: theme.palette.text.primary,
                    },
                  },
                ]}
                sx={{
                  '& .MuiChartsLegend-root': {
                    fill: theme.palette.text.primary,
                  },
                  '& .MuiChartsAxis-root': {
                    stroke: theme.palette.text.secondary,
                  },
                  '& .MuiChartsAxis-tick': {
                    stroke: theme.palette.text.secondary,
                  },
                  '& .MuiChartsAxis-tickLabel': {
                    fill: theme.palette.text.secondary,
                  },
                  '& .MuiChartsGrid-line': {
                    stroke: theme.palette.divider,
                  },
                }}
              />
            </Box>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default SkillTrendsDashboard;

