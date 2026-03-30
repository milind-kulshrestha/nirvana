import { useEffect, useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import useAuthStore from './stores/authStore';
import LoginNew from './pages/LoginNew';
import AgentHub from './pages/AgentHub';
import WatchlistsNew from './pages/WatchlistsNew';
import WatchlistDetail from './pages/WatchlistDetail';
import Settings from './pages/Settings';
import Discover from './pages/Discover';
import ETFDashboard from './pages/ETFDashboard';
import AppShell from './components/layout/AppShell';
import StartupScreen from './components/StartupScreen';
import OnboardingWizard from './components/OnboardingWizard';
import { API_BASE } from './config';

function ProtectedRoute({ children }) {
  const { user, loading } = useAuthStore();

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-muted-foreground">Loading...</div>
      </div>
    );
  }

  return user ? children : <Navigate to="/login" replace />;
}

function AuthenticatedApp() {
  const { user } = useAuthStore();
  const [showOnboarding, setShowOnboarding] = useState(false);
  const [missingKeys, setMissingKeys] = useState([]);
  const [onboardingChecked, setOnboardingChecked] = useState(false);

  useEffect(() => {
    if (!user || onboardingChecked) return;

    const checkOnboarding = async () => {
      try {
        const response = await fetch(`${API_BASE}/api/settings/status`, {
          credentials: 'include',
        });
        if (response.ok) {
          const data = await response.json();
          if (data.missing_keys && data.missing_keys.length > 0) {
            setMissingKeys(data.missing_keys);
            setShowOnboarding(true);
          }
        }
      } catch (error) {
        console.error('Error checking settings status:', error);
      } finally {
        setOnboardingChecked(true);
      }
    };

    checkOnboarding();
  }, [user, onboardingChecked]);

  return (
    <>
      {showOnboarding && (
        <OnboardingWizard
          missingKeys={missingKeys}
          onComplete={() => setShowOnboarding(false)}
        />
      )}
      <AppShell />
    </>
  );
}

function App() {
  const [backendReady, setBackendReady] = useState(false);
  const { checkAuth } = useAuthStore();

  useEffect(() => {
    if (backendReady) {
      checkAuth();
    }
  }, [backendReady, checkAuth]);

  if (!backendReady) {
    return <StartupScreen onReady={() => setBackendReady(true)} />;
  }

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginNew />} />
        <Route
          element={
            <ProtectedRoute>
              <AuthenticatedApp />
            </ProtectedRoute>
          }
        >
          <Route index element={<AgentHub />} />
          <Route path="watchlists" element={<WatchlistsNew />} />
          <Route path="watchlists/:id" element={<WatchlistDetail />} />
          <Route path="discover" element={<Discover />} />
          <Route path="etf" element={<ETFDashboard />} />
          <Route path="settings" element={<Settings />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
