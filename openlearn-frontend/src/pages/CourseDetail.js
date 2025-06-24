import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import axiosInstance from '../axiosInstance';

const CourseDetail = () => {
  const { id } = useParams();
  const [course, setCourse] = useState(null);

  useEffect(() => {
    axiosInstance.get(`/api/courses/${id}/`)
      .then((res) => {
        setCourse(res.data);
      })
      .catch((err) => {
        console.error("❌ Failed to fetch course details:", err);
      });
  }, [id]);

  if (!course) return <p>Loading course...</p>;

  return (
    <div style={{ padding: "1rem" }}>
      <h2>{course.title}</h2>
      <p>{course.description}</p>
      <small>Created at: {new Date(course.created_at).toLocaleString()}</small>
    </div>
  );
};

export default CourseDetail;
