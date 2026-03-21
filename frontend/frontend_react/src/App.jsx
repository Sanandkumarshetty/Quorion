import { Route, Routes } from "react-router-dom";
import LandingPage from "./pages/LandingPage";
import AccountTypePage from "./pages/AccountTypePage";
import AuthPortalPage from "./pages/AuthPortalPage";
import StudentDashboardPage from "./pages/StudentDashboardPage";
import WaitingRoomPage from "./pages/WaitingRoomPage";
import QuizSessionPage from "./pages/QuizSessionPage";
import LeaderboardPage from "./pages/LeaderboardPage";
import AdminDashboardPage from "./pages/AdminDashboardPage";
import CreateQuizPage from "./pages/CreateQuizPage";
import QuizResultPage from "./pages/QuizResultPage";
import ProtectedRoute from "./components/ProtectedRoute";

export default function App() {
  return (
    <div className="app-shell simple-shell">
      <header className="global-header">
        <span>Quorion</span>
      </header>

      <main className="page-stage full-stage">
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/account-type" element={<AccountTypePage />} />
          <Route path="/auth" element={<AuthPortalPage />} />
          <Route
            path="/student/dashboard"
            element={
              <ProtectedRoute allowedRoles={["student"]}>
                <StudentDashboardPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/student/waiting-room"
            element={
              <ProtectedRoute allowedRoles={["student"]}>
                <WaitingRoomPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/student/quiz-session"
            element={
              <ProtectedRoute allowedRoles={["student"]}>
                <QuizSessionPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/student/results"
            element={
              <ProtectedRoute allowedRoles={["student"]}>
                <QuizResultPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/student/leaderboard"
            element={
              <ProtectedRoute allowedRoles={["student", "admin"]}>
                <LeaderboardPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/dashboard"
            element={
              <ProtectedRoute allowedRoles={["admin"]}>
                <AdminDashboardPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/create-quiz"
            element={
              <ProtectedRoute allowedRoles={["admin"]}>
                <CreateQuizPage />
              </ProtectedRoute>
            }
          />
          <Route path="*" element={<LandingPage />} />
        </Routes>
      </main>
    </div>
  );
}
