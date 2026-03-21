import { useEffect, useMemo, useState } from "react";
import { Link, useLocation, useNavigate, useSearchParams } from "react-router-dom";
import { useAuth } from "../auth/AuthProvider";
import TopNav from "../components/TopNav";

function PortalForm({
  title,
  subtitle,
  fields,
  primary,
  secondary,
  note,
  values,
  error,
  success,
  loading,
  onChange,
  onPrimary,
  onSecondary
}) {
  return (
    <section className="portal-form active single-portal-form">
      <h3>{title}</h3>
      <p>{subtitle}</p>
      <div className="field-stack">
        {fields.map((field) => (
          <label key={field.name} className="field">
            <span>{field.label}</span>
            <input
              name={field.name}
              onChange={onChange}
              placeholder={field.placeholder}
              type={field.type || "text"}
              value={values[field.name] || ""}
            />
          </label>
        ))}
      </div>
      {error ? <div className="form-alert error">{error}</div> : null}
      {success ? <div className="form-alert success">{success}</div> : null}
      <div className="dual-actions">
        <button className="primary-btn" disabled={loading} onClick={onPrimary} type="button">
          {loading ? "Please wait..." : primary}
        </button>
        {secondary ? (
          <button className="secondary-btn" onClick={onSecondary} type="button">
            {secondary}
          </button>
        ) : null}
      </div>
      {note ? <small>{note}</small> : null}
    </section>
  );
}

function getDashboardRoute(role) {
  return role === "admin" ? "/admin/dashboard" : "/student/dashboard";
}

export default function AuthPortalPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const [searchParams, setSearchParams] = useSearchParams();
  const { isAuthenticated, user, login, register } = useAuth();
  const selectedRole = searchParams.get("role") === "admin" ? "admin" : "student";
  const selectedMode = searchParams.get("mode") === "login" ? "login" : "register";
  const isLogin = selectedMode === "login";
  const [formValues, setFormValues] = useState({
    name: "",
    email: "",
    password: "",
    confirmPassword: ""
  });
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isAuthenticated && user?.role) {
      navigate(getDashboardRoute(user.role), { replace: true });
    }
  }, [isAuthenticated, navigate, user]);

  useEffect(() => {
    setFormValues({ name: "", email: "", password: "", confirmPassword: "" });
    setError("");
    setSuccess("");
  }, [selectedMode, selectedRole]);

  const content = useMemo(() => {
    if (selectedRole === "admin") {
      if (isLogin) {
        return {
          title: "Admin Login",
          subtitle: "Enter your email and password to continue.",
          fields: [
            { name: "email", label: "Email", placeholder: "admin@eduportal.com", type: "email" },
            { name: "password", label: "Password", placeholder: "Enter password", type: "password" }
          ],
          primary: "Login",
          secondary: null,
          note: "Admin accounts use the backend authentication service.",
          destination: "/admin/dashboard"
        };
      }

      return {
        title: "Admin Registration",
        subtitle: "Create your admin account and continue to the dashboard.",
        fields: [
          { name: "name", label: "Admin Name", placeholder: "Admin Identification" },
          { name: "email", label: "Email", placeholder: "admin@eduportal.com", type: "email" },
          { name: "password", label: "Password", placeholder: "Enter password", type: "password" },
          { name: "confirmPassword", label: "Confirm Password", placeholder: "Confirm password", type: "password" }
        ],
        primary: "Create Admin Account",
        secondary: "Already have login?",
        note: "New admins must register before they can use the platform.",
        destination: "/admin/dashboard"
      };
    }

    if (isLogin) {
      return {
        title: "Student Login",
        subtitle: "Enter your email and password to continue.",
        fields: [
          { name: "email", label: "Email", placeholder: "student@example.com", type: "email" },
          { name: "password", label: "Password", placeholder: "Enter password", type: "password" }
        ],
        primary: "Login",
        secondary: null,
        note: "Students must log in before they can join quizzes or view results.",
        destination: "/student/dashboard"
      };
    }

    return {
      title: "Student Registration",
      subtitle: "Create your student account to join private and public quizzes.",
      fields: [
        { name: "name", label: "Name", placeholder: "John Doe" },
        { name: "email", label: "Email", placeholder: "student@example.com", type: "email" },
        { name: "password", label: "Password", placeholder: "Enter password", type: "password" },
        { name: "confirmPassword", label: "Confirm Password", placeholder: "Confirm password", type: "password" }
      ],
      primary: "Create Student Account",
      secondary: "Already have login?",
      note: "New students must create an account before using platform features.",
      destination: "/student/dashboard"
    };
  }, [isLogin, selectedRole]);

  function goToOppositeMode() {
    setSearchParams({ role: selectedRole, mode: isLogin ? "register" : "login" });
  }

  function switchRole() {
    const nextRole = selectedRole === "student" ? "admin" : "student";
    setSearchParams({ role: nextRole, mode: selectedMode });
  }

  function handleChange(event) {
    const { name, value } = event.target;
    setFormValues((current) => ({ ...current, [name]: value }));
  }

  async function handleSubmit() {
    setError("");
    setSuccess("");

    if (!formValues.email.trim() || !formValues.password.trim()) {
      setError("Email and password are required.");
      return;
    }

    if (!isLogin) {
      if (!formValues.name.trim()) {
        setError("Name is required.");
        return;
      }
      if (formValues.password !== formValues.confirmPassword) {
        setError("Passwords do not match.");
        return;
      }
    }

    setLoading(true);

    try {
      if (isLogin) {
        await login({ role: selectedRole, email: formValues.email, password: formValues.password });
        setSuccess("Login successful.");
      } else {
        await register({
          role: selectedRole,
          name: formValues.name,
          email: formValues.email,
          password: formValues.password
        });
        setSuccess("Account created successfully.");
      }

      const redirectTo = location.state?.from?.pathname || content.destination;
      navigate(redirectTo, { replace: true });
    } catch (requestError) {
      setError(requestError.message || "Unable to complete the request.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="canvas">
      <TopNav
        brand="EduPortal"
        homeTo="/"
        links={[
          { label: "Home", to: "/" },
          { label: "Choose Account", to: "/account-type" }
        ]}
        actions={<Link className="nav-router-link" to={isLogin ? "/" : "/account-type"}>{isLogin ? "Back Home" : "Back"}</Link>}
      />

      <section className="center-intro compact-intro">
        <h1>{isLogin ? "Welcome Back" : "Create Your Account"}</h1>
        <p>
          {isLogin
            ? `You selected ${selectedRole}. Log in before using platform features.`
            : `${selectedRole === "student" ? "Student" : "Admin"} account selected. Registration is required for new users.`}
        </p>
      </section>

      <section className="single-portal-layout">
        <PortalForm
          title={content.title}
          subtitle={content.subtitle}
          fields={content.fields}
          primary={content.primary}
          secondary={content.secondary}
          note={content.note}
          values={formValues}
          error={error}
          success={success}
          loading={loading}
          onChange={handleChange}
          onPrimary={handleSubmit}
          onSecondary={content.secondary ? goToOppositeMode : undefined}
        />
      </section>

      <div className="oauth-row auth-footer-links account-switch-row">
        {!isLogin ? (
          <Link className="secondary-btn button-link" to="/account-type">
            Choose Account Type Again
          </Link>
        ) : null}
        <button className="secondary-btn" onClick={switchRole} type="button">
          Switch to {selectedRole === "student" ? "Admin" : "Student"}
        </button>
      </div>
    </div>
  );
}
