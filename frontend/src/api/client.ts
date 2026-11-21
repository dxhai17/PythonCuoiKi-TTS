/**
 * Base HTTP API client with unified error normalization.
 */

const API_BASE = '/api';

export class ApiError extends Error {
  public status: number;
  public details?: any;

  constructor(status: number, message: string, details?: any) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.details = details;
  }
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let errorMsg = `HTTP Error ${res.status}`;
    let details: any = null;
    try {
      const data = await res.json();
      errorMsg = data.error || errorMsg;
      details = data.details || null;
    } catch {
      // Non-JSON response
    }
    throw new ApiError(res.status, errorMsg, details);
  }

  // Handle empty bodies (204 No Content, etc.)
  if (res.status === 204) {
    return {} as T;
  }

  return res.json() as Promise<T>;
}

export async function apiGet<T>(endpoint: string, params?: Record<string, string | number>): Promise<T> {
  const url = new URL(`${API_BASE}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`, window.location.origin);
  if (params) {
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null) {
        url.searchParams.append(k, String(v));
      }
    });
  }

  const res = await fetch(url.toString(), {
    headers: { 'Accept': 'application/json' },
  });
  return handleResponse<T>(res);
}

export async function apiPost<T>(endpoint: string, body?: any): Promise<T> {
  const res = await fetch(`${API_BASE}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
    body: body ? JSON.stringify(body) : undefined,
  });
  return handleResponse<T>(res);
}

export async function apiUpload<T>(endpoint: string, formData: FormData): Promise<T> {
  const res = await fetch(`${API_BASE}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`, {
    method: 'POST',
    headers: {
      'Accept': 'application/json',
    },
    body: formData,
  });
  return handleResponse<T>(res);
}
