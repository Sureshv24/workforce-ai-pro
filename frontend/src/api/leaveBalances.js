
import api from "./client";

export const getLeaveBalances = (
  employeeId,
  year = new Date().getFullYear()
) => {
  if (employeeId) {
    return api.get(`/leave-balances/${employeeId}`, {
      params: { year },
    });
  }

  return api.get("/leave-balances/", {
    params: { year },
  });
};

export const saveLeaveBalance = (data) => {
  return api.post("/leave-balances/", data);
};
