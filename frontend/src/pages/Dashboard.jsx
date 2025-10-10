import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'

const Dashboard = () => {
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState('profile')
  const [loading, setLoading] = useState(true)
  const [userData, setUserData] = useState(null)
  const [profileData, setProfileData] = useState(null)
  const [error, setError] = useState(null)
  
  // CV Upload states
  const [selectedFile, setSelectedFile] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [uploadSuccess, setUploadSuccess] = useState(false)
  const [uploadError, setUploadError] = useState(null)

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
      }

      setLoading(false)
    } catch (err) {
      console.error(err)
      setError(err.message)
      setLoading(false)
      navigate('/')
    }
  }

  const handleLogout = () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('token_type')
    navigate('/')
  }

  const handleFileSelect = (e) => {
    const file = e.target.files?.[0]
    if (file) {
      const validTypes = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
      if (!validTypes.includes(file.type)) {
        setUploadError('Solo se permiten archivos PDF, DOC o DOCX')
        return
      }
      if (file.size > 5 * 1024 * 1024) {
        setUploadError('El archivo no puede superar 5MB')
        return
      }
      setSelectedFile(file)
      setUploadError(null)
      setUploadSuccess(false)
    }
  }

  const handleUploadCV = async () => {
    if (!selectedFile) {
      setUploadError('Por favor selecciona un archivo')
      return
    }

    try {
      setUploading(true)
      setUploadError(null)
      setUploadSuccess(false)

      const token = localStorage.getItem('access_token')
      const formData = new FormData()
      formData.append('file', selectedFile)

      const res = await fetch('/documents/upload', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`
        },
        body: formData
      })

      const data = await res.json()

      if (!res.ok) {
        throw new Error(data.detail || 'Error al subir el archivo')
      }

      setUploadSuccess(true)
      setSelectedFile(null)
      // Reload profile to show new CV
      await loadUserData()
    } catch (err) {
      console.error(err)
      setUploadError(err.message)
    } finally {
      setUploading(false)
    }
  }

  const getResourcesByArea = () => {
    const area = profileData?.area_of_interest?.toLowerCase() || ''
    
    const techResources = [
      { name: 'Stack Overflow Jobs', url: 'https://stackoverflow.com/jobs', description: 'Ofertas para desarrolladores' },
      { name: 'GitHub Jobs', url: 'https://github.com/jobs', description: 'Trabajos en tecnología' },
      { name: 'AngelList', url: 'https://angel.co/jobs', description: 'Startups tech' },
      { name: 'We Work Remotely', url: 'https://weworkremotely.com', description: 'Trabajo remoto tech' }
    ]

    const generalResources = [
      { name: 'LinkedIn Jobs', url: 'https://www.linkedin.com/jobs', description: 'Red profesional global' },
      { name: 'InfoJobs', url: 'https://www.infojobs.net', description: 'Portal de empleo España' },
      { name: 'Indeed', url: 'https://es.indeed.com', description: 'Búsqueda de empleo' },
      { name: 'Glassdoor', url: 'https://www.glassdoor.es', description: 'Ofertas y reviews' }
    ]

    const courses = [
      { name: 'freeCodeCamp', url: 'https://www.freecodecamp.org', description: 'Programación gratis' },
      { name: 'Coursera', url: 'https://www.coursera.org', description: 'Cursos online certificados' },
      { name: 'Udemy', url: 'https://www.udemy.com', description: 'Cursos variados' },
      { name: 'edX', url: 'https://www.edx.org', description: 'Cursos universitarios' }
    ]

    return { techResources, generalResources, courses }
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

  const { techResources, generalResources, courses } = getResourcesByArea()

  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-500 via-orange-300 to-white relative overflow-hidden">
      {/* Banners decorativos */}
      <img 
        src="/img/Banner-geometrico-1.png" 
        alt=""
        className="absolute top-0 right-0 w-64 h-64 object-contain opacity-15 z-0 pointer-events-none"
      />
      <img 
        src="/img/Banner-geometrico-2.png" 
        alt=""
        className="absolute bottom-0 left-0 w-64 h-64 object-contain opacity-15 z-0 pointer-events-none"
      />

      {/* Header */}
      <header className="bg-white shadow-lg relative z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center space-x-3">
              <div className="w-12 h-12 p-1 bg-white rounded-xl shadow-md">
                <img 
                  src="/img/logo-factoria-f5.png" 
                  alt="Factoría F5"
                  className="w-full h-full object-contain"
                />
              </div>
              <div>
                <h1 className="text-2xl font-bold bg-gradient-to-r from-orange-500 to-orange-300 bg-clip-text text-transparent">
                  OrientaTech
                </h1>
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

          <div className="p-8">
            {/* Profile Tab */}
            {activeTab === 'profile' && (
              <div>
                <div className="flex justify-between items-center mb-6">
                  <h2 className="text-2xl font-bold text-gray-800">Mi Información Personal</h2>
                  <button
                    onClick={() => navigate('/perfil/editar')}
                    className="bg-gradient-to-r from-orange-500 to-orange-300 text-white px-4 py-2 rounded-lg hover:from-orange-600 hover:to-orange-400 transition duration-200 shadow-md"
                  >
                    Editar Perfil
                  </button>
                </div>

                {profileData ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <p className="text-sm text-gray-600 font-semibold">Nombre Completo</p>
                      <p className="text-gray-800">{profileData.full_name || 'No especificado'}</p>
                    </div>
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <p className="text-sm text-gray-600 font-semibold">Email</p>
                      <p className="text-gray-800">{userData?.email}</p>
                    </div>
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <p className="text-sm text-gray-600 font-semibold">Fecha de Nacimiento</p>
                      <p className="text-gray-800">{profileData.date_of_birth || 'No especificado'}</p>
                    </div>
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <p className="text-sm text-gray-600 font-semibold">Género</p>
                      <p className="text-gray-800">{profileData.gender || 'No especificado'}</p>
                    </div>
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <p className="text-sm text-gray-600 font-semibold">Ubicación</p>
                      <p className="text-gray-800">{profileData.location || 'No especificado'}</p>
                    </div>
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <p className="text-sm text-gray-600 font-semibold">Nivel Educativo</p>
                      <p className="text-gray-800">{profileData.education_level || 'No especificado'}</p>
                    </div>
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <p className="text-sm text-gray-600 font-semibold">Área de Interés</p>
                      <p className="text-gray-800">{profileData.area_of_interest || 'No especificado'}</p>
                    </div>
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <p className="text-sm text-gray-600 font-semibold">Nivel Digital</p>
                      <p className="text-gray-800">{profileData.digital_level || 'No especificado'}</p>
                    </div>
                    <div className="bg-gray-50 p-4 rounded-lg md:col-span-2">
                      <p className="text-sm text-gray-600 font-semibold">Habilidades Principales</p>
                      <p className="text-gray-800">{profileData.main_skills || 'No especificado'}</p>
                    </div>
                    <div className="bg-gray-50 p-4 rounded-lg md:col-span-2">
                      <p className="text-sm text-gray-600 font-semibold">Experiencia Previa</p>
                      <p className="text-gray-800">{profileData.previous_experience || 'No especificado'}</p>
                    </div>
                    {profileData.resume_path && (
                      <div className="bg-gray-50 p-4 rounded-lg md:col-span-2">
                        <p className="text-sm text-gray-600 font-semibold">CV</p>
                        <p className="text-green-600">CV subido correctamente</p>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <p className="text-gray-600">No se encontró información de perfil</p>
                  </div>
                )}
              </div>
            )}

            {/* Assistant Tab */}
            {activeTab === 'assistant' && (
              <div>
                <h2 className="text-2xl font-bold text-gray-800 mb-6">Asistente de Reinvención Profesional</h2>
                
                <div className="bg-gradient-to-r from-orange-50 to-orange-100 border border-orange-200 rounded-lg p-6 mb-6">
                  <div className="flex items-start">
                    <svg className="w-6 h-6 text-orange-600 mt-1 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <div>
                      <h3 className="font-semibold text-orange-800 mb-2">Sube tu CV para análisis personalizado</h3>
                      <p className="text-orange-700 text-sm">
                        Nuestro asistente analizará tu CV y te ayudará a crear un plan de reinvención profesional adaptado a tus objetivos.
                      </p>
                    </div>
                  </div>
                </div>

                <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center mb-6 hover:border-orange-400 transition-colors">
                  <svg className="w-16 h-16 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                  </svg>
                  <input
                    type="file"
                    accept=".pdf,.doc,.docx"
                    onChange={handleFileSelect}
                    className="hidden"
                    id="cv-upload"
                  />
                  <label
                    htmlFor="cv-upload"
                    className="inline-block cursor-pointer bg-gradient-to-r from-orange-500 to-orange-300 text-white px-6 py-3 rounded-lg hover:from-orange-600 hover:to-orange-400 transition duration-200 shadow-md"
                  >
                    Seleccionar Archivo
                  </label>
                  <p className="text-sm text-gray-500 mt-2">PDF, DOC o DOCX (máx. 5MB)</p>
                  
                  {selectedFile && (
                    <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg inline-block">
                      <p className="text-green-700 font-semibold">Archivo seleccionado: {selectedFile.name}</p>
                    </div>
                  )}
                </div>

                {uploadError && (
                  <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
                    <p className="text-red-700">{uploadError}</p>
                  </div>
                )}

                {uploadSuccess && (
                  <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg">
                    <p className="text-green-700">CV subido y perfil actualizado correctamente</p>
                  </div>
                )}

                <button
                  onClick={handleUploadCV}
                  disabled={!selectedFile || uploading}
                  className="w-full bg-gradient-to-r from-orange-500 to-orange-300 text-white py-3 rounded-lg font-semibold hover:from-orange-600 hover:to-orange-400 transition duration-200 shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {uploading ? 'Subiendo...' : 'Subir CV y Actualizar Perfil'}
                </button>

                <div className="mt-8 bg-gray-50 rounded-lg p-6">
                  <h3 className="font-semibold text-gray-800 mb-4">Próximamente</h3>
                  <ul className="space-y-2 text-gray-600">
                    <li className="flex items-center">
                      <svg className="w-5 h-5 text-orange-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                      </svg>
                      Análisis automático de competencias
                    </li>
                    <li className="flex items-center">
                      <svg className="w-5 h-5 text-orange-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                      </svg>
                      Recomendaciones personalizadas de formación
                    </li>
                    <li className="flex items-center">
                      <svg className="w-5 h-5 text-orange-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                      </svg>
                      Plan de carrera adaptado a tu perfil
                    </li>
                    <li className="flex items-center">
                      <svg className="w-5 h-5 text-orange-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                      </svg>
                      Conexión con oportunidades laborales
                    </li>
                  </ul>
                </div>
              </div>
            )}

            {/* Resources Tab */}
            {activeTab === 'resources' && (
              <div>
                <h2 className="text-2xl font-bold text-gray-800 mb-6">Recursos de Empleabilidad y Formación</h2>
                
                {/* Tech Platforms */}
                <div className="mb-8">
                  <h3 className="text-xl font-semibold text-gray-800 mb-4 flex items-center">
                    <svg className="w-6 h-6 text-orange-500 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
                    </svg>
                    Plataformas Tecnológicas
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {techResources.map((resource, index) => (
                      <a
                        key={index}
                        href={resource.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="bg-white border-2 border-gray-200 rounded-lg p-4 hover:border-orange-400 hover:shadow-lg transition duration-200"
                      >
                        <div className="flex justify-between items-start">
                          <div>
                            <h4 className="font-semibold text-gray-800">{resource.name}</h4>
                            <p className="text-sm text-gray-600 mt-1">{resource.description}</p>
                          </div>
                          <svg className="w-5 h-5 text-orange-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                          </svg>
                        </div>
                      </a>
                    ))}
                  </div>
                </div>

                {/* General Platforms */}
                <div className="mb-8">
                  <h3 className="text-xl font-semibold text-gray-800 mb-4 flex items-center">
                    <svg className="w-6 h-6 text-orange-500 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                    </svg>
                    Portales de Empleo Generales
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {generalResources.map((resource, index) => (
                      <a
                        key={index}
                        href={resource.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="bg-white border-2 border-gray-200 rounded-lg p-4 hover:border-orange-400 hover:shadow-lg transition duration-200"
                      >
                        <div className="flex justify-between items-start">
                          <div>
                            <h4 className="font-semibold text-gray-800">{resource.name}</h4>
                            <p className="text-sm text-gray-600 mt-1">{resource.description}</p>
                          </div>
                          <svg className="w-5 h-5 text-orange-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                          </svg>
                        </div>
                      </a>
                    ))}
                  </div>
                </div>

                {/* Courses */}
                <div>
                  <h3 className="text-xl font-semibold text-gray-800 mb-4 flex items-center">
                    <svg className="w-6 h-6 text-orange-500 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                    </svg>
                    Plataformas de Formación
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {courses.map((resource, index) => (
                      <a
                        key={index}
                        href={resource.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="bg-white border-2 border-gray-200 rounded-lg p-4 hover:border-orange-400 hover:shadow-lg transition duration-200"
                      >
                        <div className="flex justify-between items-start">
                          <div>
                            <h4 className="font-semibold text-gray-800">{resource.name}</h4>
                            <p className="text-sm text-gray-600 mt-1">{resource.description}</p>
                          </div>
                          <svg className="w-5 h-5 text-orange-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                          </svg>
                        </div>
                      </a>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-12 relative z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 text-center">
          <p className="text-xs text-gray-500">Transformamos talento, creamos oportunidades</p>
          <div className="flex items-center justify-center mt-1">
            <span className="text-xs font-bold text-orange-500">FACTORÍA F5 </span>
            <span className="text-xs text-gray-400 ml-1">- Impulsando el talento digital</span>
          </div>
        </div>
      </footer>
    </div>
  )
}

export default Dashboard
