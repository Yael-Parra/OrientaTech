import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Login from './pages/Login'
import Registration from './pages/Registration'
import Dashboard from './pages/Dashboard'
import EditProfile from './pages/EditProfile'

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        <Routes>
          <Route path="/" element={<Login />} />
          <Route path="/registro" element={<Registration />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/perfil/editar" element={<EditProfile />} />
        </Routes>
      </div>
    </Router>
  )
}

export default App
