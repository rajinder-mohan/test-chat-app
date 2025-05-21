import React, { createContext, useState, useEffect, useContext } from 'react';
import { AuthService } from '../services/auth';

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [currentUser, setCurrentUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  useEffect(() => {
    const fetchUser = async () => {
      if (AuthService.isAuthenticated()) {
        try {
          const response = await AuthService.getCurrentUser();
          setCurrentUser(response.data);
        } catch (err) {
          console.error('Failed to fetch user:', err);
          AuthService.logout();
        } finally {
          setLoading(false);
        }
      } else {
        setLoading(false);
      }
    };
    
    fetchUser();
  }, []);
  
  const login = async (username, password) => {
    try {
      setError(null);
      const data = await AuthService.login(username, password);
      const userResponse = await AuthService.getCurrentUser();
      setCurrentUser(userResponse.data);
      return data;
    } catch (err) {
      setError(err.response?.data?.detail || 'Login failed');
      throw err;
    }
  };
  
  const register = async (username, email, password) => {
    try {
      setError(null);
      const data = await AuthService.register(username, email, password);
      return data;
    } catch (err) {
      setError(err.response?.data?.detail || 'Registration failed');
      throw err;
    }
  };
  
  const logout = () => {
    AuthService.logout();
    setCurrentUser(null);
  };
  
  const value = {
    currentUser,
    loading,
    error,
    login,
    register,
    logout,
    isAuthenticated: AuthService.isAuthenticated
  };
  
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => useContext(AuthContext); 