import { useCallback, useEffect, useState } from "react";
import { CalendarDays, Check, X, RefreshCw } from "lucide-react";
import { getEmployees } from "../api/employees";
import {
  getLeaveRequests,
  createLeaveRequest,
  reviewLeaveRequest,
} from "../api/leaves";
import {
  getLeaveBalances,
  saveLeaveBalance,
} from "../api/leaveBalances";

const emptyForm = {
  employee_id: "",
  leave_type: "Casual",
  start_date: "",
  end_date: "",
  reason: "",
};

function errorMessage(error, fallback) {
  const detail = error.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return detail.map((item) => item.msg).join(", ");
  return error.message || fallback;
}

function dateLabel(value) {
  if (!value) return "—";
  return new Date(`${value.slice(0, 10)}T00:00:00`).toLocaleDateString();
}

export default function LeaveManagement({ currentUser }) {
  const isHR = ["ADMIN", "HR"].includes(
    String(currentUser?.role || "").toUpperCase()
  );

  const [requests, setRequests] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [form, setForm] = useState(emptyForm);
  const [filterStatus, setFilterStatus] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [reviewingId, setReviewingId] = useState(null);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [balances, setBalances] = useState([]);
  const [balanceForm, setBalanceForm] = useState({
    employee_id: "",
    leave_type: "Casual",
    year: new Date().getFullYear(),
    total_days: 12,
  });
  const [savingBalance, setSavingBalance] = useState(false);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const params = { page: 1, page_size: 100 };
      if (filterStatus) params.status = filterStatus;

      const requestsPromise = getLeaveRequests(params);
      const employeesPromise = isHR
        ? getEmployees({ page: 1, page_size: 100 })
        : Promise.resolve({ data: [] });

      const balancesPromise = getLeaveBalances(
        isHR ? undefined : undefined,
        new Date().getFullYear()
      );

      const [requestResponse, employeeResponse, balanceResponse] =
        await Promise.all([
          requestsPromise,
          employeesPromise,
          balancesPromise,
        ]);

      setBalances(
        Array.isArray(balanceResponse.data)
          ? balanceResponse.data
          : balanceResponse.data?.items || []
      );

      const requestData = requestResponse.data;
      setRequests(
        Array.isArray(requestData)
          ? requestData
          : requestData?.items || requestData?.results || []
      );

      const employeeData = employeeResponse.data;
      setEmployees(
        Array.isArray(employeeData)
          ? employeeData
          : employeeData?.items || employeeData?.results || []
      );
    } catch (err) {
      setError(
        errorMessage(
          err,
          "Unable to load leave requests. Check your login and API permissions."
        )
      );
    } finally {
      setLoading(false);
    }
  }, [filterStatus, isHR]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  async function submitRequest(event) {
    event.preventDefault();
    setError("");
    setNotice("");

    if (!isHR) {
      setError(
        "Employee self-service requires a verified employee-to-user account mapping."
      );
      return;
    }

    if (!form.employee_id) {
      setError("Please select an employee.");
      return;
    }

    if (form.end_date < form.start_date) {
      setError("End date cannot be before start date.");
      return;
    }

    setSaving(true);

    try {
      await createLeaveRequest({
        ...form,
        employee_id: Number(form.employee_id),
      });
      setForm(emptyForm);
      setNotice("Leave request submitted successfully.");
      await loadData();
    } catch (err) {
      setError(errorMessage(err, "Unable to submit leave request."));
    } finally {
      setSaving(false);
    }
  }

  async function reviewRequest(leaveId, status) {
    const action = status.toLowerCase();

    if (!window.confirm(`Are you sure you want to ${action} this request?`)) {
      return;
    }

    setError("");
    setNotice("");
    setReviewingId(leaveId);

    try {
      await reviewLeaveRequest(leaveId, {
        status,
        review_comment: null,
      });
      setNotice(`Leave request ${action}d successfully.`);
      await loadData();
    } catch (err) {
      const detail = err.response?.data?.detail;
      const message = errorMessage(
        err,
        "Unable to review leave request."
      );

      if (status === "Approved" && err.response?.status === 400) {
        setError(
          typeof detail === "string"
            ? `Cannot approve this leave request: ${detail}`
            : `Cannot approve this leave request: ${message}`
        );
      } else {
        setError(message);
      }
    } finally {
      setReviewingId(null);
    }
  }

  async function submitBalance(event) {
    event.preventDefault();
    setError("");
    setNotice("");

    if (!balanceForm.employee_id) {
      setError("Please select an employee for the leave balance.");
      return;
    }

    setSavingBalance(true);

    try {
      await saveLeaveBalance({
        employee_id: Number(balanceForm.employee_id),
        leave_type: balanceForm.leave_type,
        year: Number(balanceForm.year),
        total_days: Number(balanceForm.total_days),
      });

      setNotice("Leave balance saved successfully.");
      await loadData();
    } catch (err) {
      setError(errorMessage(err, "Unable to save leave balance."));
    } finally {
      setSavingBalance(false);
    }
  }

  const pendingCount = requests.filter((item) => item.status === "Pending").length;
  const approvedCount = requests.filter((item) => item.status === "Approved").length;
  const rejectedCount = requests.filter((item) => item.status === "Rejected").length;

  return (
    <section className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="mb-2 flex items-center gap-2 text-sm text-slate-500">
            <CalendarDays size={17} /> HR WORKSPACE
          </div>
          <h1 className="text-2xl font-semibold text-slate-900">
            Leave Management
          </h1>
          <p className="mt-1 text-sm text-slate-500">
            Submit, track, approve and reject employee leave requests.
          </p>
        </div>
        <button
          type="button"
          onClick={loadData}
          disabled={loading}
          className="inline-flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50"
        >
          <RefreshCw size={16} /> Refresh
        </button>
      </div>

      {error && (
        <div role="alert" className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
          {error}
        </div>
      )}
      {notice && (
        <div role="status" className="rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700">
          {notice}
        </div>
      )}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        {[
          { label: "Pending requests", value: pendingCount },
          { label: "Approved requests", value: approvedCount },
          { label: "Rejected requests", value: rejectedCount },
        ].map((item) => (
          <article key={item.label} className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <p className="text-sm text-slate-500">{item.label}</p>
            <p className="mt-2 text-3xl font-semibold text-slate-900">
              {item.value}
            </p>
          </article>
        ))}
      </div>

      <section className="space-y-4 rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <div>
          <h2 className="text-lg font-semibold text-slate-900">
            Leave balances
          </h2>
          <p className="mt-1 text-sm text-slate-500">
            Current-year allowances and approved leave usage.
          </p>
        </div>

        {isHR && (
          <form onSubmit={submitBalance} className="grid grid-cols-1 gap-3 md:grid-cols-5">
            <select
              required
              aria-label="Employee for leave balance"
              value={balanceForm.employee_id}
              onChange={(event) => setBalanceForm({
                ...balanceForm,
                employee_id: event.target.value,
              })}
              className="rounded-lg border border-slate-300 bg-white p-2.5 text-sm"
            >
              <option value="">Select employee</option>
              {employees.map((employee) => (
                <option key={employee.id} value={employee.id}>
                  {employee.full_name || employee.employee_code} — ID {employee.id}
                </option>
              ))}
            </select>

            <select
              aria-label="Balance leave type"
              value={balanceForm.leave_type}
              onChange={(event) => setBalanceForm({
                ...balanceForm,
                leave_type: event.target.value,
              })}
              className="rounded-lg border border-slate-300 bg-white p-2.5 text-sm"
            >
              {["Casual", "Sick", "Annual", "Unpaid"].map((type) => (
                <option key={type} value={type}>{type}</option>
              ))}
            </select>

            <input
              aria-label="Balance year"
              type="number"
              min="2000"
              max="2100"
              required
              value={balanceForm.year}
              onChange={(event) => setBalanceForm({
                ...balanceForm,
                year: event.target.value,
              })}
              className="rounded-lg border border-slate-300 p-2.5 text-sm"
            />

            <input
              aria-label="Total allocated leave days"
              type="number"
              min="0"
              max="365"
              required
              value={balanceForm.total_days}
              onChange={(event) => setBalanceForm({
                ...balanceForm,
                total_days: event.target.value,
              })}
              className="rounded-lg border border-slate-300 p-2.5 text-sm"
            />

            <button
              type="submit"
              disabled={savingBalance || employees.length === 0}
              className="rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
            >
              {savingBalance ? "Saving..." : "Save allowance"}
            </button>
          </form>
        )}

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {balances.map((balance) => (
            <article
              key={balance.id}
              className="rounded-xl border border-slate-200 bg-slate-50 p-4"
            >
              <p className="text-sm font-medium text-slate-600">
                {balance.leave_type} leave
              </p>
              <p className="mt-2 text-2xl font-semibold text-slate-900">
                {balance.remaining_days} days left
              </p>
              <div className="mt-3 space-y-1 text-sm text-slate-500">
                <p>Employee ID: {balance.employee_id}</p>
                <p>Allocated: {balance.total_days} days</p>
                <p>Used: {balance.used_days} days</p>
                <p>Year: {balance.year}</p>
              </div>
            </article>
          ))}
        </div>

        {!loading && balances.length === 0 && (
          <p className="text-sm text-slate-500">
            No leave balances configured for this year yet.
          </p>
        )}
      </section>

      {isHR ? (
        <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <h2 className="text-lg font-semibold text-slate-900">
            Submit a leave request
          </h2>
          <p className="mb-5 mt-1 text-sm text-slate-500">
            Select the employee and enter the requested leave details.
          </p>

          <form onSubmit={submitRequest} className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <label className="text-sm font-medium text-slate-700">
              Employee
              <select
                required
                value={form.employee_id}
                onChange={(event) =>
                  setForm({ ...form, employee_id: event.target.value })
                }
                className="mt-1 block w-full rounded-lg border border-slate-300 bg-white p-2.5 font-normal"
              >
                <option value="">Select employee</option>
                {employees.map((employee) => (
                  <option key={employee.id} value={employee.id}>
                    {employee.full_name || employee.employee_code} — ID {employee.id}
                  </option>
                ))}
              </select>
            </label>

            <label className="text-sm font-medium text-slate-700">
              Leave type
              <select
                value={form.leave_type}
                onChange={(event) =>
                  setForm({ ...form, leave_type: event.target.value })
                }
                className="mt-1 block w-full rounded-lg border border-slate-300 bg-white p-2.5 font-normal"
              >
                {["Casual", "Sick", "Annual", "Unpaid"].map((type) => (
                  <option key={type} value={type}>{type}</option>
                ))}
              </select>
            </label>

            <label className="text-sm font-medium text-slate-700">
              Start date
              <input
                required
                type="date"
                min={new Date().toLocaleDateString("en-CA")}
                value={form.start_date}
                onChange={(event) =>
                  setForm({ ...form, start_date: event.target.value })
                }
                className="mt-1 block w-full rounded-lg border border-slate-300 p-2.5 font-normal"
              />
            </label>

            <label className="text-sm font-medium text-slate-700">
              End date
              <input
                required
                type="date"
                min={form.start_date || new Date().toLocaleDateString("en-CA")}
                value={form.end_date}
                onChange={(event) =>
                  setForm({ ...form, end_date: event.target.value })
                }
                className="mt-1 block w-full rounded-lg border border-slate-300 p-2.5 font-normal"
              />
            </label>

            <label className="text-sm font-medium text-slate-700 md:col-span-2">
              Reason
              <textarea
                required
                minLength={3}
                maxLength={2000}
                rows={3}
                value={form.reason}
                onChange={(event) =>
                  setForm({ ...form, reason: event.target.value })
                }
                placeholder="Enter the reason for this leave request"
                className="mt-1 block w-full rounded-lg border border-slate-300 p-2.5 font-normal"
              />
            </label>

            <div className="md:col-span-2">
              <button
                type="submit"
                disabled={saving || employees.length === 0}
                className="rounded-lg bg-indigo-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {saving ? "Submitting..." : "Submit leave request"}
              </button>
              {employees.length === 0 && (
                <p className="mt-2 text-sm text-amber-700">
                  No employees loaded. Check employee API permissions.
                </p>
              )}
            </div>
          </form>
        </section>
      ) : (
        <div className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
          You can view your own requests if your employee account is linked.
          Employee self-service submission needs a verified employee mapping.
          Please contact HR if your requests cannot be loaded.
        </div>
      )}

      <section className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 p-5">
          <div>
            <h2 className="text-lg font-semibold text-slate-900">Leave requests</h2>
            <p className="mt-1 text-sm text-slate-500">
              {requests.length} request{requests.length === 1 ? "" : "s"} displayed
            </p>
          </div>
          <select
            aria-label="Filter leave requests by status"
            value={filterStatus}
            onChange={(event) => setFilterStatus(event.target.value)}
            className="rounded-lg border border-slate-300 bg-white p-2 text-sm"
          >
            <option value="">All statuses</option>
            <option value="Pending">Pending</option>
            <option value="Approved">Approved</option>
            <option value="Rejected">Rejected</option>
          </select>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full min-w-[850px] text-left text-sm">
            <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
              <tr>
                <th className="px-5 py-3">Employee ID</th>
                <th className="px-5 py-3">Leave type</th>
                <th className="px-5 py-3">Dates</th>
                <th className="px-5 py-3">Reason</th>
                <th className="px-5 py-3">Status</th>
                {isHR && <th className="px-5 py-3">Actions</th>}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {requests.map((item) => (
                <tr key={item.id} className="align-top hover:bg-slate-50">
                  <td className="px-5 py-4 font-medium text-slate-800">
                    #{item.employee_id}
                  </td>
                  <td className="px-5 py-4 text-slate-700">{item.leave_type}</td>
                  <td className="px-5 py-4 whitespace-nowrap text-slate-600">
                    {dateLabel(item.start_date)} – {dateLabel(item.end_date)}
                  </td>
                  <td className="max-w-xs whitespace-normal px-5 py-4 text-slate-600">
                    {item.reason}
                    {item.review_comment && (
                      <p className="mt-2 text-xs text-slate-500">
                        Review: {item.review_comment}
                      </p>
                    )}
                  </td>
                  <td className="px-5 py-4">
                    <span className={`inline-flex rounded-full px-2.5 py-1 text-xs font-medium ${
                      item.status === "Approved"
                        ? "bg-emerald-100 text-emerald-700"
                        : item.status === "Rejected"
                          ? "bg-red-100 text-red-700"
                          : "bg-amber-100 text-amber-800"
                    }`}>
                      {item.status}
                    </span>
                  </td>
                  {isHR && (
                    <td className="px-5 py-4">
                      {item.status === "Pending" ? (
                        <div className="flex gap-2">
                          <button
                            type="button"
                            title="Approve request"
                            aria-label={`Approve leave request ${item.id}`}
                            disabled={reviewingId === item.id}
                            onClick={() => reviewRequest(item.id, "Approved")}
                            className="rounded-md border border-emerald-200 p-2 text-emerald-700 hover:bg-emerald-50 disabled:opacity-50"
                          >
                            <Check size={16} />
                          </button>
                          <button
                            type="button"
                            title="Reject request"
                            aria-label={`Reject leave request ${item.id}`}
                            disabled={reviewingId === item.id}
                            onClick={() => reviewRequest(item.id, "Rejected")}
                            className="rounded-md border border-red-200 p-2 text-red-700 hover:bg-red-50 disabled:opacity-50"
                          >
                            <X size={16} />
                          </button>
                        </div>
                      ) : (
                        <span className="text-slate-400">Reviewed</span>
                      )}
                    </td>
                  )}
                </tr>
              ))}
              {!loading && requests.length === 0 && (
                <tr>
                  <td colSpan={isHR ? 6 : 5} className="px-5 py-10 text-center text-slate-500">
                    No leave requests found.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
        {loading && (
          <p className="p-5 text-sm text-slate-500">Loading leave requests...</p>
        )}
      </section>
    </section>
  );
}
