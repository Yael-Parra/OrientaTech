import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'

export default function EditProfile() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(false)

  const [formData, setFormData] = useState({
    full_name: '',
    date_of_birth: '',
    gender: '',
    location: '',
    education_level: '',
    previous_experience: '',
    area_of_interest: '',
    main_skills: '',
    digital_level: ''
  })

  useEffect(() => {
    loadProfileData()
  }, [])

  const loadProfileData = async () => {
    try {
      const token = localStorage.getItem('access_token')
      if (!token) {
        navigate('/')
        return
      }

      const res = await fetch('/profile/', {
        headers: {
          Authorization: `Bearer ${token}`
        }
      })

      if (!res.ok) {
        throw new Error('No se pudo cargar el perfil')
      }

      const data = await res.json()
      setFormData({
        full_name: data.full_name || '',
        date_of_birth: data.date_of_birth || '',
        gender: data.gender || '',
        location: data.location || '',
        education_level: data.education_level || '',
        previous_experience: data.previous_experience || '',
        area_of_interest: data.area_of_interest || '',
        main_skills: data.main_skills || '',
        digital_level: data.digital_level || ''
      })
      setLoading(false)
    } catch (err) {
      console.error(err)
      setError(err.message)
      setLoading(false)
    }
  }

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: value
    }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    try {
      setSaving(true)
      setError(null)

      const token = localStorage.getItem('access_token')
      const res = await fetch('/profile/', {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify(formData)
      })

      if (!res.ok) {
        const data = await res.json()
        throw new Error(data.detail || 'Error al actualizar el perfil')
      }

      setSuccess(true)
      setTimeout(() => {
        navigate('/dashboard')
      }, 2000)
    } catch (err) {
      console.error(err)
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-orange-500 via-orange-300 to-white flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-orange-600 mx-auto"></div>
          <p className="mt-4 text-gray-700">Cargando perfil...</p>
        </div>
      </div>
    )
  }

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
          <div className="flex items-center justify-between">
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
                <p className="text-sm text-gray-600">Editar Perfil</p>
              </div>
            </div>
            <button
              onClick={() => navigate('/dashboard')}
              className="text-orange-600 hover:text-orange-700 font-medium flex items-center space-x-1"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
              </svg>
              <span>Volver al Dashboard</span>
            </button>
          </div>
        </div>
      </header>

      {/* Form */}
      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 relative z-10">
        <div className="bg-white rounded-2xl shadow-2xl p-8">
          <div className="mb-8">
            <h2 className="text-3xl font-bold bg-gradient-to-r from-orange-500 to-orange-300 bg-clip-text text-transparent">
              Actualizar Mi Perfil
            </h2>
            <p className="text-gray-600 mt-2">Modifica tu información personal y profesional</p>
          </div>

          {success && (
            <div className="mb-6 p-4 bg-green-50 border-2 border-green-200 rounded-lg">
              <div className="flex items-center">
                <svg className="w-6 h-6 text-green-600 mr-2 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <div>
                  <p className="text-green-700 font-semibold">Perfil actualizado correctamente</p>
                  <p className="text-green-600 text-sm">Redirigiendo al dashboard...</p>
                </div>
              </div>
            </div>
          )}

          {error && (
            <div className="mb-6 p-4 bg-red-50 border-2 border-red-200 rounded-lg">
              <div className="flex items-center">
                <svg className="w-6 h-6 text-red-600 mr-2 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <p className="text-red-700">{error}</p>
              </div>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Personal Information */}
            <div className="border-b border-gray-200 pb-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
                <svg className="w-5 h-5 text-orange-500 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
                Información Personal
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-gray-700 font-semibold mb-2">
                    Nombre Completo
                  </label>
                  <input
                    type="text"
                    name="full_name"
                    value={formData.full_name}
                    onChange={handleChange}
                    className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:border-orange-500 focus:outline-none transition duration-200"
                  />
                </div>

                <div>
                  <label className="block text-gray-700 font-semibold mb-2">
                    Fecha de Nacimiento
                  </label>
                  <input
                    type="date"
                    name="date_of_birth"
                    value={formData.date_of_birth}
                    onChange={handleChange}
                    className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:border-orange-500 focus:outline-none transition duration-200"
                  />
                </div>

                <div>
                  <label className="block text-gray-700 font-semibold mb-2">
                    Género
                  </label>
                  <select
                    name="gender"
                    value={formData.gender}
                    onChange={handleChange}
                    className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:border-orange-500 focus:outline-none transition duration-200"
                  >
                    <option value="">Selecciona...</option>
                    <option value="male">Masculino</option>
                    <option value="female">Femenino</option>
                    <option value="other">Otro</option>
                    <option value="prefer_not_to_say">Prefiero no decir</option>
                  </select>
                </div>

                <div>
                  <label className="block text-gray-700 font-semibold mb-2">
                    Ubicación
                  </label>
                  <input
                    type="text"
                    name="location"
                    value={formData.location}
                    onChange={handleChange}
                    placeholder="Ciudad, País"
                    className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:border-orange-500 focus:outline-none transition duration-200"
                  />
                </div>
              </div>
            </div>

            {/* Education & Professional */}
            <div className="border-b border-gray-200 pb-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
                <svg className="w-5 h-5 text-orange-500 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                </svg>
                Educación y Experiencia
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-gray-700 font-semibold mb-2">
                    Nivel Educativo
                  </label>
                  <select
                    name="education_level"
                    value={formData.education_level}
                    onChange={handleChange}
                    className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:border-orange-500 focus:outline-none transition duration-200"
                  >
                    <option value="">Selecciona...</option>
                    <option value="no_formal">Sin formación formal</option>
                    <option value="primary">Primaria</option>
                    <option value="secondary">Secundaria</option>
                    <option value="high_school">Bachillerato</option>
                    <option value="vocational">Formación Profesional</option>
                    <option value="bachelor">Grado</option>
                    <option value="master">Máster</option>
                    <option value="phd">Doctorado</option>
                  </select>
                </div>

                <div>
                  <label className="block text-gray-700 font-semibold mb-2">
                    Área de Interés
                  </label>
                  <input
                    type="text"
                    name="area_of_interest"
                    value={formData.area_of_interest}
                    onChange={handleChange}
                    placeholder="Frontend, Backend, Data Science..."
                    className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:border-orange-500 focus:outline-none transition duration-200"
                  />
                </div>

                <div className="md:col-span-2">
                  <label className="block text-gray-700 font-semibold mb-2">
                    Experiencia Previa
                  </label>
                  <textarea
                    name="previous_experience"
                    value={formData.previous_experience}
                    onChange={handleChange}
                    rows={4}
                    placeholder="Describe tu experiencia laboral anterior..."
                    className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:border-orange-500 focus:outline-none transition duration-200"
                  />
                </div>
              </div>
            </div>

            {/* Skills */}
            <div className="pb-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
                <svg className="w-5 h-5 text-orange-500 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
                Habilidades
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-gray-700 font-semibold mb-2">
                    Nivel Digital
                  </label>
                  <select
                    name="digital_level"
                    value={formData.digital_level}
                    onChange={handleChange}
                    className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:border-orange-500 focus:outline-none transition duration-200"
                  >
                    <option value="">Selecciona...</option>
                    <option value="basic">Básico</option>
                    <option value="intermediate">Intermedio</option>
                    <option value="advanced">Avanzado</option>
                    <option value="expert">Experto</option>
                  </select>
                </div>

                <div>
                  <label className="block text-gray-700 font-semibold mb-2">
                    Habilidades Principales
                  </label>
                  <input
                    type="text"
                    name="main_skills"
                    value={formData.main_skills}
                    onChange={handleChange}
                    placeholder="JavaScript, React, Python..."
                    className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:border-orange-500 focus:outline-none transition duration-200"
                  />
                  <p className="text-xs text-gray-500 mt-1">Separa las habilidades con comas</p>
                </div>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex gap-4 pt-6 border-t">
              <button
                type="submit"
                disabled={saving}
                className="flex-1 px-6 py-3 bg-gradient-to-r from-orange-500 to-orange-300 text-white rounded-lg hover:from-orange-600 hover:to-orange-400 transition duration-200 shadow-lg font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {saving ? (
                  <span className="flex items-center justify-center">
                    <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Guardando...
                  </span>
                ) : (
                  'Guardar Cambios'
                )}
              </button>
              
              <button
                type="button"
                onClick={() => navigate('/dashboard')}
                className="flex-1 px-6 py-3 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition duration-200 font-semibold"
              >
                Cancelar
              </button>
            </div>
          </form>
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
