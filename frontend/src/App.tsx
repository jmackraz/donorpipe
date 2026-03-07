import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { BrowserRouter } from "react-router-dom"
import AppLayout from "./components/AppLayout"
import LoginForm from "./components/LoginForm"
import { AuthProvider, useAuth } from "./contexts/AuthContext"

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      staleTime: 5 * 60 * 1000,
    },
  },
})

function AppContent() {
  const { isAuthenticated } = useAuth()
  if (!isAuthenticated) return <LoginForm />
  return (
    <BrowserRouter>
      <AppLayout />
    </BrowserRouter>
  )
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </QueryClientProvider>
  )
}
