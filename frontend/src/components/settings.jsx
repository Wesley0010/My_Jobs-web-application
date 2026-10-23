import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import './Auth.css'; 

export default function Settings() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    username: '', email: '', first_name: '', middle_name: '', last_name: '', phone_number: '', date_of_birth: '', role: ''
  });
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) return navigate('/login');

    // Fetch current profile data
    fetch('http://localhost:8000/api/profile/', {
      headers: { 'Authorization': `Token ${token}` }
    })
      .then(res => res.json())
      .then(data => {
        // Handle null date_of_birth from database
        if (data.date_of_birth === null) data.date_of_birth = '';
        setFormData(data);
      })
      .catch(err => setError('Failed to load profile data.'));
  }, [navigate]);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleUpdate = async (e) => {
    e.preventDefault();
    setMessage('');
    setError('');
    setIsSaving(true);
    const token = localStorage.getItem('token');

    try {
      const response = await fetch('http://localhost:8000/api/profile/update/', {
        method: 'PUT',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Token ${token}` 
        },
        body: JSON.stringify(formData),
      });

      const data = await response.json();
      
      if (response.ok) {
        setMessage('✅ Profile updated successfully!');
        // If the username changed, update local storage so the app knows
        if (formData.username !== localStorage.getItem('username')) {
            localStorage.setItem('username', formData.username);
        }
      } else {
        setError(data.error || 'Failed to update profile.');
      }
    } catch (err) {
      setError('Server error. Is Django running?');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="auth-container" style={{maxWidth: '600px', marginTop: '30px'}}>
      <Link to="/dashboard" style={{color: '#aaa', textDecoration: 'none', marginBottom: '20px', display: 'block'}}>
        ← Back to Dashboard
      </Link>
      
      <h2>Account Settings</h2>
      <p style={{textAlign: 'center', color: '#4CAF50', fontWeight: 'bold'}}>Role: {formData.role}</p>
      
      {message && <p style={{color: '#4CAF50', textAlign: 'center', fontWeight: 'bold'}}>{message}</p>}
      {error && <p className="error-msg">{error}</p>}

      <form onSubmit={handleUpdate}>
        <div style={{display: 'flex', gap: '10px'}}>
          <div className="form-group" style={{flex: 1}}>
            <label>First Name</label>
            <input type="text" name="first_name" value={formData.first_name || ''} onChange={handleChange} required />
          </div>
          <div className="form-group" style={{flex: 1}}>
            <label>Middle Name</label>
            <input type="text" name="middle_name" value={formData.middle_name || ''} onChange={handleChange} />
          </div>
        </div>

        <div className="form-group">
          <label>Last Name</label>
          <input type="text" name="last_name" value={formData.last_name || ''} onChange={handleChange} required />
        </div>

        <div className="form-group">
          <label>Username</label>
          <input type="text" name="username" value={formData.username || ''} onChange={handleChange} required />
        </div>

        <div className="form-group">
          <label>Email</label>
          <input type="email" name="email" value={formData.email || ''} onChange={handleChange} required />
        </div>

        <div style={{display: 'flex', gap: '10px'}}>
          <div className="form-group" style={{flex: 1}}>
            <label>Date of Birth</label>
            <input type="date" name="date_of_birth" value={formData.date_of_birth || ''} onChange={handleChange} />
          </div>
          <div className="form-group" style={{flex: 1}}>
            <label>Phone Number</label>
            <input type="text" name="phone_number" value={formData.phone_number || ''} onChange={handleChange} />
          </div>
        </div>

        <button type="submit" className="btn-submit" disabled={isSaving}>
          {isSaving ? 'Saving Changes...' : 'Save Changes'}
        </button>
      </form>
    </div>
  );
}