import { useState } from 'react'
import { Link } from 'react-router-dom'

const Registration = () => {
  const [currentStep, setCurrentStep] = useState(1)
  const [formData, setFormData] = useState({
    firstName: '',
    lastName: '',
    study: '',
    previousExperience: '',
    softSkills: [],
    hardSkills: [],
    objective: '',
    email: '',
    password: '',
    confirmPassword: ''
  })

  const totalSteps = 6

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
    if (formData.password !== formData.confirmPassword) {
      alert('Las contraseñas no coinciden')
      return
    }
    // Aquí se conectará con el backend
    console.log('Registration data:', formData)
    alert('¡Registro completado! Serás redirigido al login.')
  }

  const renderStep = () => {
    switch(currentStep) {
      case 1:
        return (
          <div className="space-y-6">
            <div className="text-center mb-8">
              <h2 className="text-2xl font-bold text-gray-800">¡Bienvenido/a!</h2>
              <p className="text-gray-600 mt-2">Comencemos conociendo tu nombre</p>
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
          </div>
        )

      case 2:
        return (
          <div className="space-y-6">
            <div className="text-center mb-8">
              <h2 className="text-2xl font-bold text-gray-800">Tu área de estudio</h2>
              <p className="text-gray-600 mt-2">¿Qué estás aprendiendo en Factoría F5?</p>
            </div>
            
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
                className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:border-orange-500 focus:outline-none transition duration-200"
                placeholder="••••••••"
                required
              />
            </div>
            
            <div>
              <label className="block text-gray-700 font-semibold mb-2">Confirmar contraseña</label>
              <input
                type="password"
                name="confirmPassword"
                value={formData.confirmPassword}
                onChange={handleChange}
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
    <div className="min-h-screen bg-gradient-to-br from-orange-500 via-red-500 to-red-600 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl p-8">
        {/* Header con logo */}
        <div className="text-center mb-8">
          <Link to="/" className="inline-block">
            <div className="bg-gradient-to-r from-orange-500 to-red-500 w-12 h-12 rounded-full mx-auto mb-4 flex items-center justify-center">
              <svg className="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 20 20">
                <path d="M10 2L3 7v11a1 1 0 001 1h3v-8h6v8h3a1 1 0 001-1V7l-7-5z"/>
              </svg>
            </div>
          </Link>
          <h1 className="text-2xl font-bold bg-gradient-to-r from-orange-500 to-red-500 bg-clip-text text-transparent">
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
              className="bg-gradient-to-r from-orange-500 to-red-500 h-2 rounded-full transition-all duration-300"
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
                className="px-6 py-3 bg-gradient-to-r from-orange-500 to-red-500 text-white rounded-lg font-semibold hover:from-orange-600 hover:to-red-600 transition duration-200"
              >
                Siguiente
              </button>
            ) : (
              <button
                type="submit"
                className="px-6 py-3 bg-gradient-to-r from-orange-500 to-red-500 text-white rounded-lg font-semibold hover:from-orange-600 hover:to-red-600 transition duration-200"
              >
                Completar registro
              </button>
            )}
          </div>
        </form>

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