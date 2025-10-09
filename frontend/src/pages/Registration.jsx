import { useState } from 'react'
import { Link } from 'react-router-dom'

const Registration = () => {
  const [currentStep, setCurrentStep] = useState(1)
  const [formData, setFormData] = useState({
    firstName: '',
    lastName: '',
    dateOfBirth: '',
    gender: '',
    location: '',
    educationLevel: '',
    study: '',
    previousExperience: '',
    softSkills: [],
    hardSkills: [],
    digitalLevel: '',
    objective: '',
    email: '',
    password: '',
    confirmPassword: ''
  })

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  // Helper: format backend validation/errors (arrays/objects) into a string
  const formatErrorForDisplay = (err) => {
    if (!err) return ''
    if (typeof err === 'string') return err
    if (Array.isArray(err)) {
      // FastAPI validation errors are usually an array of objects with { loc, msg, type }
      return err.map(e => (e.msg ? e.msg : JSON.stringify(e))).join('; ')
    }
    if (typeof err === 'object') {
      if (err.detail) return formatErrorForDisplay(err.detail)
      if (err.message) return String(err.message)
      return JSON.stringify(err)
    }
    return String(err)
  }

  const totalSteps = 6

  const genderOptions = [
    { value: 'male', label: 'Masculino' },
    { value: 'female', label: 'Femenino' },
    { value: 'other', label: 'Otro' },
    { value: 'prefer_not_to_say', label: 'Prefiero no decir' }
  ]

  const educationLevelOptions = [
    { value: 'no_formal', label: 'Sin educación formal' },
    { value: 'primary', label: 'Primaria' },
    { value: 'secondary', label: 'Secundaria' },
    { value: 'high_school', label: 'Bachillerato' },
    { value: 'vocational', label: 'Formación Profesional' },
    { value: 'bachelors', label: 'Grado Universitario' },
    { value: 'masters', label: 'Máster' },
    { value: 'phd', label: 'Doctorado' }
  ]

  const digitalLevelOptions = [
    { value: 'basic', label: 'Básico' },
    { value: 'intermediate', label: 'Intermedio' },
    { value: 'advanced', label: 'Avanzado' },
    { value: 'expert', label: 'Experto' }
  ]

  const studyOptions = [
    'Frontend Developer',
    'Backend Developer', 
    'Full Stack Developer',
    'Diseño UX/UI',
    'Inteligencia Artificial',
    'Data Science',
    'DevOps',
    'Ciberseguridad'
  ]

  const softSkillsOptions = [
    'Comunicación efectiva', 'Trabajo en equipo', 'Liderazgo', 'Adaptabilidad',
    'Resolución de problemas', 'Creatividad', 'Gestión del tiempo', 'Pensamiento crítico'
  ]

  const hardSkillsOptions = [
    'JavaScript', 'Python', 'React', 'Node.js', 'HTML/CSS', 'SQL',
    'Git', 'AWS', 'Docker', 'Figma', 'Photoshop', 'Agile/Scrum'
  ]

  const objectiveOptions = [
    'Crear mi propia startup',
    'Trabajar en una multinacional tech',
    'Consultoría tecnológica',
    'Trabajo freelancer',
    'Empresa local/nacional',
    'Emprendimiento social'
  ]

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target
    
    if (type === 'checkbox' && (name === 'softSkills' || name === 'hardSkills')) {
      setFormData(prev => ({
        ...prev,
        [name]: checked 
          ? [...prev[name], value]
          : prev[name].filter(skill => skill !== value)
      }))
    } else {
      setFormData(prev => ({
        ...prev,
        [name]: value
      }))
    }
  }

  const nextStep = () => {
    if (currentStep < totalSteps) {
      setCurrentStep(currentStep + 1)
    }
  }

  const prevStep = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1)
    }
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    ;(async () => {
      try {
        if (formData.password !== formData.confirmPassword) {
          setError('Las contraseñas no coinciden')
          return
        }
        
        // Validar longitud de contraseña (bcrypt soporta máximo 72 bytes)
        if (formData.password.length > 72) {
          setError('La contraseña no puede tener más de 72 caracteres')
          return
        }
        
        if (formData.password.length < 8) {
          setError('La contraseña debe tener al menos 8 caracteres')
          return
        }
        
        setError(null)
        setLoading(true)

        // Construir nombre completo para el registro
        const fullName = `${(formData.firstName || '').trim()} ${(formData.lastName || '').trim()}`.trim()

        // 1) Register user (nombre, email + password)
        const registerRes = await fetch('/auth/register', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ 
            nombre: fullName,
            email: formData.email, 
            password: formData.password 
          })
        })

        const registerData = await registerRes.json().catch(() => ({}))
        if (!registerRes.ok) {
          setError(formatErrorForDisplay(registerData))
          return
        }

        // 2) Auto-login to obtain token
        const loginRes = await fetch('/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email: formData.email, password: formData.password })
        })

        const loginData = await loginRes.json()
        if (!loginRes.ok) {
          // Account created but login failed - instruct user to login manually
          setError('Cuenta creada, pero no se pudo iniciar sesión automáticamente. Por favor inicia sesión manualmente.')
          return
        }

        const token = loginData.access_token
        if (!token) {
          setError('No se obtuvo token tras el login')
          return
        }

        console.log('🔑 Token obtenido:', token) // Debug
        console.log('👤 User ID del login:', loginData) // Debug

        // 3) Build profile payload mapping frontend fields -> backend model
        // fullName ya está definido arriba
        const mainSkillsArray = [ ...(formData.hardSkills || []), ...(formData.softSkills || []) ]
        const main_skills = mainSkillsArray.length ? mainSkillsArray.join(', ') : null

        const profilePayload = {
          full_name: fullName || null,
          date_of_birth: formData.dateOfBirth || null,
          gender: formData.gender || null,
          location: formData.location || null,
          education_level: formData.educationLevel || null,
          previous_experience: formData.previousExperience || null,
          area_of_interest: formData.study || formData.objective || null,
          main_skills: main_skills,
          digital_level: formData.digitalLevel || null,
          resume_path: null
        }

        console.log('📋 Profile payload:', profilePayload) // Debug

        // 4) Create profile using token
        const profileRes = await fetch('/profile/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify(profilePayload)
        })

        console.log('📡 Profile response status:', profileRes.status) // Debug

        if (profileRes.ok) {
          // Success: profile created - guardar token y redirigir al dashboard
          localStorage.setItem('access_token', token)
          localStorage.setItem('token_type', 'bearer')
          window.location.href = '/dashboard'
        } else {
          const profileData = await profileRes.json().catch(() => ({}))
          // If profile exists conflict, still redirect to dashboard
          if (profileRes.status === 409) {
            localStorage.setItem('access_token', token)
            localStorage.setItem('token_type', 'bearer')
            window.location.href = '/dashboard'
          } else {
            setError(formatErrorForDisplay(profileData) || 'Error creando perfil')
          }
        }

      } catch (err) {
        console.error(err)
        setError(err.message || 'Error de conexión')
      } finally {
        setLoading(false)
      }
    })()
  }

  const renderStep = () => {
    switch(currentStep) {
      case 1:
        return (
          <div className="space-y-6">
            <div className="text-center mb-8">
              <h2 className="text-2xl font-bold text-gray-800">¡Bienvenido/a!</h2>
              <p className="text-gray-600 mt-2">Comencemos conociendo tu información personal</p>
            </div>
            
            <div>
              <label className="block text-gray-700 font-semibold mb-2">Nombre</label>
              <input
                type="text"
                name="firstName"
                value={formData.firstName}
                onChange={handleChange}
                className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:border-orange-500 focus:outline-none transition duration-200"
                placeholder="Tu nombre"
                required
              />
            </div>
            
            <div>
              <label className="block text-gray-700 font-semibold mb-2">Apellidos</label>
              <input
                type="text"
                name="lastName"
                value={formData.lastName}
                onChange={handleChange}
                className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:border-orange-500 focus:outline-none transition duration-200"
                placeholder="Tus apellidos"
                required
              />
            </div>

            <div>
              <label className="block text-gray-700 font-semibold mb-2">Fecha de Nacimiento</label>
              <input
                type="date"
                name="dateOfBirth"
                value={formData.dateOfBirth}
                onChange={handleChange}
                className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:border-orange-500 focus:outline-none transition duration-200"
                required
              />
            </div>

            <div>
              <label className="block text-gray-700 font-semibold mb-2">Género</label>
              <select
                name="gender"
                value={formData.gender}
                onChange={handleChange}
                className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:border-orange-500 focus:outline-none transition duration-200"
                required
              >
                <option value="">Selecciona una opción</option>
                {genderOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-gray-700 font-semibold mb-2">Ubicación</label>
              <input
                type="text"
                name="location"
                value={formData.location}
                onChange={handleChange}
                className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:border-orange-500 focus:outline-none transition duration-200"
                placeholder="Ciudad, País"
                required
              />
            </div>
          </div>
        )

      case 2:
        return (
          <div className="space-y-6">
            <div className="text-center mb-8">
              <h2 className="text-2xl font-bold text-gray-800">Tu educación y área de estudio</h2>
              <p className="text-gray-600 mt-2">¿Cuál es tu nivel educativo y qué estás aprendiendo?</p>
            </div>
            
            <div>
              <label className="block text-gray-700 font-semibold mb-2">Nivel de Educación</label>
              <select
                name="educationLevel"
                value={formData.educationLevel}
                onChange={handleChange}
                className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:border-orange-500 focus:outline-none transition duration-200"
                required
              >
                <option value="">Selecciona tu nivel educativo</option>
                {educationLevelOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-gray-700 font-semibold mb-2">Área de Estudio en Factoría F5</label>
              <div className="grid grid-cols-1 gap-3">
                {studyOptions.map((option) => (
                  <label key={option} className="flex items-center p-4 border-2 border-gray-200 rounded-lg hover:border-orange-300 cursor-pointer transition duration-200">
                    <input
                      type="radio"
                      name="study"
                      value={option}
                      checked={formData.study === option}
                      onChange={handleChange}
                      className="mr-3 h-4 w-4 text-orange-500 focus:ring-orange-500"
                    />
                    <span className="font-medium text-gray-700">{option}</span>
                  </label>
                ))}
              </div>
            </div>
          </div>
        )

      case 3:
        return (
          <div className="space-y-6">
            <div className="text-center mb-8">
              <h2 className="text-2xl font-bold text-gray-800">Tu experiencia previa</h2>
              <p className="text-gray-600 mt-2">Cuéntanos sobre tu background profesional</p>
            </div>
            
            <div>
              <label className="block text-gray-700 font-semibold mb-2">
                ¿Qué experiencia laboral tienes? (mecánico, abogado, comercial, etc.)
              </label>
              <textarea
                name="previousExperience"
                value={formData.previousExperience}
                onChange={handleChange}
                rows="5"
                className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:border-orange-500 focus:outline-none transition duration-200"
                placeholder="Describe tu experiencia profesional anterior..."
                required
              />
            </div>
          </div>
        )

      case 4:
        return (
          <div className="space-y-6">
            <div className="text-center mb-8">
              <h2 className="text-2xl font-bold text-gray-800">Tus habilidades</h2>
              <p className="text-gray-600 mt-2">Selecciona las habilidades que ya posees</p>
            </div>

            <div>
              <h3 className="text-lg font-semibold text-orange-600 mb-4">Nivel Digital</h3>
              <select
                name="digitalLevel"
                value={formData.digitalLevel}
                onChange={handleChange}
                className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:border-orange-500 focus:outline-none transition duration-200"
                required
              >
                <option value="">Selecciona tu nivel</option>
                {digitalLevelOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>
            
            <div>
              <h3 className="text-lg font-semibold text-orange-600 mb-4">Soft Skills</h3>
              <div className="grid grid-cols-2 gap-3">
                {softSkillsOptions.map((skill) => (
                  <label key={skill} className="flex items-center p-3 border border-gray-200 rounded-lg hover:bg-orange-50 cursor-pointer transition duration-200">
                    <input
                      type="checkbox"
                      name="softSkills"
                      value={skill}
                      checked={formData.softSkills.includes(skill)}
                      onChange={handleChange}
                      className="mr-2 h-4 w-4 text-orange-500 focus:ring-orange-500"
                    />
                    <span className="text-sm text-gray-700">{skill}</span>
                  </label>
                ))}
              </div>
            </div>

            <div>
              <h3 className="text-lg font-semibold text-orange-600 mb-4">Hard Skills</h3>
              <div className="grid grid-cols-2 gap-3">
                {hardSkillsOptions.map((skill) => (
                  <label key={skill} className="flex items-center p-3 border border-gray-200 rounded-lg hover:bg-orange-50 cursor-pointer transition duration-200">
                    <input
                      type="checkbox"
                      name="hardSkills"
                      value={skill}
                      checked={formData.hardSkills.includes(skill)}
                      onChange={handleChange}
                      className="mr-2 h-4 w-4 text-orange-500 focus:ring-orange-500"
                    />
                    <span className="text-sm text-gray-700">{skill}</span>
                  </label>
                ))}
              </div>
            </div>
          </div>
        )

      case 5:
        return (
          <div className="space-y-6">
            <div className="text-center mb-8">
              <h2 className="text-2xl font-bold text-gray-800">Tu objetivo profesional</h2>
              <p className="text-gray-600 mt-2">¿Hacia dónde quieres dirigir tu carrera?</p>
            </div>
            
            <div className="space-y-3">
              {objectiveOptions.map((option) => (
                <label key={option} className="flex items-center p-4 border-2 border-gray-200 rounded-lg hover:border-orange-300 cursor-pointer transition duration-200">
                  <input
                    type="radio"
                    name="objective"
                    value={option}
                    checked={formData.objective === option}
                    onChange={handleChange}
                    className="mr-3 h-4 w-4 text-orange-500 focus:ring-orange-500"
                  />
                  <span className="font-medium text-gray-700">{option}</span>
                </label>
              ))}
            </div>
          </div>
        )

      case 6:
        return (
          <div className="space-y-6">
            <div className="text-center mb-8">
              <h2 className="text-2xl font-bold text-gray-800">Configuración de cuenta</h2>
              <p className="text-gray-600 mt-2">Último paso para completar tu registro</p>
            </div>
            
            <div>
              <label className="block text-gray-700 font-semibold mb-2">Email</label>
              <input
                type="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:border-orange-500 focus:outline-none transition duration-200"
                placeholder="tu@email.com"
                required
              />
            </div>
            
            <div>
              <label className="block text-gray-700 font-semibold mb-2">Contraseña</label>
              <input
                type="password"
                name="password"
                value={formData.password}
                onChange={handleChange}
                maxLength={72}
                className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:border-orange-500 focus:outline-none transition duration-200"
                placeholder="••••••••"
                required
              />
              <p className="text-xs text-gray-500 mt-1">Mínimo 8 caracteres, máximo 72</p>
            </div>
            
            <div>
              <label className="block text-gray-700 font-semibold mb-2">Confirmar contraseña</label>
              <input
                type="password"
                name="confirmPassword"
                value={formData.confirmPassword}
                onChange={handleChange}
                maxLength={72}
                className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:border-orange-500 focus:outline-none transition duration-200"
                placeholder="••••••••"
                required
              />
            </div>
          </div>
        )

      default:
        return null
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-500 via-orange-300 to-white flex items-center justify-center p-4 relative overflow-hidden">
      {/* Banner geométrico superior derecho */}
      <img 
        src="/img/Banner-geometrico-1.png" 
        alt=""
        className="absolute top-0 right-0 w-72 h-72 opacity-15 z-0"
      />
      {/* Banner geométrico inferior izquierdo */}
      <img 
        src="/img/Banner-geometrico-2.png" 
        alt=""
        className="absolute bottom-0 left-0 w-72 h-72 opacity-15 z-0"
      />
      
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl p-8 relative z-10">
        {/* Header con logo */}
        <div className="text-center mb-8">
          <Link to="/" className="inline-block">
            <div className="w-16 h-16 mx-auto mb-4 p-2 bg-white rounded-2xl shadow-lg">
              <img 
                src="/img/logo-factoria-f5.png" 
                alt="Factoría F5 Logo"
                className="w-full h-full object-contain"
              />
            </div>
          </Link>
          <h1 className="text-2xl font-bold bg-gradient-to-r from-orange-500 to-orange-300 bg-clip-text text-transparent">
            OrientaTech
          </h1>
        </div>

        {/* Barra de progreso */}
        <div className="mb-8">
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm font-medium text-gray-600">Paso {currentStep} de {totalSteps}</span>
            <span className="text-sm font-medium text-orange-600">{Math.round((currentStep / totalSteps) * 100)}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className="bg-gradient-to-r from-orange-500 to-orange-300 h-2 rounded-full transition-all duration-300"
              style={{ width: `${(currentStep / totalSteps) * 100}%` }}
            ></div>
          </div>
        </div>

        {/* Contenido del paso actual */}
        <form onSubmit={currentStep === totalSteps ? handleSubmit : (e) => e.preventDefault()}>
          {renderStep()}

          {/* Botones de navegación */}
          <div className="flex justify-between mt-8">
            {currentStep > 1 ? (
              <button
                type="button"
                onClick={prevStep}
                className="px-6 py-3 border-2 border-orange-500 text-orange-500 rounded-lg font-semibold hover:bg-orange-50 transition duration-200"
              >
                Anterior
              </button>
            ) : (
              <Link
                to="/"
                className="px-6 py-3 border-2 border-gray-300 text-gray-500 rounded-lg font-semibold hover:bg-gray-50 transition duration-200"
              >
                Volver al login
              </Link>
            )}

            {currentStep < totalSteps ? (
              <button
                type="button"
                onClick={nextStep}
                className="px-6 py-3 bg-gradient-to-r from-orange-500 to-orange-300 text-white rounded-lg font-semibold hover:from-orange-600 hover:to-orange-400 transition duration-200"
              >
                Siguiente
              </button>
            ) : (
              <button
                type="submit"
                disabled={loading}
                className="px-6 py-3 bg-gradient-to-r from-orange-500 to-orange-300 text-white rounded-lg font-semibold hover:from-orange-600 hover:to-orange-400 transition duration-200 disabled:opacity-60"
              >
                {loading ? 'Creando cuenta...' : 'Completar registro'}
              </button>
            )}
          </div>
        </form>
        {error && <p className="text-sm text-red-600 mt-4">{error}</p>}

        {/* Footer */}
        <div className="mt-8 text-center">
          <div className="flex items-center justify-center">
            <span className="text-xs font-bold text-orange-500">FACTORÍA F5 </span>
            <span className="text-xs text-gray-400 ml-1">- Transformamos talento, creamos oportunidades</span>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Registration