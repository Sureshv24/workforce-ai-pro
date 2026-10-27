import { useState } from "react";
import {
  login,
  forgotPassword,
  resetPassword,
} from "../api/auth";

export default function Login({ onLogin }) {
  const initialToken = new URLSearchParams(window.location.search)
    .get("reset_token");

  const [mode, setMode] = useState(initialToken ? "reset" : "login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [resetToken] = useState(initialToken || "");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [debugResetUrl, setDebugResetUrl] = useState("");
  const [loading, setLoading] = useState(false);

  function changeMode(nextMode) {
    setError("");
    setSuccess("");
    setDebugResetUrl("");
    setMode(nextMode);
  }

  async function handleLogin(event) {
    event.preventDefault();
    setError("");
    setSuccess("");
    setLoading(true);

    try {
      const result = await login(email.trim(), password);
      onLogin(result.user);
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        err.message ||
        "Login failed. Please check your credentials."
      );
    } finally {
      setLoading(false);
    }
  }

  async function handleForgotPassword(event) {
    event.preventDefault();
    setError("");
    setSuccess("");
    setDebugResetUrl("");
    setLoading(true);

    try {
      const result = await forgotPassword(email.trim());
      setSuccess(result.message || "If your account exists, reset instructions will be sent.");
      if (result.debug_reset_url) {
        setDebugResetUrl(result.debug_reset_url);
      }
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        "Unable to submit the password reset request."
      );
    } finally {
      setLoading(false);
    }
  }

  async function handleResetPassword(event) {
    event.preventDefault();
    setError("");
    setSuccess("");

    if (password !== confirmPassword) {
      setError("The passwords do not match.");
      return;
    }

    if (!resetToken) {
      setError("The password reset link is missing its token. Request a new link.");
      return;
    }

    setLoading(true);
    try {
      const result = await resetPassword(resetToken, password);
      setSuccess(result.message || "Password reset successfully.");
      setPassword("");
      setConfirmPassword("");
      window.history.replaceState({}, "", window.location.pathname);
      setMode("login");
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        "Password reset failed. Request a new reset link and try again."
      );
    } finally {
      setLoading(false);
    }
  }

  const title = mode === "forgot"
    ? "Forgot password"
    : mode === "reset"
      ? "Set a new password"
      : "WorkForce AI Pro";

  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-100 p-4">
      <form
        onSubmit={
          mode === "forgot"
            ? handleForgotPassword
            : mode === "reset"
              ? handleResetPassword
              : handleLogin
        }
        className="w-full max-w-md space-y-5 rounded-2xl border bg-white p-8 shadow-sm"
      >
        <div>
          <h1 className="text-2xl font-bold text-slate-900">{title}</h1>
          <p className="mt-2 text-sm text-slate-500">
            {mode === "login"
              ? "Sign in to access workforce intelligence."
              : mode === "forgot"
                ? "Enter your account email to request a password reset."
                : "Choose a new password for your account."}
          </p>
        </div>

        {error && (
          <div role="alert" className="rounded-lg bg-red-50 p-3 text-sm text-red-700">
            {error}
          </div>
        )}

        {success && (
          <div role="status" className="rounded-lg bg-emerald-50 p-3 text-sm text-emerald-800">
            {success}
          </div>
        )}

        {mode !== "reset" && (
          <label className="block text-sm font-medium text-slate-700">
            Email
            <input
              type="email"
              required
              autoComplete="username"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="mt-2 w-full rounded-lg border p-3"
            />
          </label>
        )}

        {mode === "login" && (
          <label className="block text-sm font-medium text-slate-700">
            Password
            <input
              type="password"
              required
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="mt-2 w-full rounded-lg border p-3"
            />
          </label>
        )}

        {mode === "reset" && (
          <>
            <label className="block text-sm font-medium text-slate-700">
              New password
              <input
                type="password"
                required
                minLength={8}
                maxLength={128}
                autoComplete="new-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="mt-2 w-full rounded-lg border p-3"
              />
            </label>
            <label className="block text-sm font-medium text-slate-700">
              Confirm new password
              <input
                type="password"
                required
                minLength={8}
                maxLength={128}
                autoComplete="new-password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="mt-2 w-full rounded-lg border p-3"
              />
            </label>
          </>
        )}

        <button
          disabled={loading}
          type="submit"
          className="w-full rounded-lg bg-indigo-600 p-3 font-semibold text-white disabled:opacity-50"
        >
          {loading
            ? "Please wait..."
            : mode === "login"
              ? "Sign in"
              : mode === "forgot"
                ? "Request reset link"
                : "Reset password"}
        </button>

        {mode === "login" && (
          <button
            type="button"
            onClick={() => changeMode("forgot")}
            className="w-full text-sm font-medium text-indigo-600 hover:underline"
          >
            Forgot password?
          </button>
        )}

        {mode === "forgot" && debugResetUrl && (
          <a
            href={debugResetUrl}
            className="block break-all text-sm font-medium text-indigo-600 underline"
          >
            Open development password-reset link
          </a>
        )}

        {mode !== "login" && (
          <button
            type="button"
            onClick={() => {
              window.history.replaceState({}, "", window.location.pathname);
              changeMode("login");
            }}
            className="w-full text-sm font-medium text-slate-600 hover:underline"
          >
            Back to sign in
          </button>
        )}
      </form>
    </main>
  );
}
