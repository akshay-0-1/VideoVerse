import { useState } from 'react';
import SummaryBlock from '../components/SummaryBlock';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { toast, ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

export default function MainPage() {
  const [url, setUrl] = useState('');
  const [summary, setSummary] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSummarize = async (e) => {
    e.preventDefault();

    if (!url) {
      toast.error('Please enter a valid YouTube URL');
      return;
    }

    // Get the token from localStorage
    const token = localStorage.getItem('userToken');
    if (!token) {
      toast.error('Please login first');
      window.location.href = '/login';
      return;
    }

    setIsLoading(true);
    try {
      const response = await fetch('http://localhost:8000/api/generate-summary/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ link: url }),
        credentials: 'include',
      });

      // Check if response is redirect to login
      if (response.redirected) {
        toast.error('Session expired. Please login again');
        window.location.href = '/login';
        return;
      }

      console.log(response)

      const data = await response.json();

      if (data.success) {
        setSummary(data.summary.content);
        toast.success('Summary generated successfully!');
      } else {
        const errorMessage = data.error || 'Failed to generate summary';
        toast.error(errorMessage);
      }
    } catch (error) {
      console.error('Error:', error);
      toast.error('Failed to generate summary. Please try again.');
    } finally {
      setIsLoading(false);
      setUrl('');
    }
  };

  const handleLogout = () => {
    // Clear the token from localStorage and redirect to login page
    localStorage.removeItem('userToken');
    window.location.href = '/login'; // Redirect to login page
  };

  return (
    <div className="bg-gradient-to-br from-gray-900 via-purple-800 to-gray-900 min-h-screen text-white flex flex-col">
      {/* Navbar */}
      <div className="flex justify-between items-center p-4 bg-black bg-opacity-70 shadow-lg">
        <div className="text-xl font-bold text-white">
          <Link to="/" className="hover:underline">AI Summarizer</Link> {/* Replace with your logo */}
        </div>
        <div className="flex space-x-6">
          <Link to="/main" className="text-white hover:underline">Home</Link>
          <Link to="/saved-summaries" className="text-white hover:underline">Saved Summaries</Link>
          <button onClick={handleLogout} className="text-white hover:underline">Logout</button>
        </div>
      </div>

      {/* Centered Content */}
      <div className="flex flex-1 items-center justify-center">
        <motion.div
          className="bg-gray-800 bg-opacity-80 p-10 rounded-lg shadow-xl w-full max-w-[600px]"
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5 }}
        >
          <h2 className="text-3xl font-extrabold text-center mb-6">
            Summarize YouTube Videos
          </h2>
          <form onSubmit={handleSummarize}>
            <input
              type="text"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="Enter YouTube Video URL"
              className="w-full p-3 text-gray-900 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500 mb-4"
            />
            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-3 rounded-md bg-purple-600 hover:bg-purple-700 transition-all duration-300 font-semibold text-white"
            >
              {isLoading ? 'Generating...' : 'Generate Summary'}
            </button>
          </form>

          {/* Render SummaryBlock only if summary is available */}
          {summary && (
            <div className="mt-6">
              <SummaryBlock summary={summary} />
            </div>
          )}
        </motion.div>
      </div>

      {/* Toast Notifications Container */}
      <ToastContainer />
    </div>
  );
}
