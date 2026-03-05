import axios from "axios";

const API_BASE = "http://localhost:8000";

const api = axios.create({ baseURL: API_BASE });

export const getSessions = () => api.get("/sessions").then((r) => r.data);
export const getSession = (id) => api.get(`/sessions/${id}`).then((r) => r.data);
export const createSession = (payload) => api.post("/sessions", payload).then((r) => r.data);
export const updateSession = (id, payload) => api.patch(`/sessions/${id}`, payload).then((r) => r.data);
export const deleteSession = (id) => api.delete(`/sessions/${id}`);

export const createToolCall = (payload) => api.post("/tool-calls", payload).then((r) => r.data);
export const updateToolCall = (id, payload) => api.patch(`/tool-calls/${id}`, payload).then((r) => r.data);

export const getStats = () => api.get("/stats").then((r) => r.data);
