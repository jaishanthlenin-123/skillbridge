import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AppLayout } from './components/Layout/AppLayout';
import { ErrorBoundary } from './components/ErrorBoundary';
import { LoginPage } from './features/auth/LoginPage';
import { RegisterPage } from './features/auth/RegisterPage';
import { DashboardPage } from './features/dashboard/DashboardPage';
import { ResumesPage } from './features/resumes/ResumesPage';
import { ResumeDetailPage } from './features/resumes/ResumeDetailPage';
import { JobsPage } from './features/jobs/JobsPage';
import { JobDetailPage } from './features/jobs/JobDetailPage';
import { MatchesPage } from './features/matching/MatchesPage';
import { MatchDetailPage } from './features/matching/MatchDetailPage';
import { RoadmapDetailPage } from './features/roadmap/RoadmapDetailPage';
import { HistoryPage } from './features/history/HistoryPage';
import { SettingsPage } from './features/settings/SettingsPage';

import { ProtectedRoute } from './components/Auth/ProtectedRoute';
import { FAQPage } from './features/faq/FAQPage';
import { SupportPage } from './features/support/SupportPage';
import { NotFoundPage } from './features/errors/NotFoundPage';
import { ServerErrorPage } from './features/errors/ServerErrorPage';

export function App() {
  return (
    <BrowserRouter>
      <ErrorBoundary>
        <Routes>
          {/* Public Authentication Routes */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />

          {/* Application Shell with Global AI Chat Widget on Every Route */}
          <Route element={<AppLayout />}>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/jobs" element={<JobsPage />} />
            <Route path="/jobs/:id" element={<JobDetailPage />} />
            <Route path="/faq" element={<FAQPage />} />
            <Route path="/support" element={<SupportPage />} />

            {/* Core Resume & Matching Routes - Seamless Guest Access Enabled */}
            <Route path="/resumes" element={<ResumesPage />} />
            <Route path="/resumes/:id" element={<ResumeDetailPage />} />
            <Route path="/matches" element={<MatchesPage />} />
            <Route path="/matches/:id" element={<MatchDetailPage />} />
            <Route path="/roadmap/:id" element={<RoadmapDetailPage />} />

            {/* Account-Specific Routes Requiring Permanent Login */}
            <Route
              path="/history"
              element={
                <ProtectedRoute>
                  <HistoryPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/settings"
              element={
                <ProtectedRoute>
                  <SettingsPage />
                </ProtectedRoute>
              }
            />

            {/* Dedicated Error Pages */}
            <Route path="/500" element={<ServerErrorPage />} />
            <Route path="/404" element={<NotFoundPage />} />

            {/* Catch-all Wildcard Route to Custom 404 Page */}
            <Route path="*" element={<NotFoundPage />} />
          </Route>
        </Routes>
      </ErrorBoundary>
    </BrowserRouter>
  );
}

export default App;
