import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';

function ForgotPassword() {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage('');

    try {
      const response = await fetch('http://localhost:8000/api/forgot-password', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email }),
      });

      const data = await response.json();

      if (response.ok) {
        setMessage('Check your email for a password reset link.');
      } else {
        setMessage(data.message || 'Failed to send reset link.');
      }
    } catch (err) {
      console.error('Error:', err);
      setMessage('Server error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex justify-center items-center min-h-screen bg-gray-200">
      <motion.div
        className="w-full max-w-md p-8 bg-white shadow-xl rounded-lg"
        initial={{ opacity: 0, scale: 0.8 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5 }}
      >
        <h2 className="text-3xl font-bold text-center mb-4">Forgot Password</h2>
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label className="block text-gray-700" htmlFor="email">Email</label>
            <input
              type="email"
              id="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full mt-2 p-3 border border-gray-300 rounded-md"
              placeholder="Enter your email"
              required
            />
          </div>
          {message && (
            <div className="mb-4 text-gray-600 text-sm text-center">
              {message}
            </div>
          )}
          <button
            type="submit"
            disabled={loading}
            className={`w-full py-3 bg-indigo-600 text-white font-semibold rounded-md 
              ${loading ? 'opacity-50 cursor-not-allowed' : 'hover:bg-indigo-700'}`}
          >
            {loading ? 'Sending...' : 'Send Reset Link'}
          </button>
        </form>
      </motion.div>
    </div>
  );
}

export default ForgotPassword; 