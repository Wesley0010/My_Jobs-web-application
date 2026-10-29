import { Link } from 'react-router-dom';
import './Welcome.css';

export default function Welcome() {
  return (
    <div className="welcome-page">
      {/* 1. HERO SECTION */}
      <header className="hero">
        <div className="hero-content">
          <h1 className="logo-text">My_Jobs</h1>
          <h2>Bridging the Gap in Malawi's Labour Market</h2>
          <p>
            Our vision is to eliminate bias, reduce hiring time, and connect capable 
            Malawian professionals with the right opportunities using advanced AI 
            semantic matching and document processing.
          </p>
          <div className="hero-buttons">
            <Link to="/signup" className="btn-primary">Get Started</Link>
            <Link to="/login" className="btn-secondary">Sign In</Link>
          </div>
        </div>
      </header>

      {/* 2. JOB CATEGORIES */}
      <section className="features">
        <h2>Jobs You Can Access</h2>
        <p className="subtitle">Powered by our AI matching engine</p>
        <div className="feature-grid">
          <div className="feature-card">
            <h3>Technology & IT</h3>
            <p>Software Engineers, Data Analysts, Network Admins, and more.</p>
          </div>
          <div className="feature-card">
            <h3>Healthcare</h3>
            <p>Nurses, Doctors, Lab Technicians, and Hospital Administrators.</p>
          </div>
          <div className="feature-card">
            <h3>Business & Finance</h3>
            <p>Accountants, HR Managers, Sales Executives, and Marketers.</p>
          </div>
          <div className="feature-card">
            <h3>Engineering</h3>
            <p>Civil Engineers, Architects, and Project Managers.</p>
          </div>
        </div>
      </section>

      {/* 3. ABOUT THE CREATORS */}
      <section className="about">
        <h2>About the Project</h2>
        <p>
          This system was developed to address the challenges of manual resume screening and 
          candidate shortlisting. By utilizing React, Django, TF-IDF, and the Google Gemini API, 
          we provide a seamless, intelligent hiring experience.
        </p>
        <p style={{marginTop: '10px', fontWeight: 'bold', color: '#4CAF50'}}>
          Developed as a Mini Project.
        </p>
      </section>

      <footer>
        <p>&copy; 2026 My_Jobs.</p>
      </footer>
    </div>
  );
}