import { Link } from "react-router-dom";
import { useAuth } from "../auth/AuthProvider";
import TopNav from "../components/TopNav";
import { landingFeatures } from "../data/mockData";

function FeatureCard({ title, description }) {
  return (
    <article className="feature-card">
      <div className="feature-icon">{title.slice(0, 1)}</div>
      <h3>{title}</h3>
      <p>{description}</p>
    </article>
  );
}

export default function LandingPage() {
  const { isAuthenticated, user, logout } = useAuth();
  const dashboardRoute = user?.role === "admin" ? "/admin/dashboard" : "/student/dashboard";

  return (
    <div className="canvas landing-canvas">
      <TopNav
        brand="QuizMaster"
        homeTo="/"
        links={[
          { label: "Features", to: "/" },
          { label: "Student", to: "/student/dashboard" },
          { label: "Leaderboard", to: "/student/leaderboard?type=private" },
          { label: "Admin", to: "/admin/dashboard" }
        ]}
        actions={
          isAuthenticated ? (
            <>
              <Link className="ghost-btn button-link" to={dashboardRoute}>
                Open Dashboard
              </Link>
              <button className="primary-btn small" onClick={logout} type="button">
                Logout
              </button>
            </>
          ) : (
            <>
              <Link className="ghost-btn button-link" to="/auth?mode=login&role=student">
                Login
              </Link>
              <Link className="primary-btn small button-link" to="/account-type">
                Create Account
              </Link>
            </>
          )
        }
      />

      <section className="hero-section">
        <div>
          <p className="section-tag">Real-time quiz platform</p>
          <h1>Elevate your quiz experience</h1>
          <p className="hero-copy">
            Run competitive quizzes with live rankings, timed sessions, private room access, and smooth multi-user
            participation flows.
          </p>
          <div className="hero-actions">
            <Link className="primary-btn button-link" to={isAuthenticated ? dashboardRoute : "/account-type"}>
              {isAuthenticated ? "Go to Dashboard" : "Get Started Free"}
            </Link>
            <Link className="secondary-btn button-link" to={isAuthenticated ? dashboardRoute : "/auth?mode=login&role=student"}>
              {isAuthenticated ? "Continue" : "Login to Continue"}
            </Link>
          </div>
          <div className="hero-metrics">
            <span>10k+ active users</span>
            <span>4.9/5 rating</span>
          </div>
        </div>
        <div className="illustration-card">
          <div>
            <div className="illustration-trophy">Trophy</div>
            <p>Real-time Quiz Platform Illustration</p>
          </div>
        </div>
      </section>

      <section className="section-block">
        <div className="section-heading">
          <h2>Platform Features</h2>
          <p>Everything you need to create engaging, competitive, and fair quiz experiences.</p>
        </div>
        <div className="feature-grid">
          {landingFeatures.map((feature) => (
            <FeatureCard key={feature.title} {...feature} />
          ))}
        </div>
      </section>

      <section className="section-block split-block">
        <div className="check-list">
          <h2>Why Choose QuizMaster?</h2>
          {[
            "Instant engagement with live rankings",
            "Easy quiz setup for admins and instructors",
            "Detailed analytics for every session",
            "Secure and reliable hosting for classroom use"
          ].map((item) => (
            <div key={item} className="check-row">
              <span className="check-box">+</span>
              <p>{item}</p>
            </div>
          ))}
        </div>
        <div className="illustration-card muted">
          <div>
            <div className="illustration-trophy">Chart</div>
            <p>Analytics Dashboard Preview</p>
          </div>
        </div>
      </section>

      <footer className="landing-footer">
        <div className="footer-grid">
          <div>
            <div className="brand-lockup footer-brand">
              <div className="brand-mark">Q</div>
              <span>QuizMaster</span>
            </div>
            <p>
              The ultimate online quiz platform for real-time competitions, classroom sessions, and leaderboard-driven
              learning.
            </p>
          </div>
          <div>
            <h3>About Us</h3>
            <p>We help educators, trainers, and organizations run better live quiz experiences.</p>
            <p>support@quizmaster.com</p>
          </div>
          <div>
            <h3>Help</h3>
            <div className="footer-links">
              <Link to="/auth?role=student&mode=login">Student Login</Link>
              <Link to="/auth?role=admin&mode=login">Admin Login</Link>
              <Link to="/student/leaderboard?type=private">Leaderboard</Link>
              <Link to="/admin/create-quiz">Create Quiz</Link>
            </div>
          </div>
        </div>
        <div className="footer-bottom">
          <span>Copyright 2026 QuizMaster. All rights reserved.</span>
        </div>
      </footer>
    </div>
  );
}
