import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../auth/AuthProvider";

export default function ProtectedRoute({ allowedRoles, children }) {
  const location = useLocation();
  const { isAuthenticated, isBootstrapping, user } = useAuth();

  if (isBootstrapping) {
    return (
      <div className="canvas auth-status-shell">
        <section className="auth-status-card">
          <h2>Checking your session</h2>
          <p>Please wait while we verify your login.</p>
        </section>
      </div>
    );
  }

  if (!isAuthenticated) {
    const fallbackRole = allowedRoles?.[0] === "admin" ? "admin" : "student";
    return <Navigate to={`/auth?mode=login&role=${fallbackRole}`} replace state={{ from: location }} />;
  }

  if (allowedRoles?.length && !allowedRoles.includes(user?.role)) {
    const nextRoute = user?.role === "admin" ? "/admin/dashboard" : "/student/dashboard";
    return <Navigate to={nextRoute} replace />;
  }

  return children;
}
