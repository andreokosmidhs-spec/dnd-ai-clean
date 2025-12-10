import axios from "axios";

const fallbackBase =
  process.env.REACT_APP_BACKEND_URL ||
  (typeof window !== "undefined" ? `${window.location.origin}` : "");

const instance = axios.create({
  baseURL: fallbackBase,
  withCredentials: false,
});

export default instance;
