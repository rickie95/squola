import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import Layout from "./components/Layout";
import { AuthProvider, useAuth } from "./auth/AuthProvider";
import RequireAuth from "./auth/RequireAuth";
import DashboardPage from "./pages/DashboardPage";
import MattersPage from "./pages/MattersPage";
import TeachersPage from "./pages/TeachersPage";
import ClassesPage from "./pages/ClassesPage";
import TeacherDetailPage from "./pages/TeacherDetailPage";
import SchedulingPage from "./pages/SchedulingPage";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import AccountPage from "./pages/AccountPage";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60, // 1 minute
      retry: 1,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<PublicOnly><LoginPage /></PublicOnly>} />
            <Route path="/register" element={<PublicOnly><RegisterPage /></PublicOnly>} />
            <Route
              path="*"
              element={
                <RequireAuth>
                  <Layout>
                    <Routes>
                      <Route path="/" element={<DashboardPage />} />
                      <Route path="/matters" element={<MattersPage />} />
                      <Route path="/teachers" element={<TeachersPage />} />
                      <Route path="/teachers/:id" element={<TeacherDetailPage />} />
                      <Route path="/classes" element={<ClassesPage />} />
                      <Route path="/scheduling" element={<SchedulingPage />} />
                      <Route path="/account" element={<AccountPage />} />
                    </Routes>
                  </Layout>
                </RequireAuth>
              }
            />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  );
}

export default App;

function PublicOnly({ children }: { children: React.ReactNode }) {
  const { isLoading, isAuthenticated } = useAuth();
  if (isLoading) {
    return <div className="loading">Carico sessione...</div>;
  }
  if (isAuthenticated) {
    return <Navigate to="/" replace />;
  }
  return <>{children}</>;
}
