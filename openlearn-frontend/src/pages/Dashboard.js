import React, { useEffect, useState } from 'react';
import axiosInstance from '../axiosInstance';

function Dashboard() {
  const [message, setMessage] = useState('');

  useEffect(() => {
    axiosInstance.get('/api/dashboard/')
      .then(res => {
        setMessage(`👋 Welcome, ${res.data.username || 'User'}!`);
      })
      .catch(err => {
        console.error(err);
        setMessage('❌ Unauthorized or session expired.');
      });
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('access');
    localStorage.removeItem('refresh');
    window.location.href = '/login';
  };

  return (
    <div style={{ maxWidth: 400, margin: 'auto' }}>
      <h2>Dashboard</h2>
      <p>{message}</p>

      {localStorage.getItem('access') && (
        <button onClick={handleLogout} style={{ marginTop: '20px' }}>
          🚪 Logout
        </button>
      )}
    </div>
  );
}

export default Dashboard;

