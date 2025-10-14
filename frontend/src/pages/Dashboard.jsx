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
  
  // RAG Assistant states
  const [messages, setMessages] = useState([])
  const [inputMessage, setInputMessage] = useState('')
  const [ragLoading, setRagLoading] = useState(false)
  const [hasCV, setHasCV] = useState(false)
  
  // Documents states
  const [documents, setDocuments] = useState([])
  const [documentsLoading, setDocumentsLoading] = useState(false)
  const [deletingDoc, setDeletingDoc] = useState(null)

  useEffect(() => {
    loadUserData()
  }, [])

  // Initialize chat when switching to assistant tab
  useEffect(() => {
    if (activeTab === 'assistant') {
      // Load documents when accessing assistant tab
      loadDocuments()
      
      // Show welcome message if chat is empty
      if (messages.length === 0) {
        const welcomeMessage = {
          id: Date.now(),
          text: '¡Hola! Soy tu asistente de reinvención profesional. Una vez que subas tu CV, podrás preguntarme sobre:\n\n• Tus habilidades y competencias principales\n• Tu experiencia laboral relevante\n• Recomendaciones de formación\n• Análisis de tu perfil profesional\n• Sugerencias de mejora para tu carrera\n\n¿Has subido ya tu CV?',
          isUser: false,
          timestamp: new Date()
        }
        setMessages([welcomeMessage])
      }
    }
  }, [activeTab])

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
      setHasCV(true)
      // Reload profile and documents
      await loadUserData()
      await loadDocuments()
    } catch (err) {
      console.error(err)
      setUploadError(err.message)
    } finally {
      setUploading(false)
    }
  }

  // RAG Assistant functions
  const handleSendMessage = async () => {
    if (!inputMessage.trim() || ragLoading) return

    const userMessage = { 
      id: Date.now(), 
      text: inputMessage, 
      isUser: true, 
      timestamp: new Date() 
    }
    
    setMessages(prev => [...prev, userMessage])
    setInputMessage('')
    setRagLoading(true)

    try {
      const token = localStorage.getItem('access_token')
      const searchRequest = {
        query: inputMessage,
        limit: 5,
        similarity_threshold: 0.3
      }

      const response = await fetch('/api/rag/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify(searchRequest)
      })

      // Check if response is JSON
      let data;
      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        data = await response.json()
      } else {
        const text = await response.text()
        throw new Error(`Servidor no disponible. Status: ${response.status}. Response: ${text}`)
      }

      if (!response.ok) {
        throw new Error(data.detail || `Error del servidor (${response.status}): ${data.message || 'Error desconocido'}`)
      }

      let assistantMessage = ''
      if (data.results && data.results.length > 0) {
        assistantMessage = `Basándome en tu CV, he encontrado información relevante sobre tu consulta:\n\n`
        data.results.forEach((result, index) => {
          // Use correct field names from SearchResultItem model
          const content = result.content_preview || result.content || result.text || 'Contenido no disponible'
          const score = result.similarity_score || result.score || 0
          const filename = result.original_filename || result.filename || 'Documento'
          
          assistantMessage += `📄 **${filename}**\n`
          assistantMessage += `${content.substring(0, 200)}${content.length > 200 ? '...' : ''}\n`
          if (score > 0) {
            assistantMessage += `*Relevancia: ${(score * 100).toFixed(1)}%*\n\n`
          }
        })
        
        // Add personalized recommendations based on the query
        const lowerQuery = inputMessage.toLowerCase()
        if (lowerQuery.includes('carrera') || lowerQuery.includes('mejorar') || lowerQuery.includes('fullstack')) {
          assistantMessage += `\n💡 **Recomendaciones personalizadas para tu carrera fullstack:**\n\n`
          assistantMessage += `• **Tecnologías emergentes**: Considera aprender TypeScript, GraphQL, o tecnologías serverless\n`
          assistantMessage += `• **Proyectos destacados**: Crea un portafolio que demuestre aplicaciones completas end-to-end\n`
          assistantMessage += `• **Especialización**: Profundiza en arquitecturas de microservicios o desarrollo móvil\n`
          assistantMessage += `• **Soft skills**: Desarrolla habilidades de liderazgo técnico y comunicación con stakeholders\n`
          assistantMessage += `• **Certificaciones**: Considera obtener certificaciones en cloud (AWS, Azure, GCP)`
        } else if (lowerQuery.includes('habilidad') || lowerQuery.includes('skill') || lowerQuery.includes('competencia')) {
          assistantMessage += `\n🎯 **Análisis de habilidades encontradas en tu perfil**`
        }
      } else {
        assistantMessage = 'No he encontrado información específica en tu CV sobre esa consulta. ¿Podrías reformular tu pregunta o ser más específico?'
      }

      const botMessage = {
        id: Date.now() + 1,
        text: assistantMessage,
        isUser: false,
        timestamp: new Date(),
        results: data.results || []
      }

      setMessages(prev => [...prev, botMessage])
    } catch (err) {
      console.error('RAG Error:', err)
      let errorText = 'Lo siento, ha ocurrido un error al procesar tu consulta.'
      
      if (err.message.includes('Failed to fetch') || err.message.includes('ECONNREFUSED')) {
        errorText = '🔧 Problema de conexión con el servidor:\n\n• Verifica que el backend esté corriendo en el puerto 8000\n• Revisa tu conexión a internet\n• Intenta recargar la página'
      } else if (err.message.includes('404') || err.message.includes('Servidor no disponible')) {
        errorText = '🔧 El endpoint RAG no está disponible. Por favor:\n\n1. Asegúrate de que el servidor esté corriendo en el puerto 8000\n2. Verifica que el comando `uvicorn main:app --reload` esté ejecutándose\n3. Revisa que no haya errores en el terminal del backend'
      } else if (err.message.includes('401') || err.message.includes('403')) {
        errorText = '🔐 Problema de autenticación. Por favor, cierra sesión e inicia sesión de nuevo.'
      } else if (err.message.includes('500')) {
        errorText = '🚨 Error interno del servidor. Por favor:\n\n• Revisa los logs del backend\n• Verifica que las dependencias RAG estén instaladas\n• Intenta de nuevo en unos momentos'
      } else {
        errorText += `\n\nDetalle técnico: ${err.message}`
      }
      
      const errorMessage = {
        id: Date.now() + 1,
        text: errorText,
        isUser: false,
        timestamp: new Date(),
        isError: true
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setRagLoading(false)
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  // Documents functions
  const loadDocuments = async () => {
    try {
      setDocumentsLoading(true)
      const token = localStorage.getItem('access_token')
      
      const response = await fetch('/documents/my-documents', {
        headers: {
          Authorization: `Bearer ${token}`
        }
      })

      if (response.ok) {
        const data = await response.json()
        setDocuments(data.documents || [])
        setHasCV(data.documents && data.documents.length > 0)
      } else {
        console.error('Error loading documents:', response.status)
      }
    } catch (error) {
      console.error('Error loading documents:', error)
    } finally {
      setDocumentsLoading(false)
    }
  }

  const handleDeleteDocument = async (documentId, filename) => {
    if (!documentId) {
      console.error('Document ID is undefined')
      alert('Error: ID del documento no válido')
      return
    }

    if (!window.confirm(`¿Estás seguro de que quieres eliminar "${filename || 'este documento'}"? Esta acción no se puede deshacer.`)) {
      return
    }

    try {
      setDeletingDoc(documentId)
      const token = localStorage.getItem('access_token')
      
      const response = await fetch(`/documents/delete/${documentId}`, {
        method: 'DELETE',
        headers: {
          Authorization: `Bearer ${token}`
        }
      })

      if (response.ok) {
        // Reload documents list
        await loadDocuments()
        
        // Show success message in chat if assistant tab is active
        if (activeTab === 'assistant') {
          const successMessage = {
            id: Date.now(),
            text: `✅ Documento "${filename}" eliminado exitosamente.`,
            isUser: false,
            timestamp: new Date()
          }
          setMessages(prev => [...prev, successMessage])
        }
      } else {
        const error = await response.json()
        alert(`Error al eliminar el documento: ${error.detail || 'Error desconocido'}`)
      }
    } catch (error) {
      console.error('Error deleting document:', error)
      alert('Error de conexión al eliminar el documento')
    } finally {
      setDeletingDoc(null)
    }
  }

  const handleDownloadDocument = async (documentId, filename) => {
    if (!documentId) {
      console.error('Document ID is undefined')
      alert('Error: ID del documento no válido')
      return
    }

    try {
      const token = localStorage.getItem('access_token')
      
      const response = await fetch(`/documents/download/${documentId}`, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      })

      if (response.ok) {
        const blob = await response.blob()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.style.display = 'none'
        a.href = url
        a.download = filename
        document.body.appendChild(a)
        a.click()
        window.URL.revokeObjectURL(url)
        document.body.removeChild(a)
      } else {
        alert('Error al descargar el documento')
      }
    } catch (error) {
      console.error('Error downloading document:', error)
      alert('Error de conexión al descargar el documento')
    }
  }

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const getDocumentTypeLabel = (type) => {
    const types = {
      'cv': '📄 CV',
      'cover_letter': '📝 Carta',
      'certificate': '🏆 Certificado',
      'other': '📁 Otro'
    }
    return types[type] || '📁 Documento'
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

                {/* Documents List */}
                <div className="mt-8 bg-white rounded-lg border border-gray-200 shadow-sm">
                  <div className="p-4 border-b border-gray-200 bg-gradient-to-r from-blue-50 to-blue-100">
                    <h3 className="font-semibold text-gray-800 flex items-center justify-between">
                      <div className="flex items-center">
                        <svg className="w-5 h-5 text-blue-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                        </svg>
                        Mis Documentos ({documents.length})
                      </div>
                      {documentsLoading && (
                        <svg className="w-4 h-4 animate-spin text-blue-600" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="m4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                      )}
                    </h3>
                    <p className="text-sm text-gray-600 mt-1">
                      Gestiona tus documentos subidos
                    </p>
                  </div>

                  <div className="p-4">
                    {documents.length === 0 ? (
                      <div className="text-center text-gray-500 py-8">
                        <svg className="w-12 h-12 text-gray-300 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                        <p>No tienes documentos subidos</p>
                        <p className="text-sm mt-1">Sube tu primer documento para comenzar</p>
                      </div>
                    ) : (
                      <div className="space-y-3">
                        {documents.map((doc, index) => (
                          <div key={doc.id || `doc-${index}`} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
                            <div className="flex items-center space-x-3 flex-1 min-w-0">
                              <div className="flex-shrink-0">
                                <span className="text-lg">{getDocumentTypeLabel(doc.type).split(' ')[0]}</span>
                              </div>
                              
                              <div className="flex-1 min-w-0">
                                <p className="font-medium text-gray-800 truncate" title={doc.original_name}>
                                  {doc.original_name || 'Documento sin nombre'}
                                </p>
                                <div className="flex items-center space-x-4 text-xs text-gray-500 mt-1">
                                  <span>{getDocumentTypeLabel(doc.type)}</span>
                                  <span>{formatFileSize(doc.size || 0)}</span>
                                  <span>{new Date(doc.uploaded_at).toLocaleDateString()}</span>
                                </div>
                              </div>
                            </div>
                            
                            <div className="flex items-center space-x-2 flex-shrink-0">
                              {/* Download button */}
                              <button
                                onClick={() => handleDownloadDocument(doc.id, doc.original_name)}
                                className="p-2 text-blue-600 hover:bg-blue-100 rounded-lg transition-colors"
                                title="Descargar"
                              >
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                                </svg>
                              </button>
                              
                              {/* Delete button */}
                              <button
                                onClick={() => handleDeleteDocument(doc.id, doc.original_name)}
                                disabled={deletingDoc === doc.id}
                                className="p-2 text-red-600 hover:bg-red-100 rounded-lg transition-colors disabled:opacity-50"
                                title="Eliminar"
                              >
                                {deletingDoc === doc.id ? (
                                  <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                    <path className="opacity-75" fill="currentColor" d="m4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                  </svg>
                                ) : (
                                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                  </svg>
                                )}
                              </button>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>

                {/* RAG Assistant Chat Interface */}
                <div className="mt-8 bg-white rounded-lg border border-gray-200 shadow-sm">
                  <div className="p-4 border-b border-gray-200 bg-gradient-to-r from-orange-50 to-orange-100">
                    <h3 className="font-semibold text-gray-800 flex items-center">
                      <svg className="w-5 h-5 text-orange-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                      </svg>
                      Consulta sobre tu CV
                    </h3>
                    <p className="text-sm text-gray-600 mt-1">
                      Haz preguntas específicas sobre tu CV y obtén análisis personalizados
                    </p>
                  </div>

                  {/* Chat Messages */}
                  <div className="h-96 overflow-y-auto p-4 space-y-4">
                    {messages.length === 0 ? (
                      <div className="text-center text-gray-500 mt-8">
                        <svg className="w-12 h-12 text-gray-300 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                        </svg>
                        <p>Sube tu CV y luego podrás hacer consultas como:</p>
                        <ul className="mt-2 text-sm space-y-1">
                          <li>• "¿Cuáles son mis habilidades principales?"</li>
                          <li>• "¿Qué experiencia laboral tengo?"</li>
                          <li>• "¿Qué formación necesito para [cargo específico]?"</li>
                        </ul>
                      </div>
                    ) : (
                      messages.map((message) => (
                        <div
                          key={message.id}
                          className={`flex ${message.isUser ? 'justify-end' : 'justify-start'}`}
                        >
                          <div
                            className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                              message.isUser
                                ? 'bg-gradient-to-r from-orange-500 to-orange-300 text-white'
                                : message.isError
                                ? 'bg-red-100 border border-red-200 text-red-800'
                                : 'bg-gray-100 text-gray-800'
                            }`}
                          >
                            {message.isUser ? (
                              <p className="text-sm">{message.text}</p>
                            ) : (
                              <div>
                                <p className="text-sm whitespace-pre-line">{message.text}</p>
                                {message.results && message.results.length > 0 && (
                                  <div className="mt-2 pt-2 border-t border-gray-200">
                                    <p className="text-xs text-gray-600">
                                      Encontrados {message.results.length} resultados relevantes
                                    </p>
                                  </div>
                                )}
                              </div>
                            )}
                            <p className="text-xs opacity-75 mt-1">
                              {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                            </p>
                          </div>
                        </div>
                      ))
                    )}

                    {/* Loading indicator */}
                    {ragLoading && (
                      <div className="flex justify-start">
                        <div className="bg-gray-100 px-4 py-2 rounded-lg">
                          <div className="flex space-x-1">
                            <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                            <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                            <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Input Area */}
                  <div className="border-t border-gray-200 p-4">
                    <div className="flex space-x-3">
                      <input
                        type="text"
                        value={inputMessage}
                        onChange={(e) => setInputMessage(e.target.value)}
                        onKeyPress={handleKeyPress}
                        placeholder="Pregunta algo sobre tu CV..."
                        className="flex-1 border-2 border-gray-200 rounded-lg px-4 py-2 focus:border-orange-500 focus:ring-0 outline-none transition-colors"
                        disabled={ragLoading}
                      />
                      <button
                        onClick={handleSendMessage}
                        disabled={!inputMessage.trim() || ragLoading}
                        className="bg-gradient-to-r from-orange-500 to-orange-300 text-white px-6 py-2 rounded-lg hover:from-orange-600 hover:to-orange-400 transition duration-200 shadow-md disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        {ragLoading ? (
                          <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                            <path className="opacity-75" fill="currentColor" d="m4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                          </svg>
                        ) : (
                          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                          </svg>
                        )}
                      </button>
                    </div>
                    
                    <div className="mt-2 text-xs text-gray-500 flex items-center justify-between">
                      <span>Presiona Enter para enviar</span>
                      <span className="flex items-center">
                        <svg className="w-3 h-3 text-green-500 mr-1" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                        </svg>
                        Análisis en tiempo real
                      </span>
                    </div>
                  </div>
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
