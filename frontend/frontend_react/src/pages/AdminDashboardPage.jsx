import { Link } from "react-router-dom";
import AdminSidebar from "../components/AdminSidebar";
import { useAuth } from "../auth/AuthProvider";
import { adminStats, recentQuizzes } from "../data/mockData";

export default function AdminDashboardPage() {
  const { user } = useAuth();

  return (
    <div className="canvas admin-canvas">
      <AdminSidebar />
      <section className="admin-content">
        <div className="admin-topbar">
          <div>
            <h1>Dashboard</h1>
            <p>{`Manage your quizzes and track performance, ${user?.name || "Admin"}.`}</p>
          </div>
          <Link className="primary-btn small button-link" to="/admin/create-quiz">
            Create Quiz
          </Link>
        </div>

        <div className="stats-grid">
          {adminStats.map((stat) => (
            <article key={stat.label} className="stat-card">
              <span>{stat.label}</span>
              <strong>{stat.value}</strong>
              <small>{stat.trend}</small>
            </article>
          ))}
        </div>

        <section className="table-card">
          <div className="section-heading inline">
            <h2>Recent Quizzes</h2>
            <Link to="/student/leaderboard">Open live leaderboard</Link>
          </div>
          <table className="data-table">
            <thead>
              <tr>
                <th>Quiz Name</th>
                <th>Type</th>
                <th>Participants</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {recentQuizzes.map((quiz) => (
                <tr key={quiz.name}>
                  <td>{quiz.name}</td>
                  <td>{quiz.type}</td>
                  <td>{quiz.participants}</td>
                  <td>{quiz.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      </section>
    </div>
  );
}
