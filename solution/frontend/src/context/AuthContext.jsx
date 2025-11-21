import { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState(null);
  const [selectedUser, setSelectedUser] = useState(null); // For HR/Manager viewing other users
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check localStorage for existing session
    const storedAuth = localStorage.getItem('isAuthenticated');
    const storedUser = localStorage.getItem('user');
    const storedToken = localStorage.getItem('access_token');
    
    if (storedAuth === 'true' && storedUser && storedToken) {
      setIsAuthenticated(true);
      setUser(JSON.parse(storedUser));
    }
    setLoading(false);
  }, []);

  const login = (userData) => {
    setIsAuthenticated(true);
    setUser(userData);
    localStorage.setItem('isAuthenticated', 'true');
    localStorage.setItem('user', JSON.stringify(userData));
    // Token is already stored in Login component
  };

  const logout = () => {
    setIsAuthenticated(false);
    setUser(null);
    setSelectedUser(null);
    localStorage.removeItem('isAuthenticated');
    localStorage.removeItem('user');
    localStorage.removeItem('access_token');
  };

  const isHR = user?.role === 'hr';
  const isManager = user?.role === 'manager';
  const isUser = user?.role === 'user' || user?.role === 'employee';

  // When HR/Manager is viewing another user, use selectedUser, otherwise use logged-in user
  const currentViewingUser = selectedUser || user;

  return (
    <AuthContext.Provider value={{ 
      isAuthenticated, 
      user, 
      selectedUser,
      currentViewingUser,
      setSelectedUser,
      login, 
      logout, 
      loading,
      isHR,
      isManager,
      isUser,
    }}>
      {children}
    </AuthContext.Provider>
  );
};

