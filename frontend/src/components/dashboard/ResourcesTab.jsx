import { useState, useEffect } from 'react'

const ResourcesTab = ({ userData, profileData }) => {
  const [ragRecommendations, setRagRecommendations] = useState([])
  const [loadingRecommendations, setLoadingRecommendations] = useState(false)
  const [recommendationsError, setRecommendationsError] = useState(null)

  // Load RAG recommendations when component mounts
  useEffect(() => {
    if (profileData?.area_of_interest) {
      loadRAGRecommendations()
    }
  }, [profileData])

  const loadRAGRecommendations = async () => {
    if (!userData?.id) return

    try {
      setLoadingRecommendations(true)
      setRecommendationsError(null)
      
      const token = localStorage.getItem('access_token')
      const userId = userData.id
      
      // Query to get personalized recommendations based on the user's CV
      const recommendationQuery = `Analiza mi CV y dame recomendaciones específicas para mejorar mi perfil profesional. Incluye:
      - Habilidades técnicas que debería desarrollar
      - Certificaciones que me beneficiarían
      - Áreas de mejora en mi experiencia
      - Recursos de formación específicos
      - Oportunidades de crecimiento profesional
      Dame recomendaciones concretas y actionables basadas en mi perfil actual.`

      const searchRequest = {
        query: recommendationQuery,
        limit: 3,
        similarity_threshold: 0.2
      }

      const response = await fetch(`/api/rag/search/user/${userId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify(searchRequest)
      })

      if (!response.ok) {
        throw new Error(`Error ${response.status}: ${response.statusText}`)
      }

      const data = await response.json()
      
      if (data.results && data.results.length > 0) {
        // Process the RAG results to generate actionable recommendations
        const recommendations = generateRAGBasedRecommendations(data.results, profileData)
        setRagRecommendations(recommendations)
      } else {
        // If no documents found, show message to upload CV
        setRecommendationsError('Sube tu CV para recibir recomendaciones personalizadas basadas en tu perfil profesional.')
      }
      
    } catch (error) {
      console.error('Error loading RAG recommendations:', error)
      setRecommendationsError('No se pudieron cargar las recomendaciones personalizadas. Asegúrate de haber subido tu CV.')
    } finally {
      setLoadingRecommendations(false)
    }
  }

  const generateRAGBasedRecommendations = (ragResults, profile) => {
    const recommendations = []
    
    // Analyze the content from user's documents to generate specific recommendations
    const allContent = ragResults.map(result => 
      result.content_preview || result.content || ''
    ).join(' ').toLowerCase()
    
    const area = profile?.area_of_interest?.toLowerCase() || ''
    const level = profile?.experience_level?.toLowerCase() || ''
    
    // Technology skills analysis
    if (allContent.includes('javascript') || allContent.includes('react') || allContent.includes('node') || area.includes('fullstack') || area.includes('frontend')) {
      recommendations.push({
        type: 'skill_development',
        title: 'Especialízate en Tecnologías Modernas',
        description: 'Basado en tu perfil, te recomiendo profundizar en TypeScript, Next.js y arquitecturas de microservicios. Estas tecnologías están en alta demanda.',
        priority: 'high',
        category: 'Desarrollo Técnico',
        based_on: 'Análisis de tu experiencia en JavaScript/React'
      })
    }

    if (allContent.includes('python') || allContent.includes('django') || allContent.includes('fastapi')) {
      recommendations.push({
        type: 'certification',
        title: 'Certificaciones en Cloud y DevOps',
        description: 'Con tu background en Python, considera obtener certificaciones AWS Solutions Architect o Google Cloud Professional. Complementará tu stack backend.',
        priority: 'high',
        category: 'Certificaciones',
        based_on: 'Tu experiencia con Python detectada en tu CV'
      })
    }

    // Experience level analysis
    if (level === 'junior' || allContent.includes('prácticas') || allContent.includes('becario')) {
      recommendations.push({
        type: 'portfolio',
        title: 'Construye un Portfolio Impactante',
        description: 'Crea 3-4 proyectos que demuestren tu progresión técnica. Incluye un proyecto fullstack, una API REST y contribuciones open source.',
        priority: 'high',
        category: 'Desarrollo Profesional',
        based_on: 'Tu nivel de experiencia actual'
      })
    } else if (level === 'senior' || allContent.includes('líder') || allContent.includes('senior')) {
      recommendations.push({
        type: 'leadership',
        title: 'Desarrolla Habilidades de Liderazgo Técnico',
        description: 'Considera roles de mentoring, arquitectura de sistemas y gestión de equipos. Explora certificaciones en management y metodologías ágiles.',
        priority: 'medium',
        category: 'Liderazgo',
        based_on: 'Tu experiencia senior detectada'
      })
    }

    // General recommendations based on content analysis
    if (allContent.includes('inglés') || allContent.includes('english')) {
      recommendations.push({
        type: 'language',
        title: 'Potencia tu Inglés Técnico',
        description: 'Mejora tu inglés técnico con cursos específicos de IT. Practica presentaciones técnicas y participa en comunidades internacionales.',
        priority: 'medium',
        category: 'Habilidades Blandas',
        based_on: 'Conocimientos de inglés mencionados en tu perfil'
      })
    }

    // If no specific recommendations generated, provide general ones
    if (recommendations.length === 0) {
      recommendations.push({
        type: 'general',
        title: 'Optimiza tu Perfil Profesional',
        description: 'Basándome en tu CV, te recomiendo actualizar tu perfil en LinkedIn, crear un portafolio online y obtener certificaciones en tu área de especialización.',
        priority: 'medium',
        category: 'Desarrollo Profesional',
        based_on: 'Análisis general de tu CV'
      })
    }

    return recommendations.slice(0, 4) // Limit to 4 recommendations
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
      { name: 'Coursera', url: 'https://www.coursera.org', description: 'Cursos universitarios online' },
      { name: 'Udemy', url: 'https://www.udemy.com', description: 'Cursos prácticos' },
      { name: 'Platzi', url: 'https://platzi.com', description: 'Tecnología en español' },
      { name: 'freeCodeCamp', url: 'https://www.freecodecamp.org', description: 'Programación gratuita' }
    ]

    return area.includes('tech') || area.includes('desarrollo') || area.includes('programación') || area.includes('fullstack')
      ? { techResources, generalResources, courses }
      : { techResources: generalResources, generalResources: techResources, courses }
  }

  const { techResources, generalResources, courses } = getResourcesByArea()

  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-800 mb-6">Recursos de Empleabilidad y Formación</h2>

      {/* RAG-Generated Personalized Recommendations */}
      {ragRecommendations.length > 0 && (
        <div className="mb-8 bg-gradient-to-r from-purple-50 to-pink-50 border border-purple-200 rounded-xl p-6">
          <h3 className="text-xl font-semibold text-purple-800 mb-4 flex items-center">
            <svg className="w-6 h-6 text-purple-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
            </svg>
            🤖 Recomendaciones IA basadas en tu CV
          </h3>
          <p className="text-purple-700 text-sm mb-4">
            Nuestro asistente IA ha analizado tu CV y genera estas recomendaciones específicas para tu perfil:
          </p>
          
          <div className="space-y-4">
            {ragRecommendations.map((recommendation, index) => (
              <div key={index} className="bg-white rounded-lg p-4 border border-purple-200 hover:border-purple-300 transition-colors">
                <div className="flex items-start">
                  <div className="flex-shrink-0 mr-3">
                    {recommendation.priority === 'high' && (
                      <div className="w-3 h-3 bg-red-500 rounded-full mt-1"></div>
                    )}
                    {recommendation.priority === 'medium' && (
                      <div className="w-3 h-3 bg-yellow-500 rounded-full mt-1"></div>
                    )}
                    {recommendation.priority === 'low' && (
                      <div className="w-3 h-3 bg-green-500 rounded-full mt-1"></div>
                    )}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="font-semibold text-purple-800">
                        {recommendation.title}
                      </h4>
                      <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                        {recommendation.category}
                      </span>
                    </div>
                    <p className="text-gray-700 text-sm leading-relaxed mb-2">
                      {recommendation.description}
                    </p>
                    {recommendation.based_on && (
                      <p className="text-xs text-purple-600 italic">
                        💡 {recommendation.based_on}
                      </p>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
          
          <div className="mt-4 p-3 bg-purple-100 rounded-lg">
            <p className="text-xs text-purple-700 flex items-center">
              <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
              </svg>
              🔴 Alta prioridad | 🟡 Media prioridad | 🟢 Baja prioridad - Generado por análisis IA de tu CV
            </p>
          </div>
        </div>
      )}

      {/* Loading state for recommendations */}
      {loadingRecommendations && (
        <div className="mb-8 bg-gradient-to-r from-purple-50 to-pink-50 border border-purple-200 rounded-xl p-6">
          <div className="flex items-center">
            <svg className="w-5 h-5 animate-spin text-purple-600 mr-3" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="m4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <span className="text-purple-700">Generando recomendaciones personalizadas...</span>
          </div>
        </div>
      )}

      {/* Error state for recommendations */}
      {recommendationsError && (
        <div className="mb-8 bg-orange-50 border border-orange-200 rounded-xl p-6">
          <div className="flex items-center">
            <svg className="w-5 h-5 text-orange-600 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div className="flex-1">
              <h4 className="font-medium text-orange-800 mb-1">Recomendaciones personalizadas no disponibles</h4>
              <span className="text-orange-700 text-sm">{recommendationsError}</span>
              <p className="text-orange-600 text-xs mt-2">💡 Ve a la pestaña "Asistente" para subir tu CV y obtener recomendaciones basadas en IA.</p>
            </div>
          </div>
        </div>
      )}

      {/* Tech Platforms */}
      <div className="mb-8">
        <h3 className="text-xl font-semibold text-gray-800 mb-4 flex items-center">
          <svg className="w-6 h-6 text-orange-500 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
          </svg>
          Plataformas Laborales
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
          <svg className="w-6 h-6 text-blue-500 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
          </svg>
          Portales Generales de Empleo
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {generalResources.map((resource, index) => (
            <a
              key={index}
              href={resource.url}
              target="_blank"
              rel="noopener noreferrer"
              className="bg-white border-2 border-gray-200 rounded-lg p-4 hover:border-blue-400 hover:shadow-lg transition duration-200"
            >
              <div className="flex justify-between items-start">
                <div>
                  <h4 className="font-semibold text-gray-800">{resource.name}</h4>
                  <p className="text-sm text-gray-600 mt-1">{resource.description}</p>
                </div>
                <svg className="w-5 h-5 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                </svg>
              </div>
            </a>
          ))}
        </div>
      </div>

      {/* Learning Platforms */}
      <div className="mb-8">
        <h3 className="text-xl font-semibold text-gray-800 mb-4 flex items-center">
          <svg className="w-6 h-6 text-green-500 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
          </svg>
          Plataformas de Formación
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {courses.map((course, index) => (
            <a
              key={index}
              href={course.url}
              target="_blank"
              rel="noopener noreferrer"
              className="bg-white border-2 border-gray-200 rounded-lg p-4 hover:border-green-400 hover:shadow-lg transition duration-200"
            >
              <div className="flex justify-between items-start">
                <div>
                  <h4 className="font-semibold text-gray-800">{course.name}</h4>
                  <p className="text-sm text-gray-600 mt-1">{course.description}</p>
                </div>
                <svg className="w-5 h-5 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                </svg>
              </div>
            </a>
          ))}
        </div>
      </div>

      {/* Professional Tips */}
      <div className="bg-gradient-to-r from-indigo-50 to-purple-50 border border-indigo-200 rounded-xl p-6">
        <h3 className="text-xl font-semibold text-indigo-800 mb-4 flex items-center">
          <svg className="w-6 h-6 text-indigo-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
          Consejos para tu Búsqueda de Empleo
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-white rounded-lg p-4">
            <h4 className="font-semibold text-gray-800 mb-2">🎯 Optimiza tu CV</h4>
            <ul className="text-sm text-gray-600 space-y-1">
              <li>• Adapta tu CV a cada oferta</li>
              <li>• Usa palabras clave del sector</li>
              <li>• Destaca logros cuantificables</li>
              <li>• Mantén un formato limpio y profesional</li>
            </ul>
          </div>
          <div className="bg-white rounded-lg p-4">
            <h4 className="font-semibold text-gray-800 mb-2">🤝 Networking</h4>
            <ul className="text-sm text-gray-600 space-y-1">
              <li>• Participa en eventos del sector</li>
              <li>• Únete a comunidades profesionales</li>
              <li>• Mantén actualizado tu LinkedIn</li>
              <li>• Contribuye a proyectos open source</li>
            </ul>
          </div>
          <div className="bg-white rounded-lg p-4">
            <h4 className="font-semibold text-gray-800 mb-2">📚 Formación Continua</h4>
            <ul className="text-sm text-gray-600 space-y-1">
              <li>• Mantente al día con las tecnologías</li>
              <li>• Obtén certificaciones relevantes</li>
              <li>• Practica con proyectos personales</li>
              <li>• Aprende habilidades blandas</li>
            </ul>
          </div>
          <div className="bg-white rounded-lg p-4">
            <h4 className="font-semibold text-gray-800 mb-2">💼 Proceso de Selección</h4>
            <ul className="text-sm text-gray-600 space-y-1">
              <li>• Prepara tus entrevistas técnicas</li>
              <li>• Practica casos de uso reales</li>
              <li>• Investiga sobre la empresa</li>
              <li>• Prepara preguntas inteligentes</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ResourcesTab