import React, { useState } from 'react';
import axios from 'axios';

const Login = () => {
  const [credentials, setCredentials] = useState({
    username: '',
    password: ''
  });

  const [message, setMessage] = useState('');

  const handleChange = (e) => {
    setCredentials({
      ...credentials,
      [e.target.name]: e.target.value
    });
  };

  const handleLogin = async (e) => {
    e.preventDefault();

    try {
      const res = await axios.post('http://127.0.0.1:8000/api/token/', credentials);

      // Save tokens to localStorage
      localStorage.setItem('access_token', res.data.access);
      localStorage.setItem('refresh_token', res.data.refresh);

      setMessage('✅ Logged in successfully!');
    } catch (error) {
      console.error(error);
      setMessage('❌ Login failed. Check your credentials.');
    }
  };

  return (
    <div>
      <h2>Login</h2>
      <form onSubmit={handleLogin}>
        <input
          type="text"
          name="username"
          placeholder="Username"
          required
          onChange={handleChange}
        /><br />

        <input
          type="password"
          name="password"
          placeholder="Password"
          required
          onChange={handleChange}
        /><br />

        <button type="submit">Login</button>
      </form>

      {message && <p>{message}</p>}
    </div>
  );
};

export default Login;
