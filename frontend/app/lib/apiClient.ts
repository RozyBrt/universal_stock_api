let rawBaseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
if (rawBaseUrl && !rawBaseUrl.endsWith('/api/v1') && !rawBaseUrl.endsWith('/api/v1/')) {
  rawBaseUrl = rawBaseUrl.endsWith('/') ? `${rawBaseUrl}api/v1` : `${rawBaseUrl}/api/v1`;
}
const BASE_URL = rawBaseUrl;

// Helper to get token (only works on client-side)
const getToken = () => {
  if (typeof window !== 'undefined') {
    return localStorage.getItem('access_token');
  }
  return null;
};

export const apiClient = async (endpoint: string, options: RequestInit = {}) => {
  const token = getToken();
  
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string>),
  };

  // Automatically attach token if it exists
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  // Set default Content-Type to JSON if not specified and not FormData
  if (!(options.body instanceof FormData) && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json';
  }

  const response = await fetch(`${BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (response.status === 401) {
    // Token expired or invalid, handle logout
    if (typeof window !== 'undefined') {
      localStorage.removeItem('access_token');
      // Redirect to login only if not already on login
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }
  }

  return response;
};

// Typed response helpers
export const fetchJson = async <T>(endpoint: string, options?: RequestInit): Promise<T> => {
  const res = await apiClient(endpoint, options);
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    let errorMessage = 'An error occurred';
    
    if (errorData.error && errorData.error.message) {
      errorMessage = errorData.error.message;
    } else if (typeof errorData.detail === 'string') {
      errorMessage = errorData.detail;
    } else if (Array.isArray(errorData.detail)) {
      errorMessage = errorData.detail.map((e: any) => e.msg).join(', ');
    } else if (errorData.message) {
      errorMessage = errorData.message;
    }
    
    throw new Error(errorMessage);
  }
  if (res.status === 204) {
    return null as T;
  }
  
  return res.json();
};
