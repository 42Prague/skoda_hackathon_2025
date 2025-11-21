import { useState, useEffect } from 'react';
import { 
  Box, 
  Typography, 
  Card, 
  CircularProgress, 
  Alert
} from '@mui/material';

const LearningRecommendationDashboard = ({ employeeId }) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [recommendations, setRecommendations] = useState(null);

  useEffect(() => {
    const fetchHistoryCourse = async () => {
      // Debug logging
      console.log('LearningRecommendationDashboard: Received employeeId prop:', employeeId, typeof employeeId);
      
      // Validate employeeId - must be a valid string and not "id" or "undefined"
      // Also handle numbers (convert to string) and allow non-string types
      if (!employeeId) {
        setError('Invalid employee ID: employeeId is missing');
        setLoading(false);
        console.error('LearningRecommendationDashboard: employeeId is missing or falsy');
        return;
      }
      
      // Convert to string if needed (handles numbers, etc.)
      const employeeIdStr = String(employeeId);
      
      if (employeeIdStr === 'id' || employeeIdStr === 'undefined' || employeeIdStr.trim() === '') {
        setError(`Invalid employee ID: "${employeeIdStr}"`);
        setLoading(false);
        console.error('LearningRecommendationDashboard: Invalid employeeId value:', employeeId, employeeIdStr);
        return;
      }
      
      // Strip any suffix like ":1" from employeeId
      const cleanEmployeeId = employeeIdStr.split(':')[0].trim();
      
      if (!cleanEmployeeId) {
        setError('Employee ID is required');
        setLoading(false);
        return;
      }
      
      setLoading(true);
      setError(null);
      
      try {
        const response = await fetch(`/api/stats/courses/${cleanEmployeeId}`);
        if (!response.ok) {
          throw new Error('Failed to fetch history course');
        }
        const data = await response.json(); // Get as JSON array
        // Format the data as a string
        if (Array.isArray(data) && data.length > 0) {
          const formattedText = data.map((course, index) => {
            return `${index + 1}. ${course.content_title || 'Unknown Course'} - ${course.content_provider || 'Unknown Provider'} (Completed: ${course.completed_date || 'N/A'})`;
          }).join('\n');
          setRecommendations(`Course History for Employee ${cleanEmployeeId}:\n\n${formattedText}`);
        } else {
          setRecommendations(`No course history found for employee ${cleanEmployeeId}`);
        }
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchHistoryCourse();
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
        Error loading history course: {error}
      </Alert>
    );
  }

  if (!recommendations) {
    return (
      <Alert severity="info" sx={{ mb: 2 }}>
        No history course available.
      </Alert>
    );
  }

  // recommendations is now a string from the API
  const courseHistoryText = recommendations;

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
        History Course
      </Typography>

      {/* Course History Display */}
      <Card 
        sx={{ 
          p: 3,
          backgroundColor: 'background.paper',
          boxShadow: 2
        }}
      >
        <Typography 
          variant="body1" 
          component="pre"
          sx={{ 
            color: 'text.primary',
            whiteSpace: 'pre-wrap',
            fontFamily: 'monospace',
            mb: 2
          }}
        >
          {courseHistoryText}
        </Typography>
      </Card>
    </Box>
  );
};

export default LearningRecommendationDashboard;

