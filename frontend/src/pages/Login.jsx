import { useState } from "react";
import {
  login,
  forgotPassword,
  resetPassword,
} from "../api/auth";

export default function Login({ onLogin }) {
  const initialToken = new URLSearchParams(window.location.search).get("reset_token");

  const [mode, setMode] = useState(initialToken ? "reset" : "login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [resetToken] = useState(initialToken || "");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [debugResetUrl, setDebugResetUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  function changeMode(nextMode) {
    setError("");
    setSuccess("");
    setDebugResetUrl("");
    setPassword("");
    setConfirmPassword("");
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
      setSuccess(
        result.message ||
        "If your account exists, reset instructions will be sent."
      );

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

  const title =
    mode === "forgot"
      ? "Forgot password?"
      : mode === "reset"
        ? "Create new password"
        : "Sign in to WorkForce AI";

  const description =
    mode === "login"
      ? "Access your workforce intelligence dashboard."
      : mode === "forgot"
        ? "Enter your registered email to request a password reset."
        : "Create a new password to secure your account.";

  const submitHandler =
    mode === "forgot"
      ? handleForgotPassword
      : mode === "reset"
        ? handleResetPassword
        : handleLogin;

  const submitLabel = loading
    ? "Please wait..."
    : mode === "login"
      ? "Sign In"
      : mode === "forgot"
        ? "Send Reset Instructions"
        : "Reset Password";

  return (
    <main className="relative min-h-screen overflow-x-hidden bg-[#030817] text-white">
      <div className="pointer-events-none absolute -left-40 top-40 h-[500px] w-[500px] rounded-full bg-cyan-500/[0.09] blur-[130px]" />
      <div className="pointer-events-none absolute bottom-0 left-1/3 h-[450px] w-[450px] rounded-full bg-blue-700/[0.12] blur-[140px]" />
      <div className="pointer-events-none absolute -right-40 top-0 h-[450px] w-[450px] rounded-full bg-cyan-500/[0.06] blur-[130px]" />

      <div className="relative mx-auto grid min-h-screen w-full max-w-[1500px] items-center lg:grid-cols-2">

        {/* LEFT BRAND PANEL */}
        <section className="relative flex flex-col justify-center px-6 py-8 sm:px-10 lg:px-12 xl:px-16 2xl:px-20 lg:py-10">

          <div className="absolute left-0 top-0 h-px w-full bg-gradient-to-r from-transparent via-cyan-400/30 to-transparent lg:hidden" />

          <div className="mb-8 flex items-center gap-3 xl:mb-10">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-[#05CBE7] text-xl font-black text-[#03101C] shadow-lg shadow-cyan-500/20">
              W
            </div>

            <div>
              <h1 className="text-xl font-extrabold tracking-tight">
                WorkForce <span className="text-[#05CBE7]">AI Pro</span>
              </h1>
              <p className="mt-1 text-[10px] font-semibold uppercase tracking-[0.22em] text-slate-500">
                Workforce Intelligence
              </p>
            </div>
          </div>

          <div className="max-w-xl">
            <div className="mb-7 inline-flex items-center gap-2 rounded-full border border-cyan-400/20 bg-cyan-400/[0.06] px-4 py-2">
              <span className="h-2 w-2 rounded-full bg-[#05CBE7] shadow-[0_0_12px_#05CBE7]" />
              <span className="text-xs font-semibold tracking-wide text-cyan-300">
                PEOPLE INTELLIGENCE PLATFORM
              </span>
            </div>

            <h2 className="text-4xl font-extrabold leading-[1.12] tracking-tight sm:text-[42px] xl:text-[48px] 2xl:text-[54px]">
              Your people.
              <span className="mt-2 block text-[#05CBE7]">
                Your insights.
              </span>
              <span className="mt-2 block text-white">
                One intelligent workspace.
              </span>
            </h2>

            <p className="mt-5 max-w-lg text-sm leading-7 text-slate-400 sm:text-base">
              Discover workforce trends, understand employee attrition risks,
              and transform people data into confident HR decisions.
            </p>
          </div>
        </section>

        {/* RIGHT LOGIN PANEL */}
        <section className="flex items-center justify-center px-5 py-8 sm:px-10 lg:px-10 xl:px-14">
          <div className="w-full max-w-[440px] rounded-[24px] border border-slate-800 bg-[#0D172A] p-6 shadow-2xl shadow-black/30 sm:p-7 xl:p-8">

            <div className="mb-6">
              <p className="text-xs font-bold uppercase tracking-[0.2em] text-[#05CBE7]">
                {mode === "login" ? "WELCOME BACK" : mode === "forgot" ? "ACCOUNT RECOVERY" : "PASSWORD SECURITY"}
              </p>
              <h2 className="mt-4 text-3xl font-extrabold tracking-tight text-white">
                {title}
              </h2>
              <p className="mt-3 text-sm leading-6 text-slate-400">
                {description}
              </p>
            </div>

            {error && (
              <div role="alert" className="mb-5 rounded-xl border border-red-500/20 bg-red-500/10 p-3 text-sm leading-5 text-red-300">
                {error}
              </div>
            )}

            {success && (
              <div role="status" className="mb-5 rounded-xl border border-emerald-500/20 bg-emerald-500/10 p-3 text-sm leading-5 text-emerald-300">
                {success}
              </div>
            )}

            <form
              onSubmit={
                mode === "forgot"
                  ? handleForgotPassword
                  : mode === "reset"
                    ? handleResetPassword
                    : handleLogin
              }
              className="space-y-4"
            >
              {mode !== "reset" && (
                <label className="block">
                  <span className="mb-2 block text-sm font-semibold text-slate-200">
                    Work email
                  </span>
                  <div className="relative">
                    <svg className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7">
                      <rect x="3" y="5" width="18" height="14" rx="3" />
                      <path d="m4 7 8 6 8-6" />
                    </svg>
                    <input
                      type="email"
                      required
                      autoComplete="username"
                      placeholder="Enter your work email"
                      value={email}
                      onChange={(event) => setEmail(event.target.value)}
                      className="w-full rounded-xl border border-slate-700 bg-[#030918] py-3.5 pl-12 pr-4 text-sm text-white outline-none transition placeholder:text-slate-600 hover:border-slate-600 focus:border-[#05CBE7] focus:ring-4 focus:ring-cyan-400/10"
                    />
                  </div>
                </label>
              )}

              {(mode === "login" || mode === "reset") && (
                <label className="block">
                  <span className="mb-2 block text-sm font-semibold text-slate-200">
                    {mode === "reset" ? "New password" : "Password"}
                  </span>
                  <div className="relative">
                    <svg className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7">
                      <rect x="4" y="10" width="16" height="11" rx="3" />
                      <path d="M8 10V7a4 4 0 0 1 8 0v3" />
                    </svg>
                    <input
                      type={showPassword ? "text" : "password"}
                      required
                      minLength={mode === "reset" ? 8 : undefined}
                      maxLength={mode === "reset" ? 128 : undefined}
                      autoComplete={mode === "reset" ? "new-password" : "current-password"}
                      placeholder={mode === "reset" ? "Create a new password" : "Enter your password"}
                      value={password}
                      onChange={(event) => setPassword(event.target.value)}
                      className="w-full rounded-xl border border-slate-700 bg-[#030918] py-3.5 pl-12 pr-12 text-sm text-white outline-none transition placeholder:text-slate-600 hover:border-slate-600 focus:border-[#05CBE7] focus:ring-4 focus:ring-cyan-400/10"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword((value) => !value)}
                      aria-label={showPassword ? "Hide password" : "Show password"}
                      className="absolute right-3 top-1/2 -translate-y-1/2 rounded-lg p-2 text-slate-500 hover:text-[#05CBE7]"
                    >
                      {showPassword ? (
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7">
                          <path d="m3 3 18 18M10.6 10.6a2 2 0 0 0 2.8 2.8" />
                          <path d="M9.9 5.2A10.8 10.8 0 0 1 12 5c6.5 0 10 7 10 7a16 16 0 0 1-3 3.8M6.2 6.2C3.5 8 2 12 2 12s3.5 7 10 7a10 10 0 0 0 3.2-.5" />
                        </svg>
                      ) : (
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7">
                          <path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12Z" />
                          <circle cx="12" cy="12" r="3" />
                        </svg>
                      )}
                    </button>
                  </div>
                </label>
              )}

              {mode === "reset" && (
                <label className="block">
                  <span className="mb-2 block text-sm font-semibold text-slate-200">
                    Confirm new password
                  </span>
                  <div className="relative">
                    <input
                      type={showConfirmPassword ? "text" : "password"}
                      required
                      minLength={8}
                      maxLength={128}
                      autoComplete="new-password"
                      placeholder="Enter password again"
                      value={confirmPassword}
                      onChange={(event) => setConfirmPassword(event.target.value)}
                      className="w-full rounded-xl border border-slate-700 bg-[#030918] px-4 py-3.5 pr-12 text-sm text-white outline-none transition placeholder:text-slate-600 focus:border-[#05CBE7] focus:ring-4 focus:ring-cyan-400/10"
                    />
                    <button
                      type="button"
                      onClick={() => setShowConfirmPassword((value) => !value)}
                      aria-label={showConfirmPassword ? "Hide confirmation password" : "Show confirmation password"}
                      className="absolute right-3 top-1/2 -translate-y-1/2 rounded-lg p-2 text-slate-500 hover:text-[#05CBE7]"
                    >
                      {showConfirmPassword ? "Hide" : "Show"}
                    </button>
                  </div>
                </label>
              )}

              {mode === "login" && (
                <div className="flex justify-end">
                  <button
                    type="button"
                    onClick={() => changeMode("forgot")}
                    className="text-sm font-semibold text-[#05CBE7] transition hover:text-cyan-200"
                  >
                    Forgot password?
                  </button>
                </div>
              )}

              <button
                disabled={loading}
                type="submit"
                className="flex w-full items-center justify-center gap-2 rounded-xl bg-[#05CBE7] px-5 py-3.5 text-sm font-bold text-[#03101C] shadow-lg shadow-cyan-500/10 transition hover:bg-cyan-300 focus:outline-none focus:ring-4 focus:ring-cyan-400/20 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {submitLabel}
                {!loading && (
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M5 12h14M13 6l6 6-6 6" />
                  </svg>
                )}
              </button>

              {mode === "forgot" && debugResetUrl && (
                <a
                  href={debugResetUrl}
                  className="block break-all rounded-xl border border-amber-500/20 bg-amber-500/10 p-3 text-sm text-amber-300 underline"
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
                  className="w-full py-2 text-sm font-semibold text-slate-400 transition hover:text-[#05CBE7]"
                >
                  ← Back to sign in
                </button>
              )}
            </form>

            <div className="mt-6 border-t border-slate-800 pt-4">
              <div className="flex items-center justify-center gap-2 text-xs text-slate-500">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#05CBE7" strokeWidth="1.7">
                  <path d="M12 22s8-4 8-11V5l-8-3-8 3v6c0 7 8 11 8 11Z" />
                  <path d="m9 12 2 2 4-4" />
                </svg>
                Protected authentication · WorkForce AI Pro
              </div>
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}
