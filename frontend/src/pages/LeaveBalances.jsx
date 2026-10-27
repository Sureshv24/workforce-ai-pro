import { useCallback, useEffect, useState } from "react";
import api from "../api/client";

const LEAVE_TYPES = ["Casual", "Sick", "Annual", "Unpaid"];
const currentYear = new Date().getFullYear();

const emptyForm = {
  employee_id: "",
  leave_type: "Casual",
  year: String(currentYear),
  total_days: "12",
};

export default function LeaveBalances({ currentUser }) {
  const role = String(currentUser?.role || "").toUpperCase();
  const canManage = role === "ADMIN" || role === "HR";

  const [balances, setBalances] = useState([]);
  const [year, setYear] = useState(String(currentYear));
  const [employeeId, setEmployeeId] = useState("");
  const [form, setForm] = useState(emptyForm);
  const [showForm, setShowForm] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const loadBalances = useCallback(async () => {
    setLoading(true);
    setError("");
    setMessage("");

    try {
      const params = { year: Number(year) };
      if (canManage && employeeId.trim()) {
        params.employee_id = Number(employeeId);
      }

      const response = await api.get("/leave-balances/", { params });
      setBalances(Array.isArray(response.data) ? response.data : []);
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "Unable to load leave balances. Please check your login and API connection."
      );
    } finally {
      setLoading(false);
    }
  }, [year, employeeId, canManage]);

  useEffect(() => {
    loadBalances();
  }, [loadBalances]);

  function updateForm(event) {
    const { name, value } = event.target;
    setForm((previous) => ({ ...previous, [name]: value }));
  }

  async function saveBalance(event) {
    event.preventDefault();
    setSaving(true);
    setError("");
    setMessage("");

    try {
      await api.post("/leave-balances/", {
        employee_id: Number(form.employee_id),
        leave_type: form.leave_type,
        year: Number(form.year),
        total_days: Number(form.total_days),
      });

      setMessage("Leave balance saved successfully.");
      setForm(emptyForm);
      setShowForm(false);
      await loadBalances();
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "Unable to save the leave balance. Please check the entered values."
      );
    } finally {
      setSaving(false);
    }
  }

  const totalAllocated = balances.reduce(
    (sum, item) => sum + Number(item.total_days || 0),
    0
  );
  const totalUsed = balances.reduce(
    (sum, item) => sum + Number(item.used_days || 0),
    0
  );
  const totalRemaining = balances.reduce(
    (sum, item) => sum + Number(item.remaining_days || 0),
    0
  );

  const inputClass =
    "w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100";

  return (
    <div className="space-y-6">
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Leave Balances</h1>
          <p className="mt-1 text-sm text-slate-500">
            Track allocated, used and remaining leave days.
          </p>
        </div>

        {canManage && (
          <button
            type="button"
            onClick={() => {
              setShowForm((value) => !value);
              setError("");
              setMessage("");
            }}
            className="rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-indigo-700"
          >
            {showForm ? "Cancel" : "+ Allocate Leave"}
          </button>
        )}
      </div>

      {error && (
        <div role="alert" className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
          {String(error)}
        </div>
      )}

      {message && (
        <div role="status" className="rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700">
          {message}
        </div>
      )}

      {showForm && canManage && (
        <form
          onSubmit={saveBalance}
          className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm"
        >
          <h2 className="mb-4 text-lg font-semibold text-slate-900">
            Allocate or Update Leave
          </h2>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <label className="space-y-1 text-sm font-medium text-slate-700">
              Employee ID
              <input
                className={inputClass}
                type="number"
                name="employee_id"
                min="1"
                required
                value={form.employee_id}
                onChange={updateForm}
                placeholder="Enter employee ID"
              />
            </label>

            <label className="space-y-1 text-sm font-medium text-slate-700">
              Leave Type
              <select
                className={inputClass}
                name="leave_type"
                value={form.leave_type}
                onChange={updateForm}
              >
                {LEAVE_TYPES.map((type) => (
                  <option key={type} value={type}>{type}</option>
                ))}
              </select>
            </label>

            <label className="space-y-1 text-sm font-medium text-slate-700">
              Year
              <input
                className={inputClass}
                type="number"
                name="year"
                min="2000"
                max="2100"
                required
                value={form.year}
                onChange={updateForm}
              />
            </label>

            <label className="space-y-1 text-sm font-medium text-slate-700">
              Total Days
              <input
                className={inputClass}
                type="number"
                name="total_days"
                min="0"
                step="0.5"
                required
                value={form.total_days}
                onChange={updateForm}
              />
            </label>
          </div>

          <button
            type="submit"
            disabled={saving}
            className="mt-5 rounded-lg bg-indigo-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {saving ? "Saving..." : "Save Leave Balance"}
          </button>
          <p className="mt-3 text-xs text-slate-500">
            If a balance already exists for this employee, leave type and year,
            the backend updates its total days.
          </p>
        </form>
      )}

      <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
        <label className="max-w-xs flex-1 space-y-1 text-sm font-medium text-slate-700">
          Leave Year
          <select
            className={inputClass}
            value={year}
            onChange={(event) => setYear(event.target.value)}
          >
            {[currentYear - 1, currentYear, currentYear + 1].map((item) => (
              <option key={item} value={item}>{item}</option>
            ))}
          </select>
        </label>

        {canManage && (
          <label className="max-w-xs flex-1 space-y-1 text-sm font-medium text-slate-700">
            Employee ID filter
            <input
              className={inputClass}
              type="number"
              min="1"
              value={employeeId}
              onChange={(event) => setEmployeeId(event.target.value)}
              placeholder="All employees"
            />
          </label>
        )}

        <button
          type="button"
          onClick={loadBalances}
          className="rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50"
        >
          Refresh
        </button>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        {[
          { label: "Total Allocated", value: totalAllocated, color: "text-indigo-600" },
          { label: "Days Used", value: totalUsed, color: "text-amber-600" },
          { label: "Days Remaining", value: totalRemaining, color: "text-emerald-600" },
        ].map((stat) => (
          <div key={stat.label} className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <p className="text-sm text-slate-500">{stat.label}</p>
            <p className={`mt-2 text-3xl font-bold ${stat.color}`}>
              {stat.value}
            </p>
          </div>
        ))}
      </div>

      <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
        <div className="flex items-center justify-between border-b border-slate-200 px-5 py-4">
          <h2 className="font-semibold text-slate-900">Employee Leave Summary</h2>
          <span className="text-sm text-slate-500">{balances.length} records</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full min-w-[720px] text-left text-sm">
            <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
              <tr>
                <th className="px-5 py-3">Employee ID</th>
                <th className="px-5 py-3">Leave Type</th>
                <th className="px-5 py-3">Year</th>
                <th className="px-5 py-3">Allocated</th>
                <th className="px-5 py-3">Used</th>
                <th className="px-5 py-3">Remaining</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loading ? (
                <tr>
                  <td colSpan="6" className="px-5 py-10 text-center text-slate-500">
                    Loading leave balances...
                  </td>
                </tr>
              ) : balances.length === 0 ? (
                <tr>
                  <td colSpan="6" className="px-5 py-10 text-center text-slate-500">
                    No leave balances found for {year}.
                  </td>
                </tr>
              ) : (
                balances.map((item) => (
                  <tr key={item.id} className="hover:bg-slate-50">
                    <td className="px-5 py-4 font-medium text-slate-800">
                      {item.employee_id}
                    </td>
                    <td className="px-5 py-4">
                      <span className="rounded-full bg-indigo-50 px-2.5 py-1 text-xs font-medium text-indigo-700">
                        {item.leave_type}
                      </span>
                    </td>
                    <td className="px-5 py-4 text-slate-600">{item.year}</td>
                    <td className="px-5 py-4 text-slate-700">{item.total_days}</td>
                    <td className="px-5 py-4 text-amber-700">{item.used_days}</td>
                    <td className="px-5 py-4 font-semibold text-emerald-700">
                      {item.remaining_days}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
