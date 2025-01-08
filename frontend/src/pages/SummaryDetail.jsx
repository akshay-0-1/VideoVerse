import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';

function SummaryDetail() {
  const { id } = useParams(); // Retrieve the summary ID from the URL
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Fetch the detailed summary by ID
    const fetchSummary = async () => {
      try {
        const token = localStorage.getItem('userToken');
        const response = await fetch(`http://localhost:8000/api/summaries/${id}`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        const data = await response.json();
        setSummary(data);
      } catch (error) {
        console.error('Error:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchSummary();
  }, [id]);

  if (loading) {
    return <p className="text-center">Loading summary...</p>;
  }

  if (!summary) {
    return <p className="text-center">Summary not found.</p>;
  }

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-4xl mx-auto bg-white p-8 rounded-lg shadow-md">
        <h1 className="text-3xl font-bold mb-6">{summary.title}</h1>
        <p className="text-gray-600 mb-4">{summary.content}</p>
        <div className="flex justify-between items-center text-sm text-gray-500">
          <span>
            Saved on: {new Date(summary.createdAt).toLocaleDateString()}
          </span>
          <a 
            href={summary.originalUrl} 
            target="_blank" 
            rel="noopener noreferrer"
            className="text-blue-500 hover:text-blue-700"
          >
            View Original Article
          </a>
        </div>
      </div>
    </div>
  );
}

export default SummaryDetail;
