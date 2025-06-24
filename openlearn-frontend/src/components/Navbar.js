// src/components/Navbar.js

import React from 'react';
import { Link, useNavigate } from 'react-router-dom';

const Navbar = () => {
  const navigate = useNavigate();
  const accessToken = localStorage.getItem('access');

  const handleLogout = () => {
    localStorage.removeItem('access');
    localStorage.removeItem('refresh');
    navigate('/login');
  };

  return (
    <nav style={styles.nav}>
      <h2 style={styles.logo}>OpenLearn</h2>
      <div style={styles.links}>
        {!accessToken ? (
          <>
            <Link style={styles.link} to="/login">Login</Link>
            <Link style={styles.link} to="/register">Register</Link>
          </>
        ) : (
          <>
            <Link style={styles.link} to="/dashboard">Dashboard</Link>
            <button style={styles.button} onClick={handleLogout}>Logout</button>
          </>
        )}
      </div>
    </nav>
  );
};

const styles = {
  nav: {
    padding: '10px 20px',
    backgroundColor: '#282c34',
    color: 'white',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  logo: {
    margin: 0,
  },
  links: {
    display: 'flex',
    gap: '10px',
  },
  link: {
    color: 'white',
    textDecoration: 'none',
    fontSize: '16px',
  },
  button: {
    backgroundColor: '#61dafb',
    border: 'none',
    padding: '6px 12px',
    borderRadius: '4px',
    cursor: 'pointer',
  },
};

export default Navbar;
