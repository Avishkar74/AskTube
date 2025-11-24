import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import VideoPage from './pages/VideoPage';
import CoursePage from './pages/CoursePage';
import MobileUploadPage from './pages/MobileUploadPage';

const App: React.FC = () => {
  return (
    <Router>
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-white font-sans">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/video/:id" element={<VideoPage />} />
          <Route path="/course/:courseId" element={<CoursePage />} />
          <Route path="/mobile-upload/:videoId" element={<MobileUploadPage />} />
        </Routes>
      </div>
    </Router>
  );
};

export default App;
