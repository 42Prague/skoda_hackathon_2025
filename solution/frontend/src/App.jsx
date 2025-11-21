import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import ManagerRoute from './components/ManagerRoute';
import UserRoute from './components/UserRoute';
import Navbar from './components/Navbar';
import Login from './pages/Login';
import Home from './pages/Home';
import ChatPage from './pages/ChatPage';
import Dashboard from './pages/Dashboard';
import UserManagement from './pages/UserManagement';
import { BypassBlock } from '@skodaflow/web-library';
import { Box } from '@mui/material';
import DashboardManager from './pages/Dashboard_manager';

// Component to handle manager/HR redirect from home
const HomeRoute = () => {
  const { isManager, isHR, loading } = useAuth();
  
  if (loading) {
    return null;
  }
  
  if (isManager) {
    return <Navigate to="/dashboard-manager" replace />;
  }
  
  if (isHR) {
    return <Navigate to="/dashboard-hr" replace />;
  }
  
  return <Home />;
};

function App() {
  return (
    <AuthProvider>
      <BypassBlock href="#main">Skip to content</BypassBlock>
      <Router>
        <Box sx={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
          <Navbar />
          <Box id="main" component="main" sx={{ flexGrow: 1 }}>
            <Routes>
              <Route path="/login" element={<Login />} />
              <Route
                path="/"
                element={
                  <ProtectedRoute>
                    <HomeRoute />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/chat"
                element={
                  <UserRoute>
                    <ChatPage />
                  </UserRoute>
                }
              />
              <Route
                path="/dashboard"
                element={
                  <UserRoute>
                    <Dashboard />
                  </UserRoute>
                }
              />
              <Route
                path="/dashboard-manager"
                element={
                  <DashboardManager />
                }
              />
              <Route
                path="/dashboard-hr"
                element={
                  <DashboardManager />
                }
              />
              <Route
                path="/users"
                element={
                  <ManagerRoute>
                    <UserManagement />
                  </ManagerRoute>
                }
              />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </Box>
        </Box>
      </Router>
    </AuthProvider>
  );
}

export default App;

