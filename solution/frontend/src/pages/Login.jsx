import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
  Box,
  Container,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  CircularProgress,
  Chip,
  Divider,
} from '@mui/material';
import { Logo } from '@skodaflow/web-library';
import { authAPI, analyticsAPI } from '../services/api';

// Helper function to determine user role based on username
// This is a fallback - ideally role should come from backend
const getUserRole = (username) => {
  const usernameUpper = username.trim().toUpperCase();
  
  // Check for specific test users first
  if (usernameUpper === '63398') {
    return 'hr';
  } else if (usernameUpper === '6249' || usernameUpper === '16950') {
    return 'manager';
  }
  
  // Fallback to keyword-based role detection
  if (usernameUpper.includes('HR')) {
    return 'hr';
  } else if (usernameUpper.includes('MANAGER')) {
    return 'manager';
  } else if (usernameUpper.includes('EMPLOYER')) {
    return 'employer';
  }
  
  return 'user';
};

const Login = () => {
  const [cardInserted, setCardInserted] = useState(false);
  const [cardId, setCardId] = useState('');
  const [pin, setPin] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const { login, isAuthenticated } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (isAuthenticated) {
      navigate('/');
    }
  }, [isAuthenticated, navigate]);

  const handleCardInsert = () => {
    setCardInserted(true);
    setError('');
  };

  const handleCardIdChange = (event) => {
    setCardId(event.target.value);
    setError('');
  };

  const handlePinChange = (event) => {
    const value = event.target.value.replace(/\D/g, '').slice(0, 4);
    setPin(value);
    setError('');
  };

  const handleQuickLogin = async (username, password) => {
    setCardId(username);
    setPin(password);
    setCardInserted(true);
    setError('');
    setLoading(true);

    try {
      // Call real authentication API
      const tokenResponse = await authAPI.login(username, password);
      
      // Store JWT token
      localStorage.setItem('access_token', tokenResponse.access_token);

      // Get user info from analytics API to get personal number
      let employeeInfo = null;
      try {
        employeeInfo = await analyticsAPI.getEmployee(username);
      } catch (err) {
        // Employee might not exist in analytics, use username as fallback
        console.warn('Could not fetch employee info:', err);
      }

      // Determine role (fallback to getUserRole if not in employee data)
      const role = getUserRole(username);
      
      // Create user info object
      const userInfo = {
        id: employeeInfo?.personal_number || username,
        username: username,
        cardId: username,
        personalNumber: employeeInfo?.personal_number || username,
        name: employeeInfo?.name || username,
        role: role,
        created_at: employeeInfo?.created_at || new Date().toISOString(),
      };

      login(userInfo);
      navigate('/');
    } catch (err) {
      setError(err.message || 'Authentication failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  const handleLogin = async () => {
    if (!cardId.trim()) {
      setError('Please enter your username');
      return;
    }

    if (pin.length < 4) {
      setError('Please enter your password');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const username = cardId.trim();
      
      // Call real authentication API
      const tokenResponse = await authAPI.login(username, pin);
      
      // Store JWT token
      localStorage.setItem('access_token', tokenResponse.access_token);

      // Get user info from analytics API to get personal number
      let employeeInfo = null;
      try {
        employeeInfo = await analyticsAPI.getEmployee(username);
      } catch (err) {
        // Employee might not exist in analytics, use username as fallback
        console.warn('Could not fetch employee info:', err);
      }

      // Determine role (fallback to getUserRole if not in employee data)
      const role = getUserRole(username);
      
      // Create user info object
      const userInfo = {
        id: employeeInfo?.personal_number || username,
        username: username,
        cardId: username,
        personalNumber: employeeInfo?.personal_number || username,
        name: employeeInfo?.name || username,
        role: role,
        created_at: employeeInfo?.created_at || new Date().toISOString(),
      };

      login(userInfo);
      navigate('/');
    } catch (err) {
      setError(err.message || 'Authentication failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container
      maxWidth="sm"
      sx={{
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '100vh',
        py: 4,
      }}
    >
      <Box sx={{ mb: 4, textAlign: 'center' }}>
        <Logo sx={{ height: 60, mb: 2 }} />
        <Typography variant="h4" component="h1" sx={{ mb: 1 }}>
          Welcome
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Please sign in to continue
        </Typography>
      </Box>

      <Card sx={{ width: '100%', maxWidth: 400 }}>
        <CardContent sx={{ p: 4 }}>
          {!cardInserted ? (
            <Box sx={{ textAlign: 'center' }}>
              <Box
                sx={{
                  width: 120,
                  height: 80,
                  mx: 'auto',
                  mb: 3,
                  border: '2px dashed',
                  borderColor: 'divider',
                  borderRadius: 2,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  backgroundColor: 'background.default',
                }}
              >
                <Typography variant="body2" color="text.secondary">
                  Card
                </Typography>
              </Box>
              <Button
                variant="contained"
                fullWidth
                onClick={handleCardInsert}
                sx={{ mt: 2 }}
              >
                Insert Card
              </Button>
            </Box>
          ) : (
            <Box>
              <Box
                sx={{
                  width: 120,
                  height: 80,
                  mx: 'auto',
                  mb: 3,
                  border: '2px solid',
                  borderColor: 'success.main',
                  borderRadius: 2,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  backgroundColor: 'success.light',
                }}
              >
                <Typography variant="body2" color="success.dark">
                  ✓ Ready
                </Typography>
              </Box>
              <TextField
                fullWidth
                label="Username"
                value={cardId}
                onChange={handleCardIdChange}
                error={Boolean(error && !cardId.trim())}
                helperText={error && !cardId.trim() ? error : ''}
                sx={{ mb: 3 }}
                autoFocus
              />
              <TextField
                fullWidth
                label="Password"
                type="password"
                value={pin}
                onChange={handlePinChange}
                inputProps={{
                  maxLength: 4,
                  inputMode: 'numeric',
                  pattern: '[0-9]*',
                }}
                error={Boolean(error && cardId.trim())}
                helperText={error && cardId.trim() ? error : ''}
                sx={{ mb: 3 }}
              />

              <Button
                variant="contained"
                fullWidth
                onClick={handleLogin}
                disabled={!cardId.trim() || pin.length !== 4 || loading}
                sx={{ mb: 2 }}
              >
                {loading ? <CircularProgress size={24} /> : 'Login'}
              </Button>
              <Button
                variant="text"
                fullWidth
                onClick={() => {
                  setCardInserted(false);
                  setCardId('');
                  setPin('');
                  setError('');
                }}
              >
                Cancel
              </Button>
            </Box>
          )}
        </CardContent>
      </Card>

      {/* Quick Login Buttons for Test Users */}
      <Box sx={{ mt: 3, width: '100%', maxWidth: 400 }}>
        <Divider sx={{ mb: 2 }}>
          <Chip label="Quick Login (Dev)" size="small" />
        </Divider>
        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', justifyContent: 'center' }}>
          {/* Common test users - passwords should match backend */}
          <Button
            variant="outlined"
            size="small"
            onClick={() => handleQuickLogin('63398', '0000')}
            disabled={loading}
            sx={{ minWidth: 120 }}
          >
            63398 (HR)
          </Button>
          <Button
            variant="outlined"
            size="small"
            onClick={() => handleQuickLogin('16710', '0000')}
            disabled={loading}
            sx={{ minWidth: 120 }}
          >
            16710 (User)
          </Button>
          <Button
            variant="outlined"
            size="small"
            onClick={() => handleQuickLogin('6249', '1111')}
            disabled={loading}
            sx={{ minWidth: 120 }}
          >
            6249 (Manager)
          </Button>
          <Button
            variant="outlined"
            size="small"
            onClick={() => handleQuickLogin('16950', '0000')}
            disabled={loading}
            sx={{ minWidth: 120 }}
          >
            16950 (Manager)
          </Button>
        </Box>
      </Box>
    </Container>
  );
};

export default Login;

