import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import './Auth.css';

export default function Signup() {
  const [formData, setFormData] = useState({
    username: '', first_name: '', middle_name: '', last_name: '',
    date_of_birth: '', email: '', phone_number: '', role: 'APPLICANT',
    password: '', confirm_password: ''
  });
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSignup = async (e) => {
    e.preventDefault();
    setError('');

    if (formData.password !== formData.confirm_password) {
      return setError('Passwords do not match!');
    }

    // Remove confirm_password before sending to backend
    const { confirm_password, ...dataToSend } = formData;

    try {
      const response = await fetch('http://localhost:8000/api/register/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(dataToSend),
      });

      const data = await response.json();

      if (response.ok) {
        // As per your document: Don't go to dashboard, go to sign in page
        alert('Account created successfully! Please sign in.');
        navigate('/login');
      } else {
        // Django will send back errors (e.g., "username already exists")
        setError(JSON.stringify(data));
      }
    } catch (err) {
      setError('Server error. Is Django running?');
    }
  };

  return (
    <div className="auth-container" style={{maxWidth: '500px'}}>
      <h2>Create an Account</h2>
      {error && <p className="error-msg">{error}</p>}
      
      <form onSubmit={handleSignup}>
        <div style={{display: 'flex', gap: '10px'}}>
          <div className="form-group" style={{flex: 1}}>
            <label>First Name</label>
            <input type="text" name="first_name" onChange={handleChange} required />
          </div>
          <div className="form-group" style={{flex: 1}}>
            <label>Middle Name</label>
            <input type="text" name="middle_name" onChange={handleChange} />
          </div>
        </div>

        <div className="form-group">
          <label>Last Name</label>
          <input type="text" name="last_name" onChange={handleChange} required />
        </div>

        <div className="form-group">
          <label>Username</label>
          <input type="text" name="username" onChange={handleChange} required />
        </div>

        <div className="form-group">
          <label>Email</label>
          <input type="email" name="email" onChange={handleChange} required />
        </div>

        <div style={{display: 'flex', gap: '10px'}}>
          <div className="form-group" style={{flex: 1}}>
            <label>Date of Birth</label>
            <input type="date" name="date_of_birth" onChange={handleChange} required />
          </div>
          <div className="form-group" style={{flex: 1}}>
            <label>Phone Number</label>
            <input type="text" name="phone_number" onChange={handleChange} required />
          </div>
        </div>

        <div className="form-group">
          <label>I am a...</label>
          <select name="role" onChange={handleChange} value={formData.role}>
            <option value="APPLICANT">Applicant (Looking for a job)</option>
            <option value="RECRUITER">Recruiter (Posting jobs)</option>
          </select>
        </div>

        <div className="form-group">
          <label>Password</label>
          <input type="password" name="password" onChange={handleChange} required />
        </div>

        <div className="form-group">
          <label>Confirm Password</label>
          <input type="password" name="confirm_password" onChange={handleChange} required />
        </div>

        <button type="submit" className="btn-submit">Sign Up</button>
      </form>
      
      <p style={{textAlign: 'center', marginTop: '15px', fontSize: '14px'}}>
        Already have an account? <Link to="/login" style={{color: '#4CAF50'}}>Sign in</Link>
      </p>
    </div>
  );
}