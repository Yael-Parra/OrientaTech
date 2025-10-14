import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import ProfileTab from '../components/dashboard/ProfileTab'
import AssistantTab from '../components/dashboard/AssistantTab'
import ResourcesTab from '../components/dashboard/ResourcesTab'

const Dashboard = () => {
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState('profile')
  const [loading, setLoading] = useState(true)
  const [userData, setUserData] = useState(null)
  const [profileData, setProfileData] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    loadUserData()
  }, [])

  const loadUserData = async () => {
    try {
      const token = localStorage.getItem('access_token')
      if (!token) {
        navigate('/')
        return
      }

      // Get user data
      const userRes = await fetch('/auth/me', {
        headers: {
          Authorization: `Bearer ${token}`
        }
      })

      if (!userRes.ok) {
        throw new Error('No autorizado')
      }

      const user = await userRes.json()
      setUserData(user)

      // Get profile data
      const profileRes = await fetch('/profile/', {
        headers: {
          Authorization: `Bearer ${token}`
        }
      })

      if (profileRes.ok) {
        const profile = await profileRes.json()
        setProfileData(profile)
      } else {
        console.log('Profile not found, using default values')
        setProfileData({})
      }

    } catch (err) {
      console.error('Error loading user data:', err)
      setError(err.message)
      if (err.message === 'No autorizado') {
        localStorage.removeItem('access_token')
        localStorage.removeItem('token_type')
        navigate('/')
      }
    } finally {
      setLoading(false)
    }
  }

  const handleLogout = () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('token_type')
    navigate('/')
  }

  const handleProfileUpdate = () => {
    // Callback to reload data when profile is updated from child components
    loadUserData()
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-orange-500 via-orange-300 to-white flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-orange-600 mx-auto"></div>
          <p className="mt-4 text-gray-700">Cargando...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-orange-500 via-orange-300 to-white flex items-center justify-center">
        <div className="text-center">
          <div className="bg-white rounded-lg shadow-lg p-8">
            <svg className="w-16 h-16 text-red-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
            <h2 className="text-xl font-bold text-gray-800 mb-2">Error</h2>
            <p className="text-gray-600">{error}</p>
            <button 
              onClick={() => navigate('/')}
              className="mt-4 bg-orange-500 text-white px-4 py-2 rounded-lg hover:bg-orange-600 transition duration-200"
            >
              Volver al inicio
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-500 via-orange-300 to-white">
      {/* Decorative Elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <img 
          src="/img/banner1.png" 
          alt="Banner" 
          className="absolute top-10 right-10 w-64 h-64 object-contain opacity-15"
        />
        <img 
          src="/img/banner2.png" 
          alt="Banner" 
          className="absolute bottom-10 left-10 w-48 h-48 object-contain opacity-10"
        />
      </div>

      {/* Header */}
      <header className="relative z-10 bg-white/90 backdrop-blur-sm shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center">
              <div className="w-12 h-12 bg-gradient-to-r from-orange-500 to-orange-300 rounded-xl p-1 mr-4">
                <img 
                  src="/img/logo-factoria-f5.png" 
                  alt="OrientaTech" 
                  className="w-full h-full object-contain"
                />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-800">OrientaTech</h1>
                <p className="text-sm text-gray-600">Panel de Control</p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-gray-700">Hola, {userData?.email}</span>
              <button
                onClick={handleLogout}
                className="bg-gradient-to-r from-orange-500 to-orange-300 text-white px-4 py-2 rounded-lg hover:from-orange-600 hover:to-orange-400 transition duration-200 shadow-md"
              >
                Cerrar Sesión
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 relative z-10">
        {/* Tabs */}
        <div className="bg-white rounded-xl shadow-lg overflow-hidden">
          <div className="border-b border-gray-200">
            <nav className="flex -mb-px">
              <button
                onClick={() => setActiveTab('profile')}
                className={`flex-1 py-4 px-6 text-center font-semibold transition-colors duration-200 ${
                  activeTab === 'profile'
                    ? 'border-b-2 border-orange-500 text-orange-600 bg-orange-50'
                    : 'text-gray-600 hover:text-orange-500 hover:bg-gray-50'
                }`}
              >
                <svg className="w-5 h-5 inline-block mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
                Mi Perfil
              </button>
              <button
                onClick={() => setActiveTab('assistant')}
                className={`flex-1 py-4 px-6 text-center font-semibold transition-colors duration-200 ${
                  activeTab === 'assistant'
                    ? 'border-b-2 border-orange-500 text-orange-600 bg-orange-50'
                    : 'text-gray-600 hover:text-orange-500 hover:bg-gray-50'
                }`}
              >
                <svg className="w-5 h-5 inline-block mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
                Asistente IA
              </button>
              <button
                onClick={() => setActiveTab('resources')}
                className={`flex-1 py-4 px-6 text-center font-semibold transition-colors duration-200 ${
                  activeTab === 'resources'
                    ? 'border-b-2 border-orange-500 text-orange-600 bg-orange-50'
                    : 'text-gray-600 hover:text-orange-500 hover:bg-gray-50'
                }`}
              >
                <svg className="w-5 h-5 inline-block mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
                Recursos
              </button>
            </nav>
          </div>

          {/* Tab Content */}
          <div className="p-8">
            {activeTab === 'profile' && (
              <ProfileTab 
                userData={userData} 
                profileData={profileData} 
                onProfileUpdate={handleProfileUpdate}
              />
            )}

            {activeTab === 'assistant' && (
              <AssistantTab 
                userData={userData} 
                onLoadDocuments={handleProfileUpdate}
              />
            )}

            {activeTab === 'resources' && (
              <ResourcesTab 
                userData={userData} 
                profileData={profileData}
              />
            )}
          </div>
        </div>
      </main>
    </div>
  )
}

export default Dashboard