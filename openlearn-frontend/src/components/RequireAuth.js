import React from 'react';
import { Navigate } from 'react-router-dom';

const RequireAuth = ({ children }) => {
  const accessToken = localStorage.getItem('access');

  if (!accessToken) {
    
    return <Navigate to="/login" replace />;
  }

  return children;
};

export default RequireAuth;
