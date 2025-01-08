import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';

function SavedSummaries() {
  const [summaries, setSummaries] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Fetch saved summaries
    const fetchSummaries = async () => {
      try {
        const token = localStorage.getItem('userToken');
        const response = await fetch('http://localhost:8000/api/summaries', {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });
        const data = await response.json();
        console.log('Fetched Data:', data); // Log the fetched data
        setSummaries(data);
      } catch (error) {
        console.error('Error:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchSummaries();
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('userToken');
    window.location.href = '/login';
  };

  const handleDelete = async (summaryId) => {
    try {
      const token = localStorage.getItem('userToken');
      const response = await fetch(`http://localhost:5000/api/summaries/${summaryId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        // Remove the deleted summary from state
        setSummaries(summaries.filter(summary => summary._id !== summaryId));
      } else {
        console.error('Failed to delete summary');
      }
    } catch (error) {
      console.error('Error deleting summary:', error);
    }
  };

  return (
    <div className="bg-gradient-to-br from-blue-900 via-indigo-700 to-blue-900 min-h-screen text-white flex flex-col">
      {/* Navbar */}
      <div className="flex justify-between  p-4 bg-black bg-opacity-80 shadow-xl">
        <div className="text-2xl font-bold text-white">
          <Link to="/" className="hover:text-purple-300">AI Summarizer</Link>
        </div>
        <div className="flex space-x-6">
          <Link to="/main" className="text-white hover:text-purple-300">Home</Link>
          <Link to="/saved-summaries" className="text-white hover:text-purple-300">Saved Summaries</Link>
          <button onClick={() => window.location.href = '/login'} className="text-white hover:text-purple-300">Logout</button>
        </div>
      </div>

      {/* Centered Content */}
      <div className="flex flex-1  p-8">
        <div className="bg-gradient-to-br from-indigo-800 via-purple-600 to-indigo-800 p-12 rounded-lg shadow-2xl w-full max-w-8xl">
          <h1 className="text-3xl font-bold text-center text-purple-100 mb-8">Saved Summaries</h1>

          {loading ? (
            <p className="text-center text-lg text-gray-400">Loading summaries...</p>
          ) : summaries.length === 0 ? (
            <p className="text-center text-lg text-gray-500">No saved summaries yet.</p>
          ) : (
            <div className="flex flex-col space-y-4">
              {summaries.map((summary) => (
                <div
                  key={summary._id}
                  className="bg-white p-6 rounded-lg shadow-lg w-full"
                >
                  <div className="flex justify-between items-start mb-2">
                    <h2 className="text-xl font-semibold text-purple-600">
                      <Link to={`/summary/${summary._id}`} className="hover:text-purple-700">
                        {summary.title}
                      </Link>
                    </h2>
                    <button
                      onClick={() => handleDelete(summary._id)}
                      className="text-red-500 hover:text-red-700 px-3 py-1 rounded-md hover:bg-red-50 transition-colors"
                    >
                      Delete
                    </button>
                  </div>
                  <p className="text-gray-600 text-base mb-3">
                    {summary.content.substring(0, 200)}...
                  </p>
                  <div className="flex justify-between items-center text-sm text-gray-500">
                    <span>
                      Saved on: {new Date(summary.createdAt).toLocaleDateString()}
                    </span>
                    <a
                      href={summary.originalUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-purple-600 hover:text-purple-800"
                    >
                      View Original Article
                    </a>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default SavedSummaries;
