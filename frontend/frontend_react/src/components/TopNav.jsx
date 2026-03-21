import { Link, NavLink } from "react-router-dom";

export default function TopNav({ brand = "QuizMaster", homeTo = "/", links = [], actions, profile, compact = false }) {
  return (
    <header className={compact ? "top-nav compact" : "top-nav"}>
      <Link className="brand-lockup" to={homeTo}>
        <div className="brand-mark">{brand.slice(0, 1)}</div>
        <span>{brand}</span>
      </Link>
      <nav className="nav-links">
        {links.map((link) => {
          const item = typeof link === "string" ? { label: link, to: "#" } : link;
          return item.to === "#" ? (
            <span key={item.label} className="nav-text-link">
              {item.label}
            </span>
          ) : (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) => (isActive ? "nav-router-link active" : "nav-router-link")}
            >
              {item.label}
            </NavLink>
          );
        })}
      </nav>
      <div className="nav-actions">
        {actions}
        {profile ? (
          <div className="profile-chip">
            <div className="profile-avatar">{profile.initials}</div>
            <div>
              <strong>{profile.name}</strong>
              <span>{profile.subtitle}</span>
            </div>
          </div>
        ) : null}
      </div>
    </header>
  );
}
