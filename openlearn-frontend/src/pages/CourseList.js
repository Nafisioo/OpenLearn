import React, { useEffect, useState } from 'react';
import axiomInstance from '../axiosInstance';


const CourseList = () => {
  const [courses, setCourses] = useState([]);

  useEffect(() => {
    axiomInstance.get('/courses/')
      .then(res => {
        setCourses(res.data);
      })
      .catch(err => {
        console.error('Error fetching courses:', err);
      });
  }, []);

  return (
    <div style={{ padding: '20px' }}>
      <h2>Available Courses</h2>
      {courses.length === 0 ? (
        <p>No courses available.</p>
      ) : (
        <ul>
          {courses.map(course => (
            <li key={course.id}>
              <strong>{course.title}</strong> - {course.description}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default CourseList;
