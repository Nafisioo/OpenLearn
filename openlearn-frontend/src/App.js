import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Register from './pages/Register';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import RequireAuth from './components/RequireAuth';
import Navbar from './components/Navbar';
import CourseList from './pages/CourseList';
import CourseDetail from './pages/CourseDetail'; 
import axiosInstance from './axiosInstance';

function App() {
  return (
    <Router>
      <Navbar />
      <Routes>
        <Route path="/register" element={<Register />} />
        <Route path="/login" element={<Login />} />
        <Route
          path="/dashboard"
          element={
            <RequireAuth>
              <Dashboard />
            </RequireAuth>
          }
        />
        <Route path="/courses" element={<CourseList />} />
        <Route path="/courses/:pk" element={<CourseDetail />} /> 
      </Routes>
    </Router>
  );
}

export default App;
