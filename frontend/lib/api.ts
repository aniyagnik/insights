import { useAuthStore } from "@/store/authStore";  

const BACKEND_URL = "https://insights-0etk.onrender.com/api/v1";

export async function apiRequest(
  endpoint: string,
  options: RequestInit = {}
) {
  const accessToken = useAuthStore.getState().accessToken;

  const headers = {
    "Content-Type": "application/json",
    ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
    ...(options.headers || {}),
  };

  const response = await fetch(`${BACKEND_URL}${endpoint}`, {
    ...options,
    headers,
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