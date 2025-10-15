import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'

const ProfileTab = ({ userData, profileData, onProfileUpdate }) => {
  const navigate = useNavigate()
  const [documents, setDocuments] = useState([])
  const [loadingDocs, setLoadingDocs] = useState(false)
  const [deletingDoc, setDeletingDoc] = useState(null)

  // Helper functions para manejar diferentes campos de la API
  const getDocumentName = (doc) => {
    if (doc?.original_name && doc.original_name !== 'undefined') return doc.original_name
    if (doc?.filename && doc.filename !== 'undefined') return doc.filename
    if (doc?.name && doc.name !== 'undefined') return doc.name
    return `Documento_${doc?.id || 'sin_id'}`
  }

  const getDocumentSize = (doc) => {
    // Según el modelo backend, el campo correcto es 'size'
    return doc.size || 0
  }

  const getDocumentDate = (doc) => {
    // Según el modelo backend, el campo correcto es 'uploaded_at'
    return doc.uploaded_at || new Date().toISOString()
  }

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  useEffect(() => {
    loadDocuments()
  }, [])

  const loadDocuments = async () => {
    try {
      setLoadingDocs(true)
      const token = localStorage.getItem('access_token')
      const res = await fetch('/documents/my-documents', {
        headers: {
          Authorization: `Bearer ${token}`
        }
      })

      if (res.ok) {
        const data = await res.json()
        setDocuments(data.documents || [])
      } else {
        console.error('Error loading documents:', res.status)
      }
    } catch (error) {
      console.error('Error loading documents:', error)
    } finally {
      setLoadingDocs(false)
    }
  }

  const handleDeleteDocument = async (docId, filename) => {
    if (!confirm(`¿Estás seguro de que quieres eliminar "${filename}"?`)) return

    try {
      setDeletingDoc(docId)
      const token = localStorage.getItem('access_token')
      const res = await fetch(`/documents/delete/${docId}`, {
        method: 'DELETE',
        headers: {
          Authorization: `Bearer ${token}`
        }
      })

      if (res.ok) {
        await loadDocuments() // Reload documents
      } else {
        alert('Error al eliminar el documento')
      }
    } catch (error) {
      console.error('Error deleting document:', error)
      alert('Error al eliminar el documento')
    } finally {
      setDeletingDoc(null)
    }
  }

  const handleDownloadDocument = async (docId, filename) => {
    try {
      const token = localStorage.getItem('access_token')
      const res = await fetch(`/documents/download/${docId}`, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      })

      if (res.ok) {
        const blob = await res.blob()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = filename
        document.body.appendChild(a)
        a.click()
        window.URL.revokeObjectURL(url)
        document.body.removeChild(a)
      }
    } catch (error) {
      console.error('Error downloading document:', error)
    }
  }

  const handleEditProfile = () => {
    navigate('/edit-profile')
  }

  if (!userData || !profileData) {
    return (
      <div className="text-center py-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-orange-500 mx-auto mb-4"></div>
        <p className="text-gray-600">Cargando información del perfil...</p>
      </div>
    )
  }

  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-800 mb-6">Mi Perfil</h2>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Personal Info Card */}
        <div className="bg-white border-2 border-gray-200 rounded-xl p-6 shadow-lg">
          <h3 className="text-xl font-semibold text-gray-800 mb-4 flex items-center">
            <svg className="w-5 h-5 text-orange-500 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
            </svg>
            Información Personal
          </h3>
          <div className="space-y-3">
            <div>
              <label className="block text-sm font-medium text-gray-700">Email</label>
              <p className="text-gray-900">{userData.email}</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Nombre Completo</label>
              <p className="text-gray-900">{profileData.full_name || 'No especificado'}</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Fecha de Nacimiento</label>
              <p className="text-gray-900">{profileData.date_of_birth || 'No especificado'}</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Género</label>
              <p className="text-gray-900">{
                profileData.gender ? 
                  ({
                    'male': 'Masculino',
                    'female': 'Femenino', 
                    'other': 'Otro',
                    'prefer_not_to_say': 'Prefiero no decir'
                  }[profileData.gender] || profileData.gender)
                : 'No especificado'
              }</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Ubicación</label>
              <p className="text-gray-900">{profileData.location || 'No especificado'}</p>
            </div>
          </div>
        </div>

        {/* Professional Info Card */}
        <div className="bg-white border-2 border-gray-200 rounded-xl p-6 shadow-lg">
          <h3 className="text-xl font-semibold text-gray-800 mb-4 flex items-center">
            <svg className="w-5 h-5 text-orange-500 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
            Información Profesional
          </h3>
          <div className="space-y-3">
            <div>
              <label className="block text-sm font-medium text-gray-700">Área de Interés</label>
              <p className="text-gray-900">{profileData.area_of_interest || 'No especificado'}</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Experiencia Previa</label>
              <p className="text-gray-900">{profileData.previous_experience || 'No especificado'}</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Habilidades Principales</label>
              <p className="text-gray-900">{profileData.main_skills || 'No especificado'}</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Nivel Digital</label>
              <p className="text-gray-900">{
                profileData.digital_level ? 
                  ({
                    'basic': 'Básico',
                    'intermediate': 'Intermedio',
                    'advanced': 'Avanzado',
                    'expert': 'Experto'
                  }[profileData.digital_level] || profileData.digital_level)
                : 'No especificado'
              }</p>
            </div>
          </div>
        </div>

        {/* Education Card */}
        <div className="bg-white border-2 border-gray-200 rounded-xl p-6 shadow-lg">
          <h3 className="text-xl font-semibold text-gray-800 mb-4 flex items-center">
            <svg className="w-5 h-5 text-orange-500 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 14l9-5-9-5-9 5 9 5z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 14l6.16-3.422a12.083 12.083 0 01.665 6.479A11.952 11.952 0 0012 20.055a11.952 11.952 0 00-6.824-2.998 12.078 12.078 0 01.665-6.479L12 14z" />
            </svg>
            Formación
          </h3>
          <div className="space-y-3">
            <div>
              <label className="block text-sm font-medium text-gray-700">Nivel Educativo</label>
              <p className="text-gray-900">{
                profileData.education_level ? 
                  ({
                    'no_formal': 'Sin educación formal',
                    'primary': 'Primaria',
                    'secondary': 'Secundaria', 
                    'high_school': 'Bachillerato',
                    'vocational': 'Formación Profesional',
                    'bachelors': 'Grado Universitario',
                    'masters': 'Máster',
                    'phd': 'Doctorado'
                  }[profileData.education_level] || profileData.education_level)
                : 'No especificado'
              }</p>
            </div>
          </div>
        </div>

        {/* Documents Management Card */}
        <div className="bg-white border-2 border-gray-200 rounded-xl p-6 shadow-lg lg:col-span-2">
          <h3 className="text-xl font-semibold text-gray-800 mb-4 flex items-center">
            <svg className="w-5 h-5 text-orange-500 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            Mis Documentos ({documents.length})
          </h3>
          
          {loadingDocs ? (
            <div className="flex items-center justify-center py-4">
              <svg className="w-5 h-5 animate-spin text-orange-500 mr-2" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="m4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              <span className="text-gray-600">Cargando documentos...</span>
            </div>
          ) : documents.length > 0 ? (
            <div className="space-y-3">
              {documents.map((doc) => (
                <div key={doc.id} className="bg-gray-50 rounded-lg p-4 flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="w-10 h-10 bg-orange-100 rounded-lg flex items-center justify-center">
                      <svg className="w-5 h-5 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                    </div>
                    <div>
                      <h4 className="font-medium text-gray-800">{getDocumentName(doc)}</h4>
                      <div className="flex items-center space-x-4 text-sm text-gray-500">
                        <span>{formatFileSize(getDocumentSize(doc))}</span>
                        <span>{new Date(getDocumentDate(doc)).toLocaleDateString('es-ES')}</span>
                        <span className="capitalize">{doc.type || 'Documento'}</span>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => handleDownloadDocument(doc.id, getDocumentName(doc))}
                      className="p-2 text-blue-600 hover:bg-blue-100 rounded-lg transition-colors"
                      title="Descargar"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                    </button>
                    <button
                      onClick={() => handleDeleteDocument(doc.id, getDocumentName(doc))}
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
          ) : (
            <div className="text-center py-6">
              <svg className="w-12 h-12 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <p className="text-gray-500 mb-2">No tienes documentos subidos</p>
              <p className="text-sm text-gray-400">Ve a la pestaña "Asistente" para subir tu CV</p>
            </div>
          )}
          
          <div className="mt-4 pt-4 border-t border-gray-200">
            <div className="text-sm text-gray-500 space-y-1">
              <p><strong>Última actualización del perfil:</strong> {
                profileData.updated_at ? 
                  new Date(profileData.updated_at).toLocaleDateString('es-ES', {
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric'
                  })
                : 'No disponible'
              }</p>
            </div>
          </div>
        </div>
      </div>

      {/* Edit Profile Button */}
      <div className="mt-8 text-center">
        <button
          onClick={handleEditProfile}
          className="bg-gradient-to-r from-orange-500 to-orange-300 text-white px-8 py-3 rounded-lg font-semibold hover:from-orange-600 hover:to-orange-400 transition duration-200 shadow-lg"
        >
          <svg className="w-5 h-5 inline-block mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
          </svg>
          Editar Perfil
        </button>
      </div>
    </div>
  )
}

export default ProfileTab