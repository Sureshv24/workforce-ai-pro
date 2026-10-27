import api from "./client";

export function getAttendance(params = {}) {
  return api.get("/attendance/", { params });
}

export function createAttendance(payload) {
  return api.post("/attendance/", payload);
}

export function updateAttendance(id, payload) {
  return api.patch(`/attendance/${id}`, payload);
}

export function deleteAttendance(id) {
  return api.delete(`/attendance/${id}`);
}

export function checkIn(employeeId) {
  return api.post(`/attendance/${employeeId}/check-in`);
}

export function checkOut(employeeId) {
  return api.post(`/attendance/${employeeId}/check-out`);
}

export function getDailyAttendanceSummary(attendance_date) {
  return api.get("/attendance/summary/daily", {
    params: { attendance_date },
  });
}
