const BACKEND_URL = "http://127.0.0.1:8000/api/v1";

export async function apiRequest(
  endpoint: string,
  options: RequestInit = {}
) {
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };

  const response = await fetch(`${BACKEND_URL}${endpoint}`, {
    ...options,
    headers,
    // Crucial for HTTP-only cookie sharing (transmitting refresh tokens securely)
    credentials: "include", 
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || "An error occurred");
  }

  if (response.status === 204) {
    return null;
  }

  return response.json();
}