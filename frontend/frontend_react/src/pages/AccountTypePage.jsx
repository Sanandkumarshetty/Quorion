import { Link } from "react-router-dom";

export default function AccountTypePage() {
  return (
    <div className="canvas split-auth-canvas">
      <div className="split-panel admin">
        <div className="floating-badge">Choose your role</div>
        <div className="split-copy">
          <div className="panel-icon">A</div>
          <h1>Admin Account</h1>
          <h2>Manage your institution</h2>
          <p>
            Oversee quizzes, monitor users, manage performance, and configure institutional settings.
          </p>
          <Link className="light-btn wide button-link" to="/auth?role=admin&mode=register">
            Continue as Admin
          </Link>
          <ul className="panel-list">
            <li>Full platform management</li>
            <li>User and quiz oversight</li>
            <li>Analytics and reporting</li>
          </ul>
        </div>
      </div>
      <div className="split-panel student">
        <div className="split-copy">
          <div className="panel-icon">S</div>
          <h1>Student Account</h1>
          <h2>Learn and grow</h2>
          <p>Join quiz sessions, track performance, access public quizzes, and view your results.</p>
          <Link className="light-btn wide button-link" to="/auth?role=student&mode=register">
            Continue as Student
          </Link>
          <ul className="panel-list">
            <li>Access to all course quizzes</li>
            <li>Progress tracking</li>
            <li>Leaderboard participation</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
