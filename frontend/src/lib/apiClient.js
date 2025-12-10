import axios from "axios";

const client = axios.create({
  baseURL: process.env.REACT_APP_BACKEND_URL || "",
});

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
