import { useState } from "react";
import { login } from "../api/auth";

export default function Login({ onLogin }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
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

  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-100 p-4">
      <form onSubmit={handleSubmit}
        className="w-full max-w-md space-y-5 rounded-2xl border bg-white p-8 shadow-sm">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">WorkForce AI Pro</h1>
          <p className="mt-2 text-sm text-slate-500">
            Sign in to access workforce intelligence.
          </p>
        </div>

        {error && (
          <div role="alert" className="rounded-lg bg-red-50 p-3 text-sm text-red-700">
            {error}
          </div>
        )}

        <label className="block text-sm font-medium">
          Email
          <input type="email" required autoComplete="username"
            value={email} onChange={(e) => setEmail(e.target.value)}
            className="mt-2 w-full rounded-lg border p-3" />
        </label>

        <label className="block text-sm font-medium">
          Password
          <input type="password" required autoComplete="current-password"
            value={password} onChange={(e) => setPassword(e.target.value)}
            className="mt-2 w-full rounded-lg border p-3" />
        </label>

        <button disabled={loading} type="submit"
          className="w-full rounded-lg bg-indigo-600 p-3 font-semibold text-white disabled:opacity-50">
          {loading ? "Signing in..." : "Sign in"}
        </button>
      </form>
    </main>
  );
}
