import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthProvider";

const items = [
  { label: "Dashboard", to: "/admin/dashboard" },
  { label: "Create Quiz", to: "/admin/create-quiz" },
  { label: "Leaderboard", to: "/student/leaderboard" }
];

function getInitials(name) {
  return (name || "Admin User")
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() || "")
    .join("") || "AD";
}

export default function AdminSidebar() {
  const navigate = useNavigate();
  const { user, logout } = useAuth();

  function handleLogout() {
    logout();
    navigate("/");
  }

  return (
    <aside className="admin-sidebar">
      <NavLink className="brand-lockup inverse" to="/admin/dashboard">
        <div className="brand-mark">Q</div>
        <span>Quorion</span>
      </NavLink>
      <nav className="sidebar-menu">
        {items.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) => (isActive ? "sidebar-link active" : "sidebar-link")}
          >
            {item.label}
          </NavLink>
        ))}
        <button className="sidebar-link" onClick={handleLogout} type="button">
          Logout
        </button>
      </nav>
      <div className="sidebar-user">
        <div className="profile-avatar">{getInitials(user?.name)}</div>
        <div>
          <strong>{user?.name || "Admin User"}</strong>
          <span>{user?.email || "Administrator"}</span>
        </div>
      </div>
    </aside>
  );
}

