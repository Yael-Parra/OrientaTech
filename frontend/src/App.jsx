import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Login from './pages/Login'
import Registration from './pages/Registration'

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        <Routes>
          <Route path="/" element={<Login />} />
          <Route path="/registro" element={<Registration />} />
        </Routes>
      </div>
    </Router>
  )
}

export default App
