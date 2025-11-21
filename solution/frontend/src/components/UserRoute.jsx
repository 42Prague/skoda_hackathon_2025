import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { CircularProgress, Box } from '@mui/material';

const UserRoute = ({ children }) => {
  const { isAuthenticated, isUser, loading } = useAuth();

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  // Allow regular users, HR, and managers to access user routes
  // (HR/Manager can view employee dashboards)
  return children;
};

export default UserRoute;

