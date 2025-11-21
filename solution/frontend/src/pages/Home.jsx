import { Box, Container, Typography, Card, CardContent, Grid, Button, Chip } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { ArrowRightIcon } from '@skodaflow/web-library';

const Home = () => {
  const navigate = useNavigate();
  const { user, isHR, isManager } = useAuth();

  // Redirect managers to their dashboard
  if (isManager) {
    navigate('/dashboard-manager');
    return null;
  }

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Box>
          <Typography variant="h3" component="h1" sx={{ mb: 2 }}>
            Welcome, {user?.name || 'User'}
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ mb: 2 }}>
            Your ŠKODA Portal Dashboard
          </Typography>
        </Box>
        {isHR && (
          <Chip label="HR" color="primary" sx={{ height: 32 }} />
        )}
      </Box>

      {!isHR && (
        // Regular User view - Chat and Dashboard
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Card sx={{ height: '100%' }}>
              <CardContent sx={{ p: 4 }}>
                <Typography variant="h5" component="h2" sx={{ mb: 2 }}>
                  AI Chat Assistant
                </Typography>
                <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
                  Get instant answers to your questions using our AI-powered chatbot with RAG capabilities.
                </Typography>
                <Button
                  variant="contained"
                  endIcon={<ArrowRightIcon />}
                  onClick={() => navigate('/chat')}
                  fullWidth
                >
                  Open Chat
                </Button>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={6}>
            <Card sx={{ height: '100%' }}>
              <CardContent sx={{ p: 4 }}>
                <Typography variant="h5" component="h2" sx={{ mb: 2 }}>
                  Analytics Dashboard
                </Typography>
                <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
                  View detailed analytics and insights about your data and performance metrics.
                </Typography>
                <Button
                  variant="contained"
                  color="surface"
                  endIcon={<ArrowRightIcon />}
                  onClick={() => navigate('/dashboard')}
                  fullWidth
                >
                  View Dashboard
                </Button>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}
    </Container>
  );
};

export default Home;

