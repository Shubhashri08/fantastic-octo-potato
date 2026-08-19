// Centralized API Client with strict timeout and error management
const DEFAULT_TIMEOUT_MS = 12000;
const IMAGE_TIMEOUT_MS = 30000;

export class ApiError extends Error {
  constructor(message, status = 500, data = null) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
  }
}

export async function request(endpoint, options = {}, timeoutMs = DEFAULT_TIMEOUT_MS) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  const config = {
    ...options,
    signal: controller.signal,
    headers: {
      ...(options.headers || {})
    }
  };

  const startTime = performance.now();

  try {
    const response = await fetch(endpoint, config);
    clearTimeout(timeoutId);

    const elapsed = Math.round(performance.now() - startTime);

    if (!response.ok) {
      let errorData = null;
      try {
        errorData = await response.json();
      } catch {
        // Response wasn't json
      }
      const message = errorData?.detail || errorData?.message || `HTTP ${response.status}: Request failed`;
      console.error(`[API Error] ${endpoint} (${elapsed}ms) - ${message}`);
      throw new ApiError(message, response.status, errorData);
    }

    const data = await response.json();
    return data;
  } catch (err) {
    clearTimeout(timeoutId);
    const elapsed = Math.round(performance.now() - startTime);
    if (err.name === 'AbortError') {
      console.error(`[API Timeout] ${endpoint} timed out after ${timeoutMs}ms`);
      throw new ApiError('Request timed out. Please verify backend service.', 408);
    }
    if (err instanceof ApiError) {
      throw err;
    }
    console.error(`[API Network Error] ${endpoint} (${elapsed}ms):`, err.message);
    throw new ApiError(err.message || 'Network connection failed', 0);
  }
}

export async function uploadRequest(endpoint, formData, timeoutMs = IMAGE_TIMEOUT_MS) {
  return request(endpoint, {
    method: 'POST',
    body: formData
  }, timeoutMs);
}
