import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'

const Dashboard = () => {
  const [user, setUser] = useState(null)
  const [profile, setProfile] = useState(null)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('profile') // profile, rag, resources
  const [cvFile, setCvFile] = useState(null)
  const navigate = useNavigate()

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

      // Obtener info del usuario
      const userRes = await fetch('/auth/me', {
        headers: { Authorization: `Bearer ${token}` }
      })
      
      if (userRes.ok) {
        const userData = await userRes.json()
        setUser(userData)
      }

      // Obtener perfil
      const profileRes = await fetch('/profile/', {
        headers: { Authorization: `Bearer ${token}` }
      })

      if (profileRes.ok) {
        const profileData = await profileRes.json()
        setProfile(profileData)
      }
    } catch (error) {
      console.error('Error cargando datos:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleLogout = () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('token_type')
    navigate('/')
  }

  const handleCvUpload = (e) => {
    const file = e.target.files[0]
    if (file) {
      setCvFile(file)
      // TODO: Conectar con el endpoint de subida de CV cuando esté listo
      console.log('CV seleccionado:', file.name)
    }
  }

  // Recursos de empleabilidad basados en el área de estudio
  const getEmploymentResources = () => {
    const areaOfInterest = profile?.area_of_interest || ''
    
    const resources = {
      general: [
        { name: 'LinkedIn Jobs', url: 'https://www.linkedin.com/jobs/', category: 'Empleo' },
        { name: 'InfoJobs', url: 'https://www.infojobs.net/', category: 'Empleo' },
        { name: 'Indeed', url: 'https://es.indeed.com/', category: 'Empleo' },
        { name: 'Glassdoor', url: 'https://www.glassdoor.es/', category: 'Empleo' },
      ],
      tech: [
        { name: 'Stack Overflow Jobs', url: 'https://stackoverflow.com/jobs', category: 'Empleo Tech' },
        { name: 'GitHub Jobs', url: 'https://github.com/about/careers', category: 'Empleo Tech' },
        { name: 'AngelList', url: 'https://angel.co/jobs', category: 'Startups' },
        { name: 'Remote.co', url: 'https://remote.co/', category: 'Trabajo Remoto' },
      ],
      courses: [
        { name: 'freeCodeCamp', url: 'https://www.freecodecamp.org/', category: 'Cursos Gratis' },
        { name: 'Coursera', url: 'https://www.coursera.org/', category: 'Cursos' },
        { name: 'Udemy', url: 'https://www.udemy.com/', category: 'Cursos' },
        { name: 'Platzi', url: 'https://platzi.com/', category: 'Cursos Tech' },
        { name: 'EDX', url: 'https://www.edx.org/', category: 'Cursos Universitarios' },
      ]
    }

    // Recursos específicos según área de interés
    const specificResources = {
      'Frontend Developer': [
        { name: 'Frontend Mentor', url: 'https://www.frontendmentor.io/', category: 'Práctica' },
        { name: 'CSS-Tricks', url: 'https://css-tricks.com/', category: 'Recursos' },
      ],
      'Backend Developer': [
        { name: 'HackerRank', url: 'https://www.hackerrank.com/', category: 'Práctica' },
        { name: 'LeetCode', url: 'https://leetcode.com/', category: 'Práctica' },
      ],
      'Full Stack Developer': [
        { name: 'The Odin Project', url: 'https://www.theodinproject.com/', category: 'Cursos Gratis' },
        { name: 'Full Stack Open', url: 'https://fullstackopen.com/', category: 'Cursos Gratis' },
      ],
      'Diseño UX/UI': [
        { name: 'Behance', url: 'https://www.behance.net/', category: 'Portafolio' },
        { name: 'Dribbble', url: 'https://dribbble.com/', category: 'Inspiración' },
      ],
      'Data Science': [
        { name: 'Kaggle', url: 'https://www.kaggle.com/', category: 'Competencias' },
        { name: 'DataCamp', url: 'https://www.datacamp.com/', category: 'Cursos' },
      ],
    }

    return {
      general: resources.general,
      tech: resources.tech,
      courses: resources.courses,
      specific: specificResources[areaOfInterest] || []
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-orange-500 mx-auto"></div>
          <p className="mt-4 text-gray-600">Cargando...</p>
        </div>
      </div>
    )
  }

  const resources = getEmploymentResources()

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <img 
                src="/img/logo-factoria-f5.png" 
                alt="Factoría F5"
                className="h-10 w-10 object-contain"
              />
              <div>
                <h1 className="text-2xl font-bold text-gray-900">OrientaTech</h1>
                <p className="text-sm text-gray-500">Tu plan de reinvención profesional</p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <div className="text-right">
                <p className="text-sm font-medium text-gray-900">{profile?.full_name || user?.email}</p>
                <p className="text-xs text-gray-500">{user?.email}</p>
              </div>
              <button
                onClick={handleLogout}
                className="px-4 py-2 text-sm font-medium text-gray-700 hover:text-orange-600 transition"
              >
                Cerrar Sesión
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Navigation Tabs */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <nav className="flex space-x-8">
            <button
              onClick={() => setActiveTab('profile')}
              className={`py-4 px-1 border-b-2 font-medium text-sm transition ${
                activeTab === 'profile'
                  ? 'border-orange-500 text-orange-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              👤 Mi Perfil
            </button>
            <button
              onClick={() => setActiveTab('rag')}
              className={`py-4 px-1 border-b-2 font-medium text-sm transition ${
                activeTab === 'rag'
                  ? 'border-orange-500 text-orange-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              🤖 Asistente IA
            </button>
            <button
              onClick={() => setActiveTab('resources')}
              className={`py-4 px-1 border-b-2 font-medium text-sm transition ${
                activeTab === 'resources'
                  ? 'border-orange-500 text-orange-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              🔗 Recursos
            </button>
          </nav>
        </div>
      </div>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Perfil Tab */}
        {activeTab === 'profile' && (
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow-sm p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-2xl font-bold text-gray-900">Mi Perfil</h2>
                <Link
                  to="/perfil/editar"
                  className="px-4 py-2 bg-orange-500 text-white rounded-lg hover:bg-orange-600 transition"
                >
                  Editar Perfil
                </Link>
              </div>

              {profile ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-500">Nombre Completo</label>
                    <p className="mt-1 text-lg text-gray-900">{profile.full_name || 'No especificado'}</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-500">Email</label>
                    <p className="mt-1 text-lg text-gray-900">{user?.email}</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-500">Fecha de Nacimiento</label>
                    <p className="mt-1 text-lg text-gray-900">{profile.date_of_birth || 'No especificado'}</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-500">Género</label>
                    <p className="mt-1 text-lg text-gray-900">{profile.gender || 'No especificado'}</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-500">Ubicación</label>
                    <p className="mt-1 text-lg text-gray-900">{profile.location || 'No especificado'}</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-500">Nivel Educativo</label>
                    <p className="mt-1 text-lg text-gray-900">{profile.education_level || 'No especificado'}</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-500">Área de Interés</label>
                    <p className="mt-1 text-lg text-gray-900">{profile.area_of_interest || 'No especificado'}</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-500">Nivel Digital</label>
                    <p className="mt-1 text-lg text-gray-900">{profile.digital_level || 'No especificado'}</p>
                  </div>
                  <div className="md:col-span-2">
                    <label className="block text-sm font-medium text-gray-500">Experiencia Previa</label>
                    <p className="mt-1 text-gray-900">{profile.previous_experience || 'No especificado'}</p>
                  </div>
                  <div className="md:col-span-2">
                    <label className="block text-sm font-medium text-gray-500">Habilidades Principales</label>
                    <p className="mt-1 text-gray-900">{profile.main_skills || 'No especificado'}</p>
                  </div>
                </div>
              ) : (
                <div className="text-center py-8">
                  <p className="text-gray-500 mb-4">No has completado tu perfil aún.</p>
                  <Link
                    to="/registro"
                    className="inline-block px-6 py-3 bg-orange-500 text-white rounded-lg hover:bg-orange-600 transition"
                  >
                    Completar Perfil
                  </Link>
                </div>
              )}
            </div>
          </div>
        )}

        {/* RAG Tab */}
        {activeTab === 'rag' && (
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">🤖 Asistente de Reinvención Profesional</h2>
              <p className="text-gray-600 mb-6">
                Sube tu CV y nuestro asistente de IA te ayudará a crear un plan personalizado de reinvención profesional.
              </p>

              {/* CV Upload Section */}
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-orange-400 transition">
                <input
                  type="file"
                  id="cv-upload"
                  accept=".pdf,.doc,.docx"
                  onChange={handleCvUpload}
                  className="hidden"
                />
                <label htmlFor="cv-upload" className="cursor-pointer">
                  <div className="mb-4">
                    <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                    </svg>
                  </div>
                  <p className="text-sm text-gray-600">
                    {cvFile ? (
                      <span className="text-orange-600 font-medium">CV seleccionado: {cvFile.name}</span>
                    ) : (
                      <>
                        <span className="font-medium text-orange-600">Haz clic para subir</span> o arrastra tu CV aquí
                      </>
                    )}
                  </p>
                  <p className="text-xs text-gray-500 mt-1">PDF, DOC o DOCX (máx. 5MB)</p>
                </label>
              </div>

              {cvFile && (
                <div className="mt-6">
                  <button
                    className="w-full px-6 py-3 bg-orange-500 text-white rounded-lg hover:bg-orange-600 transition font-medium"
                    onClick={() => alert('Función de análisis con IA - Próximamente')}
                  >
                    Analizar CV y Generar Plan
                  </button>
                </div>
              )}

              {/* Placeholder for RAG results */}
              <div className="mt-8 p-6 bg-gray-50 rounded-lg">
                <h3 className="font-semibold text-gray-900 mb-3">💡 Próximamente:</h3>
                <ul className="space-y-2 text-sm text-gray-600">
                  <li>✓ Análisis automático de tu CV</li>
                  <li>✓ Identificación de habilidades transferibles</li>
                  <li>✓ Recomendaciones personalizadas de formación</li>
                  <li>✓ Sugerencias de posiciones laborales</li>
                  <li>✓ Plan de acción paso a paso</li>
                </ul>
              </div>
            </div>
          </div>
        )}

        {/* Resources Tab */}
        {activeTab === 'resources' && (
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-2">🔗 Recursos de Empleabilidad</h2>
              <p className="text-gray-600 mb-6">
                Explora plataformas de empleo, cursos y recursos para impulsar tu carrera en {profile?.area_of_interest || 'tecnología'}.
              </p>

              {/* Recursos Específicos */}
              {resources.specific.length > 0 && (
                <div className="mb-8">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">
                    📌 Para {profile?.area_of_interest}
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {resources.specific.map((resource, index) => (
                      <a
                        key={index}
                        href={resource.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:border-orange-400 hover:shadow-md transition"
                      >
                        <div>
                          <h4 className="font-medium text-gray-900">{resource.name}</h4>
                          <p className="text-sm text-gray-500">{resource.category}</p>
                        </div>
                        <svg className="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                        </svg>
                      </a>
                    ))}
                  </div>
                </div>
              )}

              {/* Plataformas de Empleo Tech */}
              <div className="mb-8">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">💼 Plataformas de Empleo Tech</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {resources.tech.map((resource, index) => (
                    <a
                      key={index}
                      href={resource.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:border-orange-400 hover:shadow-md transition"
                    >
                      <div>
                        <h4 className="font-medium text-gray-900">{resource.name}</h4>
                        <p className="text-sm text-gray-500">{resource.category}</p>
                      </div>
                      <svg className="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                      </svg>
                    </a>
                  ))}
                </div>
              </div>

              {/* Plataformas Generales */}
              <div className="mb-8">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">🌐 Plataformas Generales</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {resources.general.map((resource, index) => (
                    <a
                      key={index}
                      href={resource.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:border-orange-400 hover:shadow-md transition"
                    >
                      <div>
                        <h4 className="font-medium text-gray-900">{resource.name}</h4>
                        <p className="text-sm text-gray-500">{resource.category}</p>
                      </div>
                      <svg className="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                      </svg>
                    </a>
                  ))}
                </div>
              </div>

              {/* Cursos y Formación */}
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">📚 Cursos y Formación</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {resources.courses.map((resource, index) => (
                    <a
                      key={index}
                      href={resource.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:border-orange-400 hover:shadow-md transition"
                    >
                      <div>
                        <h4 className="font-medium text-gray-900">{resource.name}</h4>
                        <p className="text-sm text-gray-500">{resource.category}</p>
                      </div>
                      <svg className="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                      </svg>
                    </a>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  )
}

export default Dashboard
