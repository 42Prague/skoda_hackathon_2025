import { useState, useEffect } from 'react';
import { 
  Box, 
  Typography, 
  Card, 
  CircularProgress, 
  Alert,
  Button,
  Grid,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Chip,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  LinearProgress,
  Divider,
  useTheme,
  useMediaQuery
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import RadioButtonUncheckedIcon from '@mui/icons-material/RadioButtonUnchecked';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import SchoolIcon from '@mui/icons-material/School';
import WorkIcon from '@mui/icons-material/Work';
import { useAuth } from '../../context/AuthContext';
import { analyticsAPI } from '../../services/api';

const CareerPathDashboard = ({ employeeId, targetRole = 'Senior Engineer' }) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const isTablet = useMediaQuery(theme.breakpoints.down('md'));
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [readinessData, setReadinessData] = useState(null);
  const [expandedStep, setExpandedStep] = useState(0);

  useEffect(() => {
    const fetchReadiness = async () => {
      if (!employeeId) {
        setLoading(false);
        return;
      }
      
      setLoading(true);
      setError(null);
      
      try {
        // Clean employee ID
        const cleanEmployeeId = String(employeeId).split(':')[0].trim();
        
        // Fetch position readiness from API
        const data = await analyticsAPI.getPositionReadiness(cleanEmployeeId, targetRole);
        
        // Transform API response to match component expectations
        // The API returns: { employeeId, targetRole, readinessScore, blockingSkills }
        // We need to transform this into the steps format expected by the component
        const transformedData = {
          overallReadiness: data.readinessScore || 0,
          steps: [
            {
              id: 1,
              title: `Target Position: ${targetRole}`,
              status: 'target',
              description: `Readiness assessment for ${targetRole} position`,
              skills: (data.blockingSkills || []).map((skill, index) => ({
                name: skill.name || skill.skill_name || `Skill ${index + 1}`,
                level: skill.currentLevel || 0,
                required: skill.requiredLevel || 80,
                status: skill.currentLevel >= skill.requiredLevel ? 'met' : 'gap',
              })),
              readiness: data.readinessScore || 0,
              timeline: 'Assessment',
            },
          ],
        };
        
        setReadinessData(transformedData);
      } catch (err) {
        setError(err.message || 'Failed to fetch career path data');
        console.error('Error fetching career path:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchReadiness();
  }, [employeeId, targetRole]);

  const handleStepChange = (stepId) => (event, isExpanded) => {
    setExpandedStep(isExpanded ? stepId : -1);
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'current':
        return 'success';
      case 'next':
        return 'warning';
      case 'future':
        return 'info';
      case 'target':
        return 'primary';
      default:
        return 'default';
    }
  };

  const getStatusLabel = (status) => {
    switch (status) {
      case 'current':
        return 'Current';
      case 'next':
        return 'Next Step';
      case 'future':
        return 'Future';
      case 'target':
        return 'Target';
      default:
        return 'Unknown';
    }
  };

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
        Error loading career path data: {error}
      </Alert>
    );
  }

  // Use readiness data from API
  const careerPathData = readinessData || { steps: [], overallReadiness: 0 };
  const steps = careerPathData.steps || [];
  const overallReadiness = careerPathData.overallReadiness || 0;

  // Prepare comparison data for bar chart from first future step
  const nextStep = steps.find(s => s.status === 'next') || steps[1] || steps[0];
  const comparisonData = nextStep?.skills ? {
    owned: nextStep.skills.map(s => ({ skill: s.name, value: s.level })),
    required: nextStep.skills.map(s => ({ skill: s.name, value: s.required })),
  } : {
    owned: [
      { skill: 'Technical Skills', value: 75 },
      { skill: 'Leadership', value: 60 },
      { skill: 'Communication', value: 80 },
      { skill: 'Project Management', value: 55 },
    ],
    required: [
      { skill: 'Technical Skills', value: 90 },
      { skill: 'Leadership', value: 85 },
      { skill: 'Communication', value: 80 },
      { skill: 'Project Management', value: 90 },
    ]
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
        Career Path Projection
      </Typography>
      <Typography 
        variant="body1" 
        color="text.secondary"
        sx={{ mb: 4 }}
      >
        Step-by-step career progression to {targetRole}
      </Typography>

      {/* Overall Readiness Score */}
      <Card 
        sx={{ 
          mb: 4,
          p: 3,
          backgroundColor: 'background.paper',
          boxShadow: 2
        }}
      >
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Box sx={{ flex: 1 }}>
            <Typography 
              variant="h6" 
              component="h3" 
              sx={{ color: 'text.primary', mb: 0.5 }}
            >
              Overall Readiness for {targetRole}
            </Typography>
            <Typography 
              variant="body2" 
              sx={{ color: 'text.secondary', mb: 2 }}
            >
              Your current readiness score for the target position
            </Typography>
            <LinearProgress 
              variant="determinate" 
              value={overallReadiness} 
              sx={{ 
                height: 8, 
                borderRadius: 4,
                backgroundColor: 'grey.200',
                '& .MuiLinearProgress-bar': {
                  backgroundColor: overallReadiness >= 80 ? 'success.main' : overallReadiness >= 60 ? 'warning.main' : 'error.main',
                }
              }}
            />
          </Box>
          <Typography 
            variant="h3" 
            component="span" 
            sx={{ 
              ml: 3,
              color: overallReadiness >= 80 ? 'success.main' : overallReadiness >= 60 ? 'warning.main' : 'error.main',
              fontWeight: 700
            }}
          >
            {Math.round(overallReadiness)}%
          </Typography>
        </Box>
      </Card>

      <Grid container spacing={3}>
        {/* Career Path Steps with Accordion */}
        <Grid item xs={12}>
          <Card 
            sx={{ 
              p: 3,
              height: '100%',
              backgroundColor: 'background.paper',
              boxShadow: 2
            }}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 3 }}>
              <TrendingUpIcon sx={{ color: 'primary.main' }} />
              <Typography 
                variant="h6" 
                component="h3" 
                sx={{ color: 'text.primary' }}
              >
                Career Path Steps
              </Typography>
            </Box>
            
            {steps.map((step, index) => (
              <Accordion
                key={step.id}
                expanded={expandedStep === step.id}
                onChange={handleStepChange(step.id)}
                sx={{
                  mb: 2,
                  '&:before': { display: 'none' },
                  boxShadow: expandedStep === step.id ? 3 : 1,
                  borderLeft: `4px solid ${theme.palette[getStatusColor(step.status)].main}`,
                }}
              >
                <AccordionSummary
                  expandIcon={<ExpandMoreIcon />}
                  sx={{
                    '& .MuiAccordionSummary-content': {
                      alignItems: 'center',
                      gap: 2,
                    },
                  }}
                >
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flex: 1 }}>
                    {step.status === 'current' ? (
                      <CheckCircleIcon sx={{ color: 'success.main' }} />
                    ) : (
                      <RadioButtonUncheckedIcon sx={{ color: 'text.secondary' }} />
                    )}
                    <Box sx={{ flex: 1 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                        <Typography variant="subtitle1" sx={{ fontWeight: 600, color: 'text.primary' }}>
                          {step.title}
                        </Typography>
                        <Chip 
                          label={getStatusLabel(step.status)} 
                          size="small" 
                          color={getStatusColor(step.status)}
                        />
                      </Box>
                      <Typography variant="caption" color="text.secondary">
                        {step.timeline}
                      </Typography>
                    </Box>
                  </Box>
                </AccordionSummary>
                <AccordionDetails>
                  <Box>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                      {step.description}
                    </Typography>

                    {/* Readiness Progress for future steps */}
                    {step.readiness !== undefined && step.status !== 'current' && (
                      <Box sx={{ mb: 3 }}>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                          <Typography variant="body2" color="text.secondary">
                            Readiness: {step.readiness}%
                          </Typography>
                        </Box>
                        <LinearProgress 
                          variant="determinate" 
                          value={step.readiness} 
                          sx={{ 
                            height: 6, 
                            borderRadius: 3,
                            backgroundColor: 'grey.200',
                          }}
                        />
                      </Box>
                    )}

                    {/* Skills Section */}
                    {step.skills && step.skills.length > 0 && (
                      <Box sx={{ mb: 3 }}>
                        <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 2, color: 'text.primary' }}>
                          Skills
                        </Typography>
                        <List dense>
                          {step.skills.map((skill, skillIndex) => (
                            <ListItem key={skillIndex} sx={{ px: 0 }}>
                              <ListItemIcon sx={{ minWidth: 36 }}>
                                {skill.status === 'met' ? (
                                  <CheckCircleIcon sx={{ color: 'success.main', fontSize: 20 }} />
                                ) : (
                                  <RadioButtonUncheckedIcon sx={{ color: 'warning.main', fontSize: 20 }} />
                                )}
                              </ListItemIcon>
                              <ListItemText
                                primary={
                                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                    <Typography variant="body2">{skill.name}</Typography>
                                    <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                                      <Typography variant="caption" color="text.secondary">
                                        {skill.level}%
                                      </Typography>
                                      <Typography variant="caption" color="text.secondary">
                                        /
                                      </Typography>
                                      <Typography variant="caption" sx={{ fontWeight: 600 }}>
                                        {skill.required}%
                                      </Typography>
                                    </Box>
                                  </Box>
                                }
                                secondary={
                                  <LinearProgress
                                    variant="determinate"
                                    value={skill.level}
                                    sx={{
                                      mt: 0.5,
                                      height: 4,
                                      borderRadius: 2,
                                      backgroundColor: 'grey.200',
                                      '& .MuiLinearProgress-bar': {
                                        backgroundColor: skill.level >= skill.required ? 'success.main' : 'warning.main',
                                      },
                                    }}
                                  />
                                }
                              />
                            </ListItem>
                          ))}
                        </List>
                      </Box>
                    )}

                    {/* Achievements for current step */}
                    {step.achievements && step.achievements.length > 0 && (
                      <Box sx={{ mb: 3 }}>
                        <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1, color: 'text.primary' }}>
                          Key Achievements
                        </Typography>
                        <List dense>
                          {step.achievements.map((achievement, achIndex) => (
                            <ListItem key={achIndex} sx={{ px: 0, py: 0.5 }}>
                              <ListItemIcon sx={{ minWidth: 36 }}>
                                <CheckCircleIcon sx={{ color: 'success.main', fontSize: 18 }} />
                              </ListItemIcon>
                              <ListItemText 
                                primary={achievement}
                                primaryTypographyProps={{ variant: 'body2', color: 'text.secondary' }}
                              />
                            </ListItem>
                          ))}
                        </List>
                      </Box>
                    )}

                    {/* Actions for next steps */}
                    {step.actions && step.actions.length > 0 && (
                      <Box>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                          <SchoolIcon sx={{ color: 'primary.main', fontSize: 20 }} />
                          <Typography variant="subtitle2" sx={{ fontWeight: 600, color: 'text.primary' }}>
                            Recommended Actions
                          </Typography>
                        </Box>
                        <List dense>
                          {step.actions.map((action, actionIndex) => (
                            <ListItem key={actionIndex} sx={{ px: 0, py: 0.5 }}>
                              <ListItemIcon sx={{ minWidth: 36 }}>
                                <WorkIcon sx={{ color: 'primary.main', fontSize: 18 }} />
                              </ListItemIcon>
                              <ListItemText 
                                primary={action}
                                primaryTypographyProps={{ variant: 'body2', color: 'text.secondary' }}
                              />
                            </ListItem>
                          ))}
                        </List>
                      </Box>
                    )}

                    {/* Requirements for future steps */}
                    {step.requirements && step.requirements.length > 0 && (
                      <Box sx={{ mt: 3 }}>
                        <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1, color: 'text.primary' }}>
                          Requirements
                        </Typography>
                        <List dense>
                          {step.requirements.map((req, reqIndex) => (
                            <ListItem key={reqIndex} sx={{ px: 0, py: 0.5 }}>
                              <ListItemIcon sx={{ minWidth: 36 }}>
                                <RadioButtonUncheckedIcon sx={{ color: 'info.main', fontSize: 18 }} />
                              </ListItemIcon>
                              <ListItemText 
                                primary={req}
                                primaryTypographyProps={{ variant: 'body2', color: 'text.secondary' }}
                              />
                            </ListItem>
                          ))}
                        </List>
                      </Box>
                    )}
                  </Box>
                </AccordionDetails>
              </Accordion>
            ))}
          </Card>
        </Grid>

      </Grid>
    </Box>
  );
};

export default CareerPathDashboard;
