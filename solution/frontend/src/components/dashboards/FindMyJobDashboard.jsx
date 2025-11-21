import { useState, useEffect } from 'react';
import { 
  Box, 
  Typography, 
  Card, 
  CircularProgress, 
  Alert, 
  Grid,
  TextField,
  Button,
  Paper,
  Chip,
  useTheme,
  useMediaQuery,
  Divider,
} from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import UploadFileIcon from '@mui/icons-material/UploadFile';
import RadarGraph from '../charts/RadarGraph';
import NetworkGraph from '../charts/NetworkGraph';

const FindMyJobDashboard = () => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const isTablet = useMediaQuery(theme.breakpoints.down('md'));
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // Job search state
  const [jobSearchQuery, setJobSearchQuery] = useState('');
  const [selectedJob, setSelectedJob] = useState(null);
  const [jobSkills, setJobSkills] = useState(null);
  
  // Employee profile state
  const [employeeProfile, setEmployeeProfile] = useState(null);
  const [employeeSkills, setEmployeeSkills] = useState(null);
  const [employeeJiraSkills, setEmployeeJiraSkills] = useState(null);
  const [matchScore, setMatchScore] = useState(null);

  const getChartSize = () => {
    if (isMobile) return 300;
    if (isTablet) return 400;
    return 500;
  };

  const getNetworkGraphSize = () => {
    if (isMobile) return 220;
    if (isTablet) return 280;
    return 350;
  };

  // Mock jobs database
  const mockJobs = [
    {
      id: 'job-001',
      title: 'Data Engineer',
      department: 'IT',
      requiredSkills: [
        { skill_name: 'Communication', quantity: 75 },
        { skill_name: 'Project Management', quantity: 60 },
        { skill_name: 'Problem Solving', quantity: 90 },
        { skill_name: 'Team Collaboration', quantity: 75 },
        { skill_name: 'Analytical Thinking', quantity: 95 },
        { skill_name: 'Leadership', quantity: 40 },
        { skill_name: 'Time Management', quantity: 75 },
        { skill_name: 'Adaptability', quantity: 90 },
        { skill_name: 'Technical Skills', quantity: 95 },
        { skill_name: 'Innovation', quantity: 85 },
      ],
    },
    {
      id: 'job-002',
      title: 'Project Manager',
      department: 'Operations',
      requiredSkills: [
        { skill_name: 'Communication', quantity: 95 },
        { skill_name: 'Project Management', quantity: 98 },
        { skill_name: 'Problem Solving', quantity: 80 },
        { skill_name: 'Team Collaboration', quantity: 95 },
        { skill_name: 'Analytical Thinking', quantity: 70 },
        { skill_name: 'Leadership', quantity: 95 },
        { skill_name: 'Time Management', quantity: 98 },
        { skill_name: 'Adaptability', quantity: 80 },
        { skill_name: 'Technical Skills', quantity: 70 },
        { skill_name: 'Innovation', quantity: 75 },
      ],
    },
    {
      id: 'job-003',
      title: 'HR Manager',
      department: 'Human Resources',
      requiredSkills: [
        { skill_name: 'Communication', quantity: 98 },
        { skill_name: 'Project Management', quantity: 80 },
        { skill_name: 'Problem Solving', quantity: 80 },
        { skill_name: 'Team Collaboration', quantity: 98 },
        { skill_name: 'Analytical Thinking', quantity: 75 },
        { skill_name: 'Leadership', quantity: 95 },
        { skill_name: 'Time Management', quantity: 80 },
        { skill_name: 'Adaptability', quantity: 75 },
        { skill_name: 'Technical Skills', quantity: 60 },
        { skill_name: 'Innovation', quantity: 70 },
      ],
    },
    {
      id: 'job-004',
      title: 'Web Developer',
      department: 'IT',
      requiredSkills: [
        { skill_name: 'Communication', quantity: 75 },
        { skill_name: 'Project Management', quantity: 65 },
        { skill_name: 'Problem Solving', quantity: 90 },
        { skill_name: 'Team Collaboration', quantity: 80 },
        { skill_name: 'Analytical Thinking', quantity: 85 },
        { skill_name: 'Leadership', quantity: 50 },
        { skill_name: 'Time Management', quantity: 80 },
        { skill_name: 'Adaptability', quantity: 90 },
        { skill_name: 'Technical Skills', quantity: 95 },
        { skill_name: 'Innovation', quantity: 85 },
      ],
    },
  ];

  // Mock employee profiles
  const mockEmployeeProfiles = [
    {
      id: 'emp-001',
      name: 'John Doe',
      position: 'Software Engineer',
      skills: [
        { skill_name: 'Communication', quantity: 80 },
        { skill_name: 'Project Management', quantity: 70 },
        { skill_name: 'Problem Solving', quantity: 85 },
        { skill_name: 'Team Collaboration', quantity: 80 },
        { skill_name: 'Analytical Thinking', quantity: 90 },
        { skill_name: 'Leadership', quantity: 60 },
        { skill_name: 'Time Management', quantity: 85 },
        { skill_name: 'Adaptability', quantity: 85 },
        { skill_name: 'Technical Skills', quantity: 92 },
        { skill_name: 'Innovation', quantity: 80 },
      ],
    },
    {
      id: 'emp-002',
      name: 'Jane Smith',
      position: 'Junior Developer',
      skills: [
        { skill_name: 'Communication', quantity: 70 },
        { skill_name: 'Project Management', quantity: 55 },
        { skill_name: 'Problem Solving', quantity: 75 },
        { skill_name: 'Team Collaboration', quantity: 75 },
        { skill_name: 'Analytical Thinking', quantity: 80 },
        { skill_name: 'Leadership', quantity: 45 },
        { skill_name: 'Time Management', quantity: 75 },
        { skill_name: 'Adaptability', quantity: 80 },
        { skill_name: 'Technical Skills', quantity: 85 },
        { skill_name: 'Innovation', quantity: 70 },
      ],
    },
  ];

  const handleJobSearch = () => {
    if (!jobSearchQuery.trim()) {
      setError('Please enter a job title, department, or keyword to search');
      return;
    }

    setLoading(true);
    setError(null);

    // Simulate API call
    setTimeout(() => {
      const query = jobSearchQuery.toLowerCase().trim();
      
      // Search by title, department, or keywords
      const foundJob = mockJobs.find(
        (job) => 
          job.title.toLowerCase().includes(query) ||
          job.department.toLowerCase().includes(query) ||
          job.title.toLowerCase().split(' ').some(word => word.startsWith(query)) ||
          job.department.toLowerCase().split(' ').some(word => word.startsWith(query))
      );

      if (foundJob) {
        setSelectedJob(foundJob);
        const normalizer = Math.max(1, ...foundJob.requiredSkills.map((s) => Number(s.quantity) || 0));
        const radarData = foundJob.requiredSkills.map((skill) => ({
          label: skill.skill_name,
          value: Math.min(Number(skill.quantity) || 0, normalizer),
          max: normalizer,
        }));
        setJobSkills(radarData);
        setError(null);
      } else {
        setError(`No job found matching "${jobSearchQuery}". Available jobs: Data Engineer, Project Manager, HR Manager, Web Developer`);
        setSelectedJob(null);
        setJobSkills(null);
      }
      setLoading(false);
    }, 800);
  };

  const handleProfileUpload = () => {
    // Simulate uploading an employee profile
    // In real implementation, this would read from a file or API
    setLoading(true);
    setError(null);

    setTimeout(() => {
      // Use first mock profile as example
      const profile = mockEmployeeProfiles[0];
      setEmployeeProfile(profile);
      
      const normalizer = Math.max(1, ...profile.skills.map((s) => Number(s.quantity) || 0));
      const radarData = profile.skills.map((skill) => ({
        label: skill.skill_name,
        value: Math.min(Number(skill.quantity) || 0, normalizer),
        max: normalizer,
      }));
      setEmployeeSkills(radarData);

      // Calculate match score if a job is selected
      if (selectedJob && jobSkills) {
        calculateMatchScore(radarData, jobSkills);
      }

      setLoading(false);
    }, 800);
  };

  const calculateMatchScore = (employeeData, jobData) => {
    let totalMatch = 0;
    let skillCount = 0;

    employeeData.forEach((empSkill) => {
      const jobSkill = jobData.find((js) => js.label === empSkill.label);
      if (jobSkill) {
        const empValue = empSkill.value;
        const jobValue = jobSkill.value;
        // Calculate match percentage (how close employee is to required level)
        const match = Math.min(100, (empValue / jobValue) * 100);
        totalMatch += match;
        skillCount++;
      }
    });

    const averageMatch = skillCount > 0 ? totalMatch / skillCount : 0;
    setMatchScore(Math.round(averageMatch));
  };

  useEffect(() => {
    // Recalculate match when either job or employee changes
    if (employeeSkills && jobSkills) {
      calculateMatchScore(employeeSkills, jobSkills);
    }
  }, [employeeSkills, jobSkills]);

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
        Find My Job
      </Typography>
      <Typography 
        variant="body1" 
        color="text.secondary"
        sx={{ mb: 4 }}
      >
        Search for job requirements or upload an employee profile to find the best match
      </Typography>

      <Grid container spacing={3}>
        {/* Left Box: Job Search */}
        <Grid item xs={12} md={6}>
          <Card sx={{ p: 3, backgroundColor: 'background.paper', boxShadow: 2, height: '100%' }}>
            <Typography 
              variant="h5" 
              component="h3" 
              sx={{ mb: 2, color: 'text.primary', fontWeight: 600 }}
            >
              Job Search
            </Typography>
            <Typography 
              variant="body2" 
              color="text.secondary"
              sx={{ mb: 2 }}
            >
              Search for a job position to see its required skills profile
            </Typography>

            {/* Available Jobs Quick Links */}
            <Box sx={{ mb: 3, display: 'flex', flexWrap: 'wrap', gap: 1 }}>
              <Typography variant="caption" color="text.secondary" sx={{ width: '100%', mb: 0.5 }}>
                Available jobs:
              </Typography>
              {mockJobs.map((job) => (
                <Chip
                  key={job.id}
                  label={job.title}
                  size="small"
                  onClick={() => {
                    setJobSearchQuery(job.title);
                    setTimeout(() => handleJobSearch(), 100);
                  }}
                  sx={{ 
                    cursor: 'pointer',
                    '&:hover': {
                      backgroundColor: 'primary.light',
                      color: 'primary.contrastText',
                    }
                  }}
                />
              ))}
            </Box>

            <Box sx={{ display: 'flex', gap: 1, mb: 3 }}>
              <TextField
                fullWidth
                placeholder="Search by job title, department, or keyword (e.g., 'Data', 'Manager', 'IT', 'HR')"
                value={jobSearchQuery}
                onChange={(e) => setJobSearchQuery(e.target.value)}
                onKeyPress={(e) => {
                  if (e.key === 'Enter') {
                    handleJobSearch();
                  }
                }}
                InputProps={{
                  startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />,
                }}
              />
              <Button
                variant="contained"
                onClick={handleJobSearch}
                disabled={loading}
                sx={{ minWidth: 100 }}
              >
                Search
              </Button>
            </Box>

            {error && (
              <Alert severity="error" sx={{ mb: 2 }}>
                {error}
              </Alert>
            )}

            {loading && (
              <Box sx={{ display: 'flex', justifyContent: 'center', my: 4 }}>
                <CircularProgress />
              </Box>
            )}

            {selectedJob && jobSkills && !loading && (
              <Box>
                <Paper sx={{ p: 2, mb: 3, backgroundColor: 'background.default' }}>
                  <Typography variant="h6" sx={{ mb: 1, fontWeight: 600 }}>
                    {selectedJob.title}
                  </Typography>
                  <Chip 
                    label={selectedJob.department} 
                    size="small" 
                    sx={{ mb: 1 }}
                  />
                  <Typography variant="body2" color="text.secondary">
                    Job ID: {selectedJob.id}
                  </Typography>
                </Paper>

                <Box sx={{ 
                  display: 'flex',
                  justifyContent: 'center',
                  alignItems: 'center',
                  flexDirection: 'column',
                }}>
                  <NetworkGraph
                    title="Job Skills"
                    data={jobSkills}
                    maxValue={Math.max(...jobSkills.map(d => d.value || 0))}
                    size={getNetworkGraphSize()}
                    centerNode={{ label: selectedJob.title, type: 'job' }}
                    loading={false}
                    error={null}
                  />
                </Box>
              </Box>
            )}
          </Card>
        </Grid>

        {/* Right Box: Employee Profile Upload */}
        <Grid item xs={12} md={6}>
          <Card sx={{ p: 3, backgroundColor: 'background.paper', boxShadow: 2, height: '100%' }}>
            <Typography 
              variant="h5" 
              component="h3" 
              sx={{ mb: 2, color: 'text.primary', fontWeight: 600 }}
            >
              Employee Profile Matching
            </Typography>
            <Typography 
              variant="body2" 
              color="text.secondary"
              sx={{ mb: 3 }}
            >
              Upload an employee profile to see if they match the selected job
            </Typography>

            <Button
              variant="outlined"
              fullWidth
              startIcon={<UploadFileIcon />}
              onClick={handleProfileUpload}
              disabled={loading}
              sx={{ mb: 3, py: 1.5 }}
            >
              Upload Employee Profile
            </Button>

            {employeeProfile && employeeSkills && !loading && (
              <Box>
                <Paper sx={{ p: 2, mb: 3, backgroundColor: 'background.default' }}>
                  <Typography variant="h6" sx={{ mb: 1, fontWeight: 600 }}>
                    {employeeProfile.name}
                  </Typography>
                  <Chip 
                    label={employeeProfile.position} 
                    size="small" 
                    sx={{ mb: 1 }}
                  />
                  <Typography variant="body2" color="text.secondary">
                    Employee ID: {employeeProfile.id}
                  </Typography>
                </Paper>

                <Box sx={{ 
                  display: 'flex',
                  justifyContent: 'center',
                  alignItems: 'center',
                  flexDirection: 'column',
                }}>
                  <Typography 
                    variant="h6" 
                    sx={{ mb: 2, fontWeight: 600, textAlign: 'center' }}
                  >
                    Employee Skills Profile
                  </Typography>
                  <RadarGraph
                    title="Employee Skills"
                    data={employeeSkills}
                    maxValue={Math.max(...employeeSkills.map(d => d.value || 0))}
                    levels={5}
                    loading={false}
                    error={null}
                    size={getChartSize()}
                    color="primary"
                  />
                </Box>
              </Box>
            )}

            {/* Match Score */}
            {matchScore !== null && selectedJob && employeeProfile && (
              <Box sx={{ mt: 3 }}>
                <Divider sx={{ my: 2 }} />
                <Paper 
                  sx={{ 
                    p: 3, 
                    backgroundColor: matchScore >= 80 ? 'success.light' : matchScore >= 60 ? 'warning.light' : 'error.light',
                    textAlign: 'center'
                  }}
                >
                  <Typography variant="h6" sx={{ mb: 1, fontWeight: 600 }}>
                    Match Score
                  </Typography>
                  <Typography 
                    variant="h3" 
                    sx={{ 
                      fontWeight: 700,
                      color: matchScore >= 80 ? 'success.dark' : matchScore >= 60 ? 'warning.dark' : 'error.dark'
                    }}
                  >
                    {matchScore}%
                  </Typography>
                  <Typography variant="body2" sx={{ mt: 1, color: 'text.secondary' }}>
                    {matchScore >= 80 
                      ? 'Excellent match! This employee is well-suited for this position.'
                      : matchScore >= 60 
                      ? 'Good match. Some skill development may be needed.'
                      : 'Limited match. Significant skill development required.'}
                  </Typography>
                </Paper>
              </Box>
            )}
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default FindMyJobDashboard;

