import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import './Auth.css'; 

export default function Settings() {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('profile');
  const [role, setRole] = useState('');
  
  // Profile State
  const [formData, setFormData] = useState({});
  const [profileMsg, setProfileMsg] = useState('');
  
  // Browse Jobs / Logs State
  const [allJobs, setAllJobs] = useState([]);
  const [myApps, setMyApps] = useState([]);
  const [appliedJobs, setAppliedJobs] = useState([]);
  
  // Complaints State
  const [myComplaints, setMyComplaints] = useState([]);
  const [allComplaints, setAllComplaints] = useState([]);
  const [newComplaint, setNewComplaint] = useState('');

  const [recruiterLogs, setRecruiterLogs] = useState([]);

  const token = localStorage.getItem('token');

  useEffect(() => {
    if (!token) return navigate('/login');
    const userRole = localStorage.getItem('role');
    setRole(userRole);

    // Load initial profile
    fetch('http://localhost:8000/api/profile/', { headers: { 'Authorization': `Token ${token}` } })
      .then(res => res.json()).then(data => {
        if (data.date_of_birth === null) data.date_of_birth = '';
        setFormData(data);
      });

    // Load Complaints based on role
    if (userRole === 'ADMIN') {
      fetch('http://localhost:8000/api/complaints/all/', { headers: { 'Authorization': `Token ${token}` } })
        .then(res => res.json()).then(data => { if(Array.isArray(data)) setAllComplaints(data); });
    } else {
      fetch('http://localhost:8000/api/complaints/my/', { headers: { 'Authorization': `Token ${token}` } })
        .then(res => res.json()).then(data => { if(Array.isArray(data)) setMyComplaints(data); });
    }
  }, [token, navigate]);

  // Fetch Tab-Specific Data
  useEffect(() => {
    if (activeTab === 'browse' && role === 'APPLICANT') {
      fetch('http://localhost:8000/api/browse-jobs/', { headers: { 'Authorization': `Token ${token}` } })
        .then(res => res.json()).then(data => { if(Array.isArray(data)) setAllJobs(data); });
      fetch('http://localhost:8000/api/my-applications/', { headers: { 'Authorization': `Token ${token}` } })
        .then(res => res.json()).then(data => { 
          if(Array.isArray(data)) {
            setAppliedJobs(data.map(a => a.job_title)); // Track applied job titles
            setMyApps(data);
          } 
        });
    }
    if (activeTab === 'logs' && role === 'RECRUITER') {
      fetch('http://localhost:8000/api/recruiter-logs/', { headers: { 'Authorization': `Token ${token}` } })
        .then(res => res.json())
        .then(data => { if(Array.isArray(data)) setRecruiterLogs(data); });
    }
  }, [activeTab, role, token]);

  // ================= LOGIC =================
  const handleUpdateProfile = async (e) => {
    e.preventDefault();
    setProfileMsg('Saving...');
    const response = await fetch('http://localhost:8000/api/profile/update/', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Token ${token}` },
      body: JSON.stringify(formData),
    });
    if (response.ok) setProfileMsg('✅ Profile updated successfully!');
    else setProfileMsg('Error updating profile.');
  };

  const handleApply = async (jobTitle, jobId) => {
    const response = await fetch(`http://localhost:8000/api/apply/${jobId}/`, {
      method: 'POST', headers: { 'Authorization': `Token ${token}` }
    });
    if (response.ok) {
      alert("Applied successfully!");
      setAppliedJobs([...appliedJobs, jobTitle]);
    } else {
      alert("Failed to apply or already applied.");
    }
  };

  const handleComplaintSubmit = async (e) => {
    e.preventDefault();
    const response = await fetch('http://localhost:8000/api/complaints/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Token ${token}` },
      body: JSON.stringify({ message: newComplaint })
    });
    if (response.ok) {
      alert("Complaint sent to Admin!");
      setNewComplaint('');
      window.location.reload();
    }
  };

  const handleAdminReply = async (id) => {
    const reply = prompt("Enter your reply to this user:");
    if (!reply) return;
    const response = await fetch(`http://localhost:8000/api/complaints/reply/${id}/`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Token ${token}` },
      body: JSON.stringify({ reply })
    });
    if (response.ok) {
      alert("Reply sent!");
      window.location.reload();
    }
  };

  const handleDownloadLetter = async (appId) => {
    const response = await fetch(`http://localhost:8000/api/interview-letter/${appId}/`, {
      headers: { 'Authorization': `Token ${token}` }
    });
    if (!response.ok) return alert("Letter not available yet.");
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `Interview_Letter.pdf`;
    a.click();
  };

  return (
    <div style={{maxWidth: '800px', margin: '30px auto', padding: '20px'}}>
      <Link to="/dashboard" style={{color: '#4CAF50', textDecoration: 'none', marginBottom: '20px', display: 'block'}}>
        ← Back to Dashboard
      </Link>
      
      <h2 style={{color: 'white', borderBottom: '1px solid #444', paddingBottom: '10px'}}>Account Settings</h2>
      
      {/* TABS */}
      <div style={{display: 'flex', gap: '10px', marginBottom: '20px', flexWrap: 'wrap'}}>
        <button onClick={() => setActiveTab('profile')} className="btn-action" style={{background: activeTab === 'profile' ? '#4CAF50' : '#333'}}>Edit Profile</button>
        <button onClick={() => setActiveTab('browse')} className="btn-action" style={{background: activeTab === 'browse' ? '#4CAF50' : '#333'}}>Browse Jobs</button>
        <button onClick={() => setActiveTab('reports')} className="btn-action" style={{background: activeTab === 'reports' ? '#4CAF50' : '#333'}}>Reports / Complaints</button>
        <button onClick={() => setActiveTab('logs')} className="btn-action" style={{background: activeTab === 'logs' ? '#4CAF50' : '#333'}}>My Logs</button>
      </div>

            {/* --- TAB: PROFILE --- */}
      {activeTab === 'profile' && (
        <div className="auth-container" style={{margin: 0, maxWidth: '100%', background: '#1e1e1e'}}>
          <h3>Edit Profile</h3>
          {profileMsg && <p style={{color: profileMsg.includes('❌') ? 'red' : '#4CAF50', fontWeight: 'bold'}}>{profileMsg}</p>}
          
          <form onSubmit={handleUpdateProfile}>
            <div style={{display: 'flex', gap: '10px'}}>
              <div className="form-group" style={{flex: 1}}>
                <label>First Name</label>
                <input type="text" name="first_name" value={formData.first_name || ''} onChange={(e) => setFormData({...formData, first_name: e.target.value})} required />
              </div>
              <div className="form-group" style={{flex: 1}}>
                <label>Middle Name</label>
                <input type="text" name="middle_name" value={formData.middle_name || ''} onChange={(e) => setFormData({...formData, middle_name: e.target.value})} />
              </div>
            </div>

            <div className="form-group">
              <label>Last Name</label>
              <input type="text" name="last_name" value={formData.last_name || ''} onChange={(e) => setFormData({...formData, last_name: e.target.value})} required />
            </div>

            <div className="form-group">
              <label>Username</label>
              <input type="text" name="username" value={formData.username || ''} onChange={(e) => setFormData({...formData, username: e.target.value})} required />
            </div>

            <div className="form-group">
              <label>Email</label>
              <input type="email" value={formData.email || ''} onChange={(e) => setFormData({...formData, email: e.target.value})} required />
            </div>

            <div style={{display: 'flex', gap: '10px'}}>
              <div className="form-group" style={{flex: 1}}>
                <label>Date of Birth</label>
                <input type="date" name="date_of_birth" value={formData.date_of_birth || ''} onChange={(e) => setFormData({...formData, date_of_birth: e.target.value})} />
              </div>
              <div className="form-group" style={{flex: 1}}>
                <label>Phone Number</label>
                <input type="text" name="phone_number" value={formData.phone_number || ''} onChange={(e) => setFormData({...formData, phone_number: e.target.value})} />
              </div>
            </div>
            
            <button type="submit" className="btn-submit">Save Changes</button>
          </form>
        </div>
      )}

      {/* --- TAB: BROWSE JOBS --- */}
      {activeTab === 'browse' && (
        <div className="card">
          <h3>Browse All Jobs (Not AI Recommended)</h3>
          {role !== 'APPLICANT' ? <p>Only applicants can browse jobs.</p> : (
            allJobs.map(job => (
              <div key={job.id} style={{background: '#2a2a2a', padding: '15px', marginBottom: '10px', borderRadius: '5px'}}>
                <h4>{job.title}</h4>
                <p style={{fontSize: '14px', color: '#ccc'}}>{job.description.substring(0, 100)}...</p>
                <button 
                  onClick={() => handleApply(job.title, job.id)} 
                  className="btn-action"
                  disabled={appliedJobs.includes(job.title)}
                  style={{background: appliedJobs.includes(job.title) ? '#555' : '#4CAF50'}}
                >
                  {appliedJobs.includes(job.title) ? 'Applied' : 'Apply Now'}
                </button>
              </div>
            ))
          )}
        </div>
      )}

      {/* --- TAB: REPORTS --- */}
      {activeTab === 'reports' && (
        <div className="card">
          <h3>Reports & Complaints</h3>
          {role !== 'ADMIN' ? (
            <div>
              <form onSubmit={handleComplaintSubmit} style={{marginBottom: '20px'}}>
                <textarea 
                  placeholder="Describe your issue to the Admin..." 
                  value={newComplaint} onChange={(e) => setNewComplaint(e.target.value)}
                  style={{width: '100%', padding: '10px', marginBottom: '10px', background: '#2a2a2a', color: 'white', border: '1px solid #444'}}
                  rows="3" required
                />
                <button type="submit" className="btn-action">Send to Admin</button>
              </form>
              <h4>My Complaints:</h4>
              {myComplaints.map(c => (
                <div key={c.id} style={{background: '#2a2a2a', padding: '10px', marginBottom: '10px', borderRadius: '5px'}}>
                  <p><strong>You:</strong> {c.message}</p>
                  <p><strong>Admin Reply:</strong> {c.reply || "Waiting for reply..."}</p>
                  <span style={{fontSize: '12px', color: c.status === 'RESOLVED' ? '#4CAF50' : '#ff9800'}}>{c.status}</span>
                </div>
              ))}
            </div>
          ) : (
            <div>
              <h4>Admin Inbox</h4>
              {allComplaints.map(c => (
                <div key={c.id} style={{background: '#2a2a2a', padding: '10px', marginBottom: '10px', borderRadius: '5px'}}>
                  <p><strong>{c.user} ({c.role}):</strong> {c.message}</p>
                  {c.reply && <p><strong>Your Reply:</strong> {c.reply}</p>}
                  {c.status === 'PENDING' && <button onClick={() => handleAdminReply(c.id)} className="btn-action" style={{padding: '5px 10px', fontSize: '12px'}}>Reply</button>}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

            {/* --- TAB: LOGS (Applications & Interviews) --- */}
      {activeTab === 'logs' && (
        <div className="card">
          <h3>Activity Logs</h3>
          
          {/* APPLICANT LOGS */}
          {role === 'APPLICANT' && (
            myApps.length === 0 ? <p>No activity yet.</p> : (
              myApps.map(app => (
                <div key={app.application_id} style={{background: '#2a2a2a', padding: '15px', marginBottom: '10px', borderRadius: '5px', borderLeft: app.status === 'INTERVIEW_SCHEDULED' ? '5px solid #4CAF50' : '5px solid #ff9800'}}>
                  <h4>{app.job_title}</h4>
                  <p>Status: <strong>{app.status}</strong></p>
                  {app.interview_date && <p>Interview Date: {app.interview_date}</p>}
                  <p style={{fontSize: '12px', color: '#aaa'}}>Applied on: {app.applied_at.substring(0, 10)}</p>
                  
                  {app.status === 'INTERVIEW_SCHEDULED' && (
                    <button onClick={() => handleDownloadLetter(app.application_id)} className="btn-action" style={{marginTop: '10px', background: '#4CAF50'}}>
                      Download Interview Letter
                    </button>
                  )}
                </div>
              ))
            )
          )}

          {/* RECRUITER LOGS */}
          {role === 'RECRUITER' && (
            recruiterLogs.length === 0 ? <p>No jobs posted yet.</p> : (
              recruiterLogs.map(log => (
                <div key={log.job_id} style={{background: '#2a2a2a', padding: '15px', marginBottom: '15px', borderRadius: '5px', borderLeft: '5px solid #2196f3'}}>
                  <h4 style={{margin: '0 0 10px 0', color: '#2196f3'}}>{log.title}</h4>
                  <p style={{margin: '0 0 10px 0', fontSize: '14px'}}>
                    <strong>Posted:</strong> {log.posted_at.substring(0, 10)} | 
                    <strong> Total Applicants:</strong> {log.total_applicants} | 
                    <strong> Interviews Scheduled:</strong> {log.interviews_scheduled}
                  </p>
                  
                  {log.applicants.length > 0 && (
                    <div style={{background: '#1e1e1e', padding: '10px', borderRadius: '5px'}}>
                      <h5 style={{margin: '0 0 5px 0', color: '#ccc'}}>Candidate Breakdown:</h5>
                      {log.applicants.map((app, i) => (
                        <div key={i} style={{fontSize: '13px', padding: '5px 0', borderBottom: '1px solid #333'}}>
                          <strong>{app.name}</strong> - Status: {app.status} {app.date && `(Scheduled: ${app.date.substring(0, 16).replace('T', ' ')})`}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))
            )
          )}
        </div>
      )}
    </div>
  );
}