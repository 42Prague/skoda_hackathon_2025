import { useState, useEffect } from 'react';
import { 
  Box, 
  Typography, 
  Card, 
  CardContent, 
  CircularProgress, 
  Alert,
  Grid,
  Chip,
  Divider
} from '@mui/material';
import { useAuth } from '../../context/AuthContext';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ScheduleIcon from '@mui/icons-material/Schedule';
import { statsAPI, analyticsAPI } from '../../services/api';

const CourseHistoryDashboard = ({ employeeId }) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [courseHistory, setCourseHistory] = useState(null);

  useEffect(() => {
    const fetchCourseHistory = async () => {
      if (!employeeId) {
        setLoading(false);
        return;
      }
      
      setLoading(true);
      setError(null);
      
      try {
        // Clean employee ID
        const cleanEmployeeId = String(employeeId).split(':')[0].trim();
        
        // Try to fetch from Degreed activity endpoint first
        let courses = [];
        try {
          const degreedData = await analyticsAPI.getDegreedActivity(cleanEmployeeId);
          courses = degreedData.map((item, index) => ({
            id: index + 1,
            title: item.content_title || 'Unknown Course',
            provider: item.provider || 'Unknown Provider',
            completedDate: item.completion_date || null,
            status: 'completed',
            duration: item.estimated_time_minutes ? Math.round(item.estimated_time_minutes / 60) : 0,
            score: item.completion_rating || null,
            category: item.category || item.content_type || 'General',
          }));
        } catch (degreedErr) {
          // Fallback to stats API
          try {
            const statsCourses = await statsAPI.getEmployeeCourses(cleanEmployeeId);
            courses = statsCourses.map((item, index) => ({
              id: index + 1,
              title: item.content_title || 'Unknown Course',
              provider: item.content_provider || 'Unknown Provider',
              completedDate: item.completed_date || null,
              status: 'completed',
              duration: item.estimated_learning_minutes ? Math.round(item.estimated_learning_minutes / 60) : 0,
              score: item.completion_rating || null,
              category: item.content_type || 'General',
            }));
          } catch (statsErr) {
            console.warn('Both course endpoints failed:', { degreedErr, statsErr });
            courses = [];
          }
        }
        
        // Calculate summary statistics
        const totalCourses = courses.length;
        const totalHours = courses.reduce((sum, c) => sum + (c.duration || 0), 0);
        const scores = courses.filter(c => c.score !== null && c.score !== undefined).map(c => c.score);
        const averageScore = scores.length > 0 
          ? scores.reduce((sum, s) => sum + s, 0) / scores.length 
          : null;
        
        setCourseHistory({
          courses,
          totalCourses,
          totalHours,
          averageScore,
        });
      } catch (err) {
        setError(err.message || 'Failed to fetch course history');
        console.error('Error fetching course history:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchCourseHistory();
  }, [employeeId]);

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 400 }}>
        <CircularProgress />
      </Box>
    );
  }

  // Use course history from API
  const history = courseHistory || { courses: [], totalCourses: 0, totalHours: 0, averageScore: null };
  const courses = history.courses || [];

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'in-progress':
        return 'warning';
      case 'not-started':
        return 'default';
      default:
        return 'default';
    }
  };

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
        Course History
      </Typography>

      {/* Summary Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={4}>
          <Card 
            sx={{ 
              p: 3,
              backgroundColor: 'background.paper',
              boxShadow: 2,
              textAlign: 'center'
            }}
          >
            <Typography 
              variant="h3" 
              component="div" 
              sx={{ 
                color: 'brand.primary',
                fontWeight: 700,
                mb: 1
              }}
            >
              {history.totalCourses || courses.length}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Total Courses Completed
            </Typography>
          </Card>
        </Grid>
        <Grid item xs={12} sm={4}>
          <Card 
            sx={{ 
              p: 3,
              backgroundColor: 'background.paper',
              boxShadow: 2,
              textAlign: 'center'
            }}
          >
            <Typography 
              variant="h3" 
              component="div" 
              sx={{ 
                color: 'brand.primary',
                fontWeight: 700,
                mb: 1
              }}
            >
              {history.totalHours || courses.reduce((sum, c) => sum + (c.duration || 0), 0)}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Total Hours
            </Typography>
          </Card>
        </Grid>
        <Grid item xs={12} sm={4}>
          <Card 
            sx={{ 
              p: 3,
              backgroundColor: 'background.paper',
              boxShadow: 2,
              textAlign: 'center'
            }}
          >
            <Typography 
              variant="h3" 
              component="div" 
              sx={{ 
                color: 'brand.primary',
                fontWeight: 700,
                mb: 1
              }}
            >
              {history.averageScore 
                ? Math.round(history.averageScore) 
                : courses.length > 0 
                  ? Math.round(courses.reduce((sum, c) => sum + (c.score || 0), 0) / courses.length)
                  : 0}%
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Average Score
            </Typography>
          </Card>
        </Grid>
      </Grid>

      {/* Course List */}
      <Typography 
        variant="h5" 
        component="h3" 
        sx={{ 
          mb: 3,
          color: 'text.primary',
          fontWeight: 600
        }}
      >
        Completed Courses
      </Typography>

      {courses.length > 0 ? (
        <Grid container spacing={3}>
          {courses.map((course) => (
            <Grid item xs={12} key={course.id || course.title}>
              <Card 
                sx={{ 
                  backgroundColor: 'background.paper',
                  boxShadow: 2,
                  transition: 'transform 0.2s, box-shadow 0.2s',
                  '&:hover': {
                    transform: 'translateY(-2px)',
                    boxShadow: 4,
                  }
                }}
              >
                <CardContent>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                    <Box sx={{ flexGrow: 1 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                        <CheckCircleIcon sx={{ color: 'success.main', fontSize: 20 }} />
                        <Typography 
                          variant="h6" 
                          component="h4" 
                          sx={{ 
                            color: 'text.primary',
                            fontWeight: 600
                          }}
                        >
                          {course.title}
                        </Typography>
                      </Box>
                      {course.category && (
                        <Chip 
                          label={course.category} 
                          size="small" 
                          sx={{ mb: 1 }}
                          color="primary"
                        />
                      )}
                      <Typography 
                        variant="body2" 
                        sx={{ color: 'text.secondary', mt: course.category ? 0 : 1 }}
                      >
                        {course.provider || 'Provider not specified'}
                      </Typography>
                    </Box>
                    <Chip 
                      label={course.status || 'completed'} 
                      color={getStatusColor(course.status || 'completed')}
                      size="small"
                    />
                  </Box>
                  <Divider sx={{ my: 2 }} />
                  <Grid container spacing={2}>
                    <Grid item xs={12} sm={4}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <ScheduleIcon sx={{ color: 'text.secondary', fontSize: 18 }} />
                        <Typography variant="body2" color="text.secondary">
                          Completed: {formatDate(course.completedDate)}
                        </Typography>
                      </Box>
                    </Grid>
                    <Grid item xs={12} sm={4}>
                      <Typography variant="body2" color="text.secondary">
                        Duration: {course.duration || 'N/A'} hours
                      </Typography>
                    </Grid>
                    <Grid item xs={12} sm={4}>
                      <Typography variant="body2" color="text.secondary">
                        Score: <strong style={{ color: course.score >= 90 ? 'green' : course.score >= 80 ? 'orange' : 'red' }}>
                          {course.score || 'N/A'}%
                        </strong>
                      </Typography>
                    </Grid>
                  </Grid>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      ) : (
        <Alert severity="info">No course history available.</Alert>
      )}
    </Box>
  );
};

export default CourseHistoryDashboard;

