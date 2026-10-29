import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import Chatbot from './Chatbot';
import './Dashboard.css';

export default function Dashboard() {
  const [role, setRole] = useState('');
  const navigate = useNavigate();

  // --- APPLICANT STATE ---
  const [file, setFile] = useState(null);
  const [uploadStatus, setUploadStatus] = useState('');
  const [recommendedJobs, setRecommendedJobs] = useState([]);
  const [appliedJobs, setAppliedJobs] = useState([]);

  // --- RECRUITER STATE ---
  const [jobData, setJobData] = useState({ title: '', description: '' });
  const [jobFile, setJobFile] = useState(null);
  const [recruiterJobs, setRecruiterJobs] = useState([]);
  
  // --- AI MATCHING & APPLICATIONS STATE ---
  const [selectedJobId, setSelectedJobId] = useState(null);
  const [matchedApplicants, setMatchedApplicants] = useState([]);
  const [jobApplications, setJobApplications] = useState([]);

  // --- ADMIN STATE ---
  const [allUsers, setAllUsers] = useState([]);
  const [allJobs, setAllJobs] = useState([]);

  useEffect(() => {
    const token = localStorage.getItem('token');
    const userRole = localStorage.getItem('role');

    if (!token) {
      navigate('/login');
    } else {
      setRole(userRole);
      
      if (userRole === 'APPLICANT') {
        fetch('http://localhost:8000/api/matched-jobs/', {
          headers: { 'Authorization': `Token ${token}` }
        }).then(res => res.json()).then(data => {
            if (Array.isArray(data)) setRecommendedJobs(data);
        });
      }

      if (userRole === 'RECRUITER') {
        fetch('http://localhost:8000/api/recruiter-jobs/', {
          headers: { 'Authorization': `Token ${token}` }
        }).then(res => res.json()).then(data => {
            if (Array.isArray(data)) setRecruiterJobs(data);
        });
      }

      if (userRole === 'ADMIN') {
        fetch('http://localhost:8000/api/admin-data/', {
          headers: { 'Authorization': `Token ${token}` }
        }).then(res => res.json()).then(data => {
            if (data.users && data.jobs) {
              setAllUsers(data.users);
              setAllJobs(data.jobs);
            }
        });
      }
    }
  }, [navigate]);

  const handleLogout = () => {
    localStorage.clear();
    navigate('/login');
  };

  // ==========================================
  // APPLICANT LOGIC
  // ==========================================
  const handleResumeUpload = async (e) => {
    e.preventDefault();
    if (!file) return setUploadStatus('Please select a file first.');

    const token = localStorage.getItem('token');
    const formData = new FormData();
    formData.append('file', file);

    try {
      setUploadStatus('Uploading and parsing...');
      const response = await fetch('http://localhost:8000/api/upload-resume/', {
        method: 'POST',
        headers: { 'Authorization': `Token ${token}` },
        body: formData,
      });

      const data = await response.json();
      if (response.ok) {
        setUploadStatus('Success! Resume parsed.');
        window.location.reload(); 
      } else {
        setUploadStatus(data.error || 'Upload failed.');
      }
    } catch (err) {
      setUploadStatus('Server error.');
    }
  };

  const handleApply = async (jobId) => {
    const token = localStorage.getItem('token');
    try {
      const response = await fetch(`http://localhost:8000/api/apply/${jobId}/`, {
        method: 'POST',
        headers: { 'Authorization': `Token ${token}` }
      });
      const data = await response.json();
      if (response.ok) {
        alert("Application submitted successfully!");
        setAppliedJobs([...appliedJobs, jobId]);
      } else {
        alert(data.error);
      }
    } catch (err) {
      alert("Server error");
    }
  };

  // ==========================================
  // RECRUITER LOGIC
  // ==========================================
  const handleCreateJob = async (e) => {
    e.preventDefault();
    const token = localStorage.getItem('token');
    const formData = new FormData();
    formData.append('title', jobData.title);
    formData.append('description', jobData.description);
    if (jobFile) formData.append('file', jobFile);

    try {
      const response = await fetch('http://localhost:8000/api/create-job/', {
        method: 'POST',
        headers: { 'Authorization': `Token ${token}` },
        body: formData,
      });
      if (response.ok) {
        alert('Job posted successfully!');
        window.location.reload();
      }
    } catch (err) {
      alert('Server error posting job.');
    }
  };

  const handleViewJobDetails = async (jobId) => {
    const token = localStorage.getItem('token');
    
    fetch(`http://localhost:8000/api/job/${jobId}/applicants/`, {
      headers: { 'Authorization': `Token ${token}` }
    }).then(res => res.json()).then(data => {
        if (Array.isArray(data)) setMatchedApplicants(data);
    });

    fetch(`http://localhost:8000/api/job/${jobId}/applications/`, {
      headers: { 'Authorization': `Token ${token}` }
    }).then(res => res.json()).then(data => {
        if (Array.isArray(data)) setJobApplications(data);
    });

    setSelectedJobId(jobId);
  };

  const handleScheduleInterview = async (applicationId) => {
    const dateInput = prompt("Enter interview date and time (Format: YYYY-MM-DD HH:MM):");
    if (!dateInput) return;

    const formattedDate = dateInput.replace(" ", "T") + ":00";
    const token = localStorage.getItem('token');

    try {
      const response = await fetch(`http://localhost:8000/api/schedule-interview/${applicationId}/`, {
        method: 'PUT',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Token ${token}` 
        },
        body: JSON.stringify({ interview_date: formattedDate })
      });
      
      if (response.ok) {
        alert("Interview Scheduled! (Check Django terminal for email)");
        handleViewJobDetails(selectedJobId);
      } else {
        const data = await response.json();
        alert(data.error || "Failed to schedule");
      }
    } catch (err) {
      alert("Server error");
    }
  };

  const handleDownloadReport = async (jobId) => {
    const token = localStorage.getItem('token');
    try {
      const response = await fetch(`http://localhost:8000/api/report/${jobId}/`, {
        headers: { 'Authorization': `Token ${token}` }
      });
      
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `Report_Job_${jobId}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      alert("Error downloading report");
    }
  };

  // ==========================================
  // ADMIN LOGIC
  // ==========================================
  const handleUpdateRole = async (userId, newRole) => {
    const token = localStorage.getItem('token');
    try {
      const response = await fetch(`http://localhost:8000/api/admin-update-role/${userId}/`, {
        method: 'PUT',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Token ${token}` 
        },
        body: JSON.stringify({ role: newRole })
      });
      
      if (response.ok) {
        alert("User role updated successfully!");
        setAllUsers(allUsers.map(user => 
          user.id === userId ? { ...user, role: newRole } : user
        ));
      } else {
        alert("Failed to update role.");
      }
    } catch (err) {
      alert("Server error");
    }
  };

  return (
    <div className="dashboard-container">
      <nav className="navbar">
        <Link to="/" style={{ textDecoration: 'none' }}>
          <h2 style={{ color: '#4CAF50', margin: 0, cursor: 'pointer' }}>My_Jobs</h2>
        </Link>
        
        <div className="nav-links" style={{display: 'flex', alignItems: 'center', gap: '15px'}}>
          {/* Gender-Neutral User Icon & Name */}
          <div style={{display: 'flex', alignItems: 'center', gap: '8px', color: 'white'}}>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#4CAF50" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
              <circle cx="12" cy="7" r="4"></circle>
            </svg>
            <span>{localStorage.getItem('firstName')} {localStorage.getItem('lastName')}</span>
          </div>
          
          <button onClick={() => navigate('/settings')}>Settings</button>
          <button onClick={handleLogout}>Logout</button>
        </div>
      </nav>

      <div className="main-content">
        <h1>Welcome to your Dashboard</h1>
        <p>You are logged in as: <strong>{role}</strong></p>

        {/* --- APPLICANT VIEW --- */}
        {role === 'APPLICANT' && (
          <div>
            <div className="card" style={{ borderColor: '#ff9800' }}>
              <h3>📄 Upload Your Resume</h3>
              {uploadStatus && <p style={{color: 'yellow', fontWeight: 'bold'}}>{uploadStatus}</p>}
              <form onSubmit={handleResumeUpload} style={{display: 'flex', gap: '10px', marginTop: '15px'}}>
                <input type="file" accept=".pdf,.docx" onChange={(e) => setFile(e.target.files[0])} style={{color: 'white'}} required />
                <button type="submit" className="btn-action">Upload & Parse</button>
              </form>
            </div>

            <div className="card">
              <h3>💼 Recommended Jobs (AI Matched)</h3>
              {recommendedJobs.length === 0 ? (
                <p>No matches yet. Upload your resume or wait for recruiters to post jobs.</p>
              ) : (
                <div style={{display: 'flex', flexDirection: 'column', gap: '15px', marginTop: '15px'}}>
                  {recommendedJobs.map((job) => (
                    <div key={job.job_id} style={{background: '#2a2a2a', padding: '15px', borderRadius: '5px', borderLeft: '5px solid #4CAF50'}}>
                      <h4>{job.title} <span style={{color: '#4CAF50'}}>({job.score}% Match)</span></h4>
                      <p style={{fontSize: '14px', color: '#ccc'}}>{job.description.substring(0, 150)}...</p>
                      <button 
                        onClick={() => handleApply(job.job_id)} 
                        className="btn-action" 
                        style={{marginTop: '10px', background: appliedJobs.includes(job.job_id) ? '#555' : '#4CAF50'}}
                        disabled={appliedJobs.includes(job.job_id)}
                      >
                        {appliedJobs.includes(job.job_id) ? 'Already Applied' : 'Apply Now'}
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* --- RECRUITER VIEW --- */}
        {role === 'RECRUITER' && (
          <div>
            <div className="card" style={{ borderColor: '#2196f3' }}>
              <h3>➕ Post a New Job</h3>
              <form onSubmit={handleCreateJob}>
                <input type="text" placeholder="Job Title" value={jobData.title} onChange={(e) => setJobData({...jobData, title: e.target.value})} style={{width: '100%', padding: '10px', marginBottom: '10px', background: '#2a2a2a', color: 'white', border: '1px solid #444', borderRadius: '5px'}} required />
                <textarea placeholder="Job Description" value={jobData.description} onChange={(e) => setJobData({...jobData, description: e.target.value})} style={{width: '100%', padding: '10px', marginBottom: '10px', background: '#2a2a2a', color: 'white', border: '1px solid #444', borderRadius: '5px'}} rows="3" required />
                <input type="file" accept=".pdf,.docx" onChange={(e) => setJobFile(e.target.files[0])} style={{color: 'white', marginBottom: '10px'}} />
                <button type="submit" className="btn-action">Post Job</button>
              </form>
            </div>

            <div className="card">
              <h3>📋 Your Posted Jobs</h3>
              <div style={{display: 'flex', flexDirection: 'column', gap: '10px', marginTop: '15px'}}>
                {recruiterJobs.map((job) => (
                  <div key={job.id} style={{background: '#2a2a2a', padding: '15px', borderRadius: '5px', display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
                    <div>
                      <h4 style={{margin: '0 0 5px 0'}}>{job.title}</h4>
                      <p style={{fontSize: '12px', margin: 0, color: '#aaa'}}>{job.description.substring(0, 50)}...</p>
                    </div>
                    <button onClick={() => handleViewJobDetails(job.id)} className="btn-action" style={{background: '#2196f3'}}>Manage Job</button>
                  </div>
                ))}
              </div>

              {selectedJobId && (
                <div style={{marginTop: '30px', borderTop: '1px solid #444', paddingTop: '20px'}}>
                  <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
                    <h4>📩 Real Applications</h4>
                    <button onClick={() => handleDownloadReport(selectedJobId)} className="btn-action" style={{background: '#4CAF50', padding: '8px 15px'}}>
                      Download PDF Report
                    </button>
                  </div>
                  
                  {jobApplications.length === 0 ? <p>No applications yet.</p> : (
                    jobApplications.map(app => (
                      <div key={app.application_id} style={{background: '#2a2a2a', padding: '15px', marginBottom: '10px', borderRadius: '5px', borderLeft: app.status === 'INTERVIEW_SCHEDULED' ? '5px solid #4CAF50' : '5px solid #ff9800'}}>
                        <h5 style={{margin: '0 0 5px 0'}}>{app.applicant_name} <span style={{color: '#aaa', fontWeight: 'normal'}}>({app.email})</span></h5>
                        <p style={{margin: '0 0 10px 0', fontSize: '14px'}}>Status: <strong>{app.status}</strong> {app.interview_date && `| Date: ${app.interview_date}`}</p>
                        {app.status === 'APPLIED' && (
                          <button onClick={() => handleScheduleInterview(app.application_id)} className="btn-action" style={{padding: '5px 10px', fontSize: '12px'}}>
                            Schedule Interview
                          </button>
                        )}
                      </div>
                    ))
                  )}

                  <h4 style={{marginTop: '20px'}}>🤖 AI Suggested Candidates</h4>
                  {matchedApplicants.length === 0 ? <p>No AI matches found.</p> : (
                    matchedApplicants.map(applicant => (
                      <div key={applicant.applicant_id} style={{background: '#1e1e1e', padding: '15px', marginBottom: '10px', borderRadius: '5px', borderLeft: '5px solid #2196f3'}}>
                         <h5 style={{margin: '0 0 5px 0'}}>{applicant.name} <span style={{color: '#2196f3'}}>({applicant.score}% Match)</span></h5>
                         <p style={{margin: 0, fontSize: '13px', color: '#aaa'}}>{applicant.email}</p>
                      </div>
                    ))
                  )}
                </div>
              )}
            </div>
          </div>
        )}

        {/* --- ADMIN VIEW --- */}
        {role === 'ADMIN' && (
          <div>
            <div className="card" style={{ borderColor: '#9c27b0' }}>
              <h3>👥 Manage Users ({allUsers.length})</h3>
              <div style={{display: 'flex', flexDirection: 'column', gap: '10px', marginTop: '15px'}}>
                {allUsers.map((user) => (
                  <div key={user.id} style={{background: '#2a2a2a', padding: '15px', borderRadius: '5px', display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
                    <div>
                      <h4 style={{margin: '0 0 5px 0'}}>{user.first_name} {user.last_name} <span style={{color: '#aaa', fontSize: '14px'}}>(@{user.username})</span></h4>
                      <p style={{margin: 0, fontSize: '13px', color: '#aaa'}}>{user.email}</p>
                    </div>
                    <select value={user.role} onChange={(e) => handleUpdateRole(user.id, e.target.value)} style={{padding: '8px', background: '#1e1e1e', color: 'white', border: '1px solid #444', borderRadius: '5px'}}>
                      <option value="APPLICANT">Applicant</option>
                      <option value="RECRUITER">Recruiter</option>
                      <option value="ADMIN">Admin</option>
                    </select>
                  </div>
                ))}
              </div>
            </div>

            <div className="card" style={{ borderColor: '#9c27b0' }}>
              <h3>📋 All System Jobs ({allJobs.length})</h3>
              <div style={{display: 'flex', flexDirection: 'column', gap: '10px', marginTop: '15px'}}>
                {allJobs.map((job) => (
                  <div key={job.id} style={{background: '#2a2a2a', padding: '15px', borderRadius: '5px'}}>
                    <h4 style={{margin: '0 0 5px 0'}}>{job.title}</h4>
                    <p style={{margin: 0, fontSize: '13px', color: '#aaa'}}>Posted by: {job.recruiter__username}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
      
      <Chatbot />
    </div>
  );
}