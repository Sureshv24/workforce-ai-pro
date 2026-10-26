import api from "./client";

export async function getHiringTrends() {
  const response = await api.get("/dashboard/hiring-trends");
  return response.data;
}
