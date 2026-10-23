import { Link } from 'react-router-dom';
import AppLayout from './AppLayout';
import './Dashboard.css';

const JOBS = [];
const STATS = [];
const ACTIVITY = [];

function Dashboard() {
  const today = new Date().toLocaleDateString(undefined, {
    weekday: 'long',
    month: 'long',
    day: 'numeric',
  });

  return (
    <AppLayout>
      <div className="dashboard">
        <div className="dashboard-header">
          <div>
            <h1>Dashboard</h1>
            <p className="dashboard-date">{today}</p>
          </div>
          <Link to="/jobs" className="btn-primary-sm">
            Browse Jobs
          </Link>
        </div>

        <section className="stat-grid">
          {STATS.map((s) => (
            <div key={s.label} className={`stat-card stat-${s.color}`}>
              <span className="stat-icon">{s.icon}</span>
              <div>
                <strong>{s.value}</strong>
                <span>{s.label}</span>
              </div>
            </div>
          ))}
        </section>

        <section className="dashboard-grid">
          <div className="dashboard-panel">
            <div className="panel-title">
              <h2>Recommended Jobs</h2>
              <Link to="/jobs" className="panel-link">
                View all →
              </Link>
            </div>

            <div className="job-list">
              {JOBS.map((job) => (
                <div key={job.id} className="job-row">
                  <div className="job-logo">{job.company.charAt(0)}</div>
                  <div className="job-info">
                    <strong>{job.title}</strong>
                    <span>
                      {job.company} · {job.location}
                    </span>
                  </div>
                  <div className="job-meta">
                    <span className="pill">{job.type}</span>
                    <span className="salary">{job.salary}</span>
                  </div>
                  <button className="btn-apply">Apply</button>
                </div>
              ))}
            </div>
          </div>

          <div className="dashboard-panel">
            <div className="panel-title">
              <h2>Recent Activity</h2>
            </div>
            <ul className="activity-list">
              {ACTIVITY.map((a) => (
                <li key={a.id}>
                  <span className="activity-dot" />
                  <div>
                    <p>{a.text}</p>
                    <small>{a.when}</small>
                  </div>
                </li>
              ))}
            </ul>
          </div>
        </section>

        <section className="quick-actions">
          <h2>Quick Actions</h2>
          <div className="quick-actions-grid">
            <Link to="/profile" className="quick-card">
              <strong>Edit Profile</strong>
              <small>Update your details</small>
            </Link>
            <Link to="/jobs" className="quick-card">
              <strong>Find Jobs</strong>
              <small>Browse new listings</small>
            </Link>
            <Link to="/saved" className="quick-card">
              <strong>Saved Jobs</strong>
              <small>Review your shortlist</small>
            </Link>
          </div>
        </section>
      </div>
    </AppLayout>
  );
}

export default Dashboard;