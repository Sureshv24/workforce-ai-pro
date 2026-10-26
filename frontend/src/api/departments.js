import api from "./client";

export const getDepartments = (params = {}) =>
  api.get("/departments/", { params });

export const createDepartment = (data) =>
  api.post("/departments/", data);

export const getDepartment = (id) =>
  api.get(`/departments/${id}`);

export const updateDepartment = (id, data) =>
  api.patch(`/departments/${id}`, data);

export const deleteDepartment = (id) =>
  api.delete(`/departments/${id}`);
