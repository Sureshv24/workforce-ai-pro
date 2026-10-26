import api from "./client";

export const getPredictionHistory = (params = {}) =>
  api.get("/predictions/history", { params });
