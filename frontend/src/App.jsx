import { useEffect, useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import useAuthStore from './stores/authStore';
import useChatStore from './stores/chatStore';
import LoginNew from './pages/LoginNew';
import WatchlistsNew from './pages/WatchlistsNew';
import WatchlistDetail from './pages/WatchlistDetail';
import Settings from './pages/Settings';
import Discover from './pages/Discover';
import ETFDashboard from './pages/ETFDashboard';
import AISidebar from './components/AISidebar';
import AIToggleButton from './components/AIToggleButton';
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

  return user ? children : <Navigate to="/" replace />;
}

function App() {
  const [backendReady, setBackendReady] = useState(false);
  const { user, checkAuth } = useAuthStore();
  const { sidebarOpen } = useChatStore();
  const [showOnboarding, setShowOnboarding] = useState(false);
  const [missingKeys, setMissingKeys] = useState([]);
  const [onboardingChecked, setOnboardingChecked] = useState(false);

  useEffect(() => {
    if (backendReady) {
      checkAuth();
    }
  }, [backendReady, checkAuth]);

  // Check onboarding status after user is authenticated
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

  if (!backendReady) {
    return <StartupScreen onReady={() => setBackendReady(true)} />;
  }

  return (
    <BrowserRouter>
      <div className="flex h-screen w-screen overflow-hidden">
        <div className={`flex-1 min-w-0 overflow-auto transition-all duration-300`}>
          {showOnboarding && (
            <OnboardingWizard
              missingKeys={missingKeys}
              onComplete={() => setShowOnboarding(false)}
            />
          )}
          <Routes>
            <Route path="/" element={<LoginNew />} />
            <Route
              path="/watchlists"
              element={
                <ProtectedRoute>
                  <WatchlistsNew />
                </ProtectedRoute>
              }
            />
            <Route
              path="/watchlists/:id"
              element={
                <ProtectedRoute>
                  <WatchlistDetail />
                </ProtectedRoute>
              }
            />
            <Route
              path="/discover"
              element={
                <ProtectedRoute>
                  <Discover />
                </ProtectedRoute>
              }
            />
            <Route
              path="/etf"
              element={
                <ProtectedRoute>
                  <ETFDashboard />
                </ProtectedRoute>
              }
            />
            <Route
              path="/settings"
              element={
                <ProtectedRoute>
                  <Settings />
                </ProtectedRoute>
              }
            />
          </Routes>
        </div>
        {user && <AISidebar />}
        {user && <AIToggleButton />}
      </div>
    </BrowserRouter>
  );
}

export default App;
