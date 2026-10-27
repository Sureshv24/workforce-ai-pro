import api from "./client";

export async function login(email, password) {
  const response = await api.post("/auth/login", { email, password });
  const { access_token, token_type } = response.data;

  if (!access_token) {
    throw new Error("Login response did not contain an access token.");
  }

  localStorage.setItem("access_token", access_token);

  try {
    const userResponse = await api.get("/auth/me");
    localStorage.setItem("user", JSON.stringify(userResponse.data));

    return {
      token: access_token,
      tokenType: token_type,
      user: userResponse.data,
    };
  } catch (error) {
    localStorage.removeItem("access_token");
    localStorage.removeItem("user");
    throw error;
  }
}

export async function forgotPassword(email) {
  const response = await api.post("/auth/forgot-password", { email });
  return response.data;
}

export async function resetPassword(token, newPassword) {
  const response = await api.post("/auth/reset-password", {
    token,
    new_password: newPassword,
  });
  return response.data;
}

export function logout() {
  localStorage.removeItem("access_token");
  localStorage.removeItem("user");
}
