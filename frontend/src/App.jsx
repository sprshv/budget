import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import AuthGuard from './components/AuthGuard'
import OnboardingGuard from './components/OnboardingGuard'
import AppShell from './components/AppShell'
import LoginPage from './pages/LoginPage'
import SignupPage from './pages/SignupPage'
import OnboardingPage from './pages/OnboardingPage'
import ForgotPasswordPage from './pages/ForgotPasswordPage'
import ResetPasswordPage from './pages/ResetPasswordPage'
import VerifyEmailPage from './pages/VerifyEmailPage'
import MfaSetupPage from './pages/MfaSetupPage'
import MfaVerifyPage from './pages/MfaVerifyPage'
import SettingsPage from './pages/SettingsPage'
import AccountsPage from './pages/AccountsPage'
import TransactionsPage from './pages/TransactionsPage'
import BudgetsPage from './pages/BudgetsPage'
import BudgetHistoryPage from './pages/BudgetHistoryPage'
import DashboardPage from './pages/DashboardPage'
import GoalsPage from './pages/GoalsPage'
import BillsPage from './pages/BillsPage'
import SubscriptionsPage from './pages/SubscriptionsPage'
import AnalyticsPage from './pages/AnalyticsPage'
import NotificationPrefsPage from './pages/NotificationPrefsPage'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/signup" element={<SignupPage />} />
        <Route path="/forgot-password" element={<ForgotPasswordPage />} />
        <Route path="/reset-password" element={<ResetPasswordPage />} />
        <Route path="/verify-email" element={<VerifyEmailPage />} />
        {/* MFA routes — /mfa-setup requires an authenticated session (AAL1);
            /mfa-verify is public so the login flow can reach it before AAL2. */}
        <Route
          path="/mfa-setup"
          element={
            <AuthGuard>
              <MfaSetupPage />
            </AuthGuard>
          }
        />
        <Route path="/mfa-verify" element={<MfaVerifyPage />} />
        <Route
          path="/onboarding"
          element={
            <AuthGuard>
              <OnboardingPage />
            </AuthGuard>
          }
        />
        <Route
          path="/dashboard"
          element={
            <AuthGuard>
              <OnboardingGuard>
                <AppShell>
                  <DashboardPage />
                </AppShell>
              </OnboardingGuard>
            </AuthGuard>
          }
        />
        <Route
          path="/settings"
          element={
            <AuthGuard>
              <OnboardingGuard>
                <AppShell>
                  <SettingsPage />
                </AppShell>
              </OnboardingGuard>
            </AuthGuard>
          }
        />
        <Route
          path="/accounts"
          element={
            <AuthGuard>
              <OnboardingGuard>
                <AppShell>
                  <AccountsPage />
                </AppShell>
              </OnboardingGuard>
            </AuthGuard>
          }
        />
        <Route
          path="/transactions"
          element={
            <AuthGuard>
              <OnboardingGuard>
                <AppShell>
                  <TransactionsPage />
                </AppShell>
              </OnboardingGuard>
            </AuthGuard>
          }
        />
        <Route
          path="/budgets"
          element={
            <AuthGuard>
              <OnboardingGuard>
                <AppShell>
                  <BudgetsPage />
                </AppShell>
              </OnboardingGuard>
            </AuthGuard>
          }
        />
        <Route
          path="/budgets/history"
          element={
            <AuthGuard>
              <OnboardingGuard>
                <AppShell>
                  <BudgetHistoryPage />
                </AppShell>
              </OnboardingGuard>
            </AuthGuard>
          }
        />
        <Route
          path="/goals"
          element={
            <AuthGuard>
              <OnboardingGuard>
                <AppShell>
                  <GoalsPage />
                </AppShell>
              </OnboardingGuard>
            </AuthGuard>
          }
        />
        <Route
          path="/bills"
          element={
            <AuthGuard>
              <OnboardingGuard>
                <AppShell>
                  <BillsPage />
                </AppShell>
              </OnboardingGuard>
            </AuthGuard>
          }
        />
        <Route
          path="/subscriptions"
          element={
            <AuthGuard>
              <OnboardingGuard>
                <AppShell>
                  <SubscriptionsPage />
                </AppShell>
              </OnboardingGuard>
            </AuthGuard>
          }
        />
        <Route
          path="/analytics"
          element={
            <AuthGuard>
              <OnboardingGuard>
                <AppShell>
                  <AnalyticsPage />
                </AppShell>
              </OnboardingGuard>
            </AuthGuard>
          }
        />
        <Route
          path="/settings/notifications"
          element={
            <AuthGuard>
              <OnboardingGuard>
                <AppShell>
                  <NotificationPrefsPage />
                </AppShell>
              </OnboardingGuard>
            </AuthGuard>
          }
        />
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
