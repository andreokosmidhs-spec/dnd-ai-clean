import axios from "axios";

const client = axios.create({
  baseURL: process.env.REACT_APP_BACKEND_URL || "",
});

// Inject JWT on every request if present
client.interceptors.request.use((config) => {
  const token = localStorage.getItem("dnd_auth_token");
  if (token) {
    config.headers = config.headers || {};
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// 402 = turn limit reached — emit a custom event so any component can respond
client.interceptors.response.use(
  (res) => res,
  (error) => {
    if (error.response?.status === 402) {
      window.dispatchEvent(new CustomEvent("dnd:turn_limit", {
        detail: error.response.data?.detail || {},
      }));
    }
    return Promise.reject(error);
  }
);

const handleRequest = async (promise) => {
  try {
    const response = await promise;
    return response.data;
  } catch (error) {
    const payload = error.response?.data || { message: error.message };
    return {
      success: false,
      data: null,
      error: payload,
      status: error.response?.status,
    };
  }
};

export const isSuccess = (response) => response?.success !== false && !response?.error;

export const getErrorMessage = (error) => {
  if (!error) return "Unknown error";
  if (typeof error === "string") return error;
  return error.message || "Unknown error";
};

const apiClient = {
  get: (url, config) => handleRequest(client.get(url, config)),
  post: (url, data, config) => handleRequest(client.post(url, data, config)),
  put: (url, data, config) => handleRequest(client.put(url, data, config)),
  patch: (url, data, config) => handleRequest(client.patch(url, data, config)),
  delete: (url, config) => handleRequest(client.delete(url, config)),
};

export default apiClient;
