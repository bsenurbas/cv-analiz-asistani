import { ThemeProvider } from './components/theme-provider'
import { Dashboard } from './components/dashboard/dashboard'

export default function App() {
  return (
    <ThemeProvider attribute="class" defaultTheme="dark" enableSystem>
      <Dashboard />
    </ThemeProvider>
  )
}