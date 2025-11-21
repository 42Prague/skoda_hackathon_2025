import { AppBar, Toolbar, Button, Box, Chip } from '@mui/material';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Typography, Logo } from '@skodaflow/web-library';

const Navbar = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { isAuthenticated, user, logout, isHR, isManager, selectedUser, setSelectedUser } = useAuth();

  if (!isAuthenticated) {
    return null;
  }

  return (
    <AppBar position="static" sx={{ backgroundColor: 'surface.main' }}>
      <Toolbar>
        <Box sx={{ display: 'flex', alignItems: 'center', flexGrow: 1 }}>
          <Logo sx={{ height: 40, mr: 2 }} />
          <Typography variant="subheadline" component="div" sx={{ color: 'onSurface.main', fontWeight: 'bold' }}>
            ŠKODA Portal
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          {!isManager && (
            <Button
              color={location.pathname === '/' ? 'primary' : 'inherit'}
              onClick={() => navigate('/')}
              sx={{ color: location.pathname === '/' ? 'primary.main' : 'text.primary' }}
            >
              Home
            </Button>
          )}
          <Button
            color={(location.pathname === '/dashboard' || location.pathname === '/dashboard-manager' || location.pathname === '/dashboard-hr') ? 'primary' : 'inherit'}
            onClick={() => navigate(`/dashboard${isManager ? '-manager' : isHR ? '-hr' : ''}`)}
            sx={{ color: (location.pathname === '/dashboard' || location.pathname === '/dashboard-manager' || location.pathname === '/dashboard-hr') ? 'primary.main' : 'text.primary' }}
          >
            Dashboard
          </Button>
          {!isHR && !isManager && (
            <>
              <Button
                color={location.pathname === '/chat' ? 'primary' : 'inherit'}
                onClick={() => navigate('/chat')}
                sx={{ color: location.pathname === '/chat' ? 'primary.main' : 'text.primary' }}
              >
                Chat
              </Button>
            </>
          )}
          {user && (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mr: 1 }}>
              <Typography variant="body2" sx={{ color: 'text.primary' }}>
                {selectedUser ? `Viewing: ${selectedUser.name}` : user.name}
              </Typography>
              {isHR && (
                <Chip 
                  label={selectedUser ? "Viewing User" : "HR"} 
                  size="small" 
                  color={selectedUser ? "info" : "primary"} 
                  sx={{ height: 20 }} 
                />
              )}
            </Box>
          )}
          {(isHR || isManager) && selectedUser && (
            <Button
              variant="text"
              size="small"
              onClick={() => {
                setSelectedUser(null);
                navigate('/users');
              }}
              sx={{ mr: 1 }}
            >
              Back to Users
            </Button>
          )}
          <Button
            variant="outlined"
            color="secondary"
            onClick={() => {
              logout();
              navigate('/login');
            }}
          >
            Logout
          </Button>
        </Box>
      </Toolbar>
    </AppBar>
  );
};

export default Navbar;

