import { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import useAuthStore from './stores/authStore';
import LoginNew from './pages/LoginNew';
import WatchlistsNew from './pages/WatchlistsNew';
import WatchlistDetail from './pages/WatchlistDetail';
import AISidebar from './components/AISidebar';
import AIToggleButton from './components/AIToggleButton';

function ProtectedRoute({ children }) {
  const { user, loading } = useAuthStore();

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-gray-600">Loading...</div>
      </div>
    );
  }

  return user ? children : <Navigate to="/" replace />;
}

function AIOverlay() {
  const { user } = useAuthStore();
  if (!user) return null;
  return (
    <>
      <AISidebar />
      <AIToggleButton />
    </>
  );
}

function App() {
  const { checkAuth } = useAuthStore();

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  return (
    <BrowserRouter>
      <AIOverlay />
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
      </Routes>
    </BrowserRouter>
  );
}

export default App;
