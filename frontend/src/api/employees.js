import api from "./client";

export const getEmployees = (params = {}) =>
  api.get("/employees/", { params });

export const createEmployee = (data) =>
  api.post("/employees/", data);

export const getEmployee = (id) =>
  api.get(`/employees/${id}`);

export const updateEmployee = (id, data) =>
  api.patch(`/employees/${id}`, data);

export const deleteEmployee = (id) =>
  api.delete(`/employees/${id}`);

export const linkEmployeeAccount = (id, data) =>
  api.put(`/employees/${id}/account`, data);
