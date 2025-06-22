import React, { useState } from 'react';
import axios from 'axios';

const Register = () => {
  const [formData, setFormData] = useState({
    username: '',
    password: '',
    email: '',
    role: 'student', // default value
  });

  const [message, setMessage] = useState('');

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    try {
      const res = await axios.post('http://127.0.0.1:8000/api/register/', formData);
      setMessage('✅ Registered successfully. You can now log in.');
    } catch (error) {
      console.error(error);
      setMessage('❌ Registration failed. Try again.');
    }
  };

  return (
    <div>
      <h2>Register</h2>
      <form onSubmit={handleSubmit}>

        <input
          type="text"
          name="username"
          placeholder="Username"
          required
          onChange={handleChange}
        /><br />

        <input
          type="email"
          name="email"
          placeholder="Email"
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

        <select name="role" onChange={handleChange} defaultValue="student">
          <option value="student">Student</option>
          <option value="instructor">Instructor</option>
        </select><br />

        <button type="submit">Register</button>
      </form>

      {message && <p>{message}</p>}
    </div>
  );
};

export default Register;
