import { useState } from 'react'
import { Link } from 'react-router-dom'

const Login = () => {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    remember: false
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const formatErrorForDisplay = (err) => {
    if (!err) return ''
    if (typeof err === 'string') return err
    if (Array.isArray(err)) {
      return err.map(e => (e.msg ? e.msg : JSON.stringify(e))).join('; ')
    }
    if (typeof err === 'object') {
      if (err.detail) return formatErrorForDisplay(err.detail)
      if (err.message) return String(err.message)
      return JSON.stringify(err)
    }
    return String(err)
  }

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }))
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    ;(async () => {
      try {
        setError(null)
        setLoading(true)
        const res = await fetch('/auth/login', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ email: formData.email, password: formData.password })
        })

        const data = await res.json().catch(() => ({}))
        if (!res.ok) {
          const detailRaw = data.detail || data.message || data || 'Error'
          setError(formatErrorForDisplay(detailRaw))
          setLoading(false)
          return
        }

        // store token
        localStorage.setItem('access_token', data.access_token)
        localStorage.setItem('token_type', data.token_type || 'bearer')

        // verify /auth/me works with token
        const meRes = await fetch('/auth/me', {
          headers: {
            Authorization: `Bearer ${data.access_token}`
          }
        })
        if (meRes.ok) {
          const me = await meRes.json()
          console.log('Authenticated user:', me)
          // redirect to dashboard after successful login
          window.location.href = '/dashboard'
        } else {
          // still consider login successful but warn
          setError('Login correcto pero no se pudo validar el usuario.')
        }
      } catch (err) {
        console.error(err)
        setError(err.message || 'Error de conexión')
      } finally {
        setLoading(false)
      }
    })()
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-500 via-orange-300 to-white flex items-center justify-center p-4 relative overflow-hidden">
      {/* Banner geométrico superior derecho */}
      <img 
        src="/img/Banner-geometrico-1.png" 
        alt=""
        className="absolute top-0 right-0 w-64 h-64 opacity-20 z-0"
      />
      {/* Banner geométrico inferior izquierdo */}
      <img 
        src="/img/Banner-geometrico-2.png" 
        alt=""
        className="absolute bottom-0 left-0 w-64 h-64 opacity-20 z-0"
      />
      
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md p-8 relative z-10">
        {/* Logo y Header */}
        <div className="text-center mb-8">
          <div className="w-20 h-20 mx-auto mb-4 p-2 bg-white rounded-2xl shadow-lg">
            <img 
              src="/img/logo-factoria-f5.png" 
              alt="Factoría F5 Logo"
              className="w-full h-full object-contain"
            />
          </div>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-orange-500 to-orange-300 bg-clip-text text-transparent">
            OrientaTech
          </h1>
          <p className="text-gray-600 mt-2">Tu futuro digital comienza aquí</p>
        </div>

  {/* Formulario */}
  <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-gray-700 font-semibold mb-2">
              Email
            </label>
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
            <label className="block text-gray-700 font-semibold mb-2">
              Contraseña
            </label>
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

          <div className="flex items-center justify-between">
            <label className="flex items-center">
              <input
                type="checkbox"
                name="remember"
                checked={formData.remember}
                onChange={handleChange}
                className="mr-2 h-4 w-4 text-orange-500 focus:ring-orange-500 border-gray-300 rounded"
              />
              <span className="text-gray-600">Recordarme</span>
            </label>
            <a href="#" className="text-orange-500 hover:text-orange-600 font-medium">
              ¿Olvidaste tu contraseña?
            </a>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-gradient-to-r from-orange-500 to-orange-300 text-white py-3 rounded-lg font-semibold hover:from-orange-600 hover:to-orange-400 transform hover:scale-105 transition duration-200 shadow-lg disabled:opacity-60"
          >
            {loading ? 'Conectando...' : 'Iniciar Sesión'}
          </button>
          {error && <p className="text-sm text-red-600 mt-2">{error}</p>}
        </form>

        {/* Divider */}
        <div className="my-6 flex items-center">
          <div className="border-t border-gray-300 flex-1"></div>
          <span className="px-4 text-gray-500 text-sm">o</span>
          <div className="border-t border-gray-300 flex-1"></div>
        </div>

        {/* Registro */}
        <div className="text-center">
          <p className="text-gray-600 mb-4">¿Primera vez en OrientaTech?</p>
          <Link
            to="/registro"
            className="w-full block bg-white border-2 border-orange-500 text-orange-500 py-3 rounded-lg font-semibold hover:bg-orange-50 transition duration-200"
          >
            Crear mi cuenta
          </Link>
        </div>

        {/* Footer */}
        <div className="mt-8 text-center">
          <p className="text-xs text-gray-500">
            Transformamos talento, creamos oportunidades
          </p>
          <div className="flex items-center justify-center mt-2">
            <span className="text-xs font-bold text-orange-500">FACTORÍA F5 </span>
            <span className="text-xs text-gray-400 ml-1">- Impulsando el talento digital</span>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Login