import { Link } from 'react-router-dom';
import './Welcome.css';

function Welcome() {
  return (
    <div className="welcome-container">
      <header className="welcome-nav">
        <Link to="/" className="brand">
          My<span>Jobs</span>
        </Link>
        <nav>
          <Link to="/login" className="nav-link">
            Sign In
          </Link>
          <Link to="/signup" className="nav-cta">
            Get Started
          </Link>
        </nav>
      </header>

      <main className="welcome-hero">
        <div className="hero-text">
          <span className="badge"> Get Your First Job </span>
          <h1>
            Find the job that <br />
            <span className="gradient-text">fits your life</span>
          </h1>
          <p className="hero-subtitle">
            Discover thousands of opportunities, connect with top companies,
            and take the next step in your career — all in one place. CLICK BELOW TO START
          </p>

          <div className="hero-actions">
            <Link to="/signup" className="btn btn-primary">
              Create Free Account
            </Link>
            <Link to="/login" className="btn btn-secondary">
              I already have an account
            </Link>
          </div>

          <div className="hero-stats">
            <div>
              <strong>comming soon</strong>
              <span>Jobs listed</span>
            </div>
            <div>
              <strong>comming soon</strong>
              <span>Companies</span>
            </div>
            <div>
              <strong>coming soon</strong>
              <span>Job seekers</span>
            </div>
          </div>
        </div>

        <div className="hero-art" aria-hidden="true">
          <div className="card-float card-1">
            <span className="dot" />
            <div>
              <strong>Online Jobs</strong>
              <small>Remote · Full-time</small>
            </div>
          </div>
          <div className="card-float card-2">
            <span className="dot dot-green" />
            <div>
              <strong>MW2026</strong>
              <small>Vision · 2026</small>
            </div>
          </div>
          <div className="card-float card-3">
            <span className="dot dot-orange" />
            <div>
              <strong>NGO's</strong>
              <small>On-site · Full-time</small>
            </div>
          </div>
        </div>
      </main>

      <footer className="welcome-footer">
        <p>© {new Date().getFullYear()} My Jobs. All rights reserved.</p>
      </footer>
    </div>
  );
}

export default Welcome;