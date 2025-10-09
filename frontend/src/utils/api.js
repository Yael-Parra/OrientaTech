export function authFetch(path, options = {}) {
  const token = localStorage.getItem('access_token')
  const headers = options.headers ? { ...options.headers } : {}
  if (token) headers['Authorization'] = `Bearer ${token}`
  return fetch(path, { ...options, headers })
}
