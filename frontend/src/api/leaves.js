import api from "./client";

export const getLeaveRequests = (params = {}) =>
  api.get("/leaves/", { params });

export const createLeaveRequest = (data) =>
  api.post("/leaves/", data);

export const reviewLeaveRequest = (leaveId, data) =>
  api.patch(`/leaves/${leaveId}/review`, data);

export const getLeaveRequest = (leaveId) =>
  api.get(`/leaves/${leaveId}`);
