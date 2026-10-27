import { useCallback, useEffect, useState } from "react";
import { getEmployees } from "../api/employees";
import {
  getAttendance,
  createAttendance,
  updateAttendance,
  deleteAttendance,
  checkIn,
  checkOut,
  getDailyAttendanceSummary,
} from "../api/attendance";

const today = () => {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-${String(now.getDate()).padStart(2, "0")}`;
};

const emptyForm = {
  employee_id: "",
  attendance_date: today(),
  check_in: "",
  check_out: "",
  status: "Present",
  remarks: "",
};

function toLocalInput(value) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  const local = new Date(date.getTime() - date.getTimezoneOffset() * 60000);
  return local.toISOString().slice(0, 16);
}

function errorMessage(error, fallback) {
  const detail = error.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return detail.map((item) => item.msg).join(", ");
  return fallback;
}

export default function Attendance() {
  const [records, setRecords] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [summary, setSummary] = useState(null);
  const [form, setForm] = useState(emptyForm);
  const [editingId, setEditingId] = useState(null);
  const [filterDate, setFilterDate] = useState(today());
  const [filterStatus, setFilterStatus] = useState("");
  const [filterEmployee, setFilterEmployee] = useState("");
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const loadData = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const params = { page: 1, page_size: 100 };
      if (filterDate) params.attendance_date = filterDate;
      if (filterStatus) params.status = filterStatus;
      if (filterEmployee) params.employee_id = Number(filterEmployee);

      const [attendanceResponse, employeeResponse, summaryResponse] =
        await Promise.all([
          getAttendance(params),
          getEmployees({ page: 1, page_size: 100 }),
          getDailyAttendanceSummary(filterDate || today()),
        ]);

      setRecords(Array.isArray(attendanceResponse.data) ? attendanceResponse.data : []);
      setEmployees(
        Array.isArray(employeeResponse.data)
          ? employeeResponse.data
          : employeeResponse.data?.items || employeeResponse.data?.results || []
      );
      setSummary(summaryResponse.data);
    } catch (err) {
      setError(errorMessage(
        err,
        "Unable to load attendance. Check your login, HR/Admin permissions, and backend."
      ));
    } finally {
      setLoading(false);
    }
  }, [filterDate, filterStatus, filterEmployee]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  function changeForm(event) {
    setForm((current) => ({
      ...current,
      [event.target.name]: event.target.value,
    }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setSaving(true);
    setError("");
    setNotice("");

    const payload = {
      employee_id: Number(form.employee_id),
      attendance_date: form.attendance_date,
      check_in: form.check_in ? new Date(form.check_in).toISOString() : null,
      check_out: form.check_out ? new Date(form.check_out).toISOString() : null,
      status: form.status,
      remarks: form.remarks.trim() || null,
    };

    try {
      if (editingId !== null) {
        delete payload.employee_id;
        await updateAttendance(editingId, payload);
        setNotice("Attendance record updated successfully.");
      } else {
        await createAttendance(payload);
        setNotice("Attendance record created successfully.");
      }

      setForm({ ...emptyForm, attendance_date: filterDate || today() });
      setEditingId(null);
      await loadData();
    } catch (err) {
      setError(errorMessage(err, "Unable to save attendance record."));
    } finally {
      setSaving(false);
    }
  }

  function startEdit(record) {
    setEditingId(record.id);
    setForm({
      employee_id: String(record.employee_id),
      attendance_date: record.attendance_date,
      check_in: toLocalInput(record.check_in),
      check_out: toLocalInput(record.check_out),
      status: record.status,
      remarks: record.remarks || "",
    });
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  async function handleDelete(record) {
    if (!window.confirm(`Delete attendance record #${record.id}?`)) return;
    setError("");
    setNotice("");

    try {
      await deleteAttendance(record.id);
      setNotice("Attendance record deleted.");
      await loadData();
    } catch (err) {
      setError(errorMessage(err, "Unable to delete attendance."));
    }
  }

  async function handlePunch(employeeId, action) {
    setError("");
    setNotice("");

    try {
      if (action === "in") {
        await checkIn(employeeId);
        setNotice(`Check-in recorded for employee #${employeeId}.`);
      } else {
        await checkOut(employeeId);
        setNotice(`Check-out recorded for employee #${employeeId}.`);
      }
      await loadData();
    } catch (err) {
      setError(errorMessage(err, `Unable to check ${action === "in" ? "in" : "out"}.`));
    }
  }

  const summaryCards = [
    { label: "Total records", value: summary?.total_records ?? "—" },
    { label: "Present", value: summary?.counts?.Present ?? 0 },
    { label: "Absent", value: summary?.counts?.Absent ?? 0 },
    { label: "Late", value: summary?.counts?.Late ?? 0 },
    { label: "On leave", value: summary?.counts?.["On Leave"] ?? 0 },
  ];

  return (
    <section className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Attendance Management</h1>
          <p className="mt-1 text-sm text-slate-500">
            Manage daily attendance using live workforce records.
          </p>
        </div>
        <button onClick={loadData} className="rounded-lg border bg-white px-4 py-2">
          Refresh
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

      <div className="grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-5">
        {summaryCards.map((item) => (
          <article key={item.label} className="rounded-xl border bg-white p-4">
            <p className="text-sm text-slate-500">{item.label}</p>
            <p className="mt-2 text-2xl font-bold text-slate-900">{item.value}</p>
          </article>
        ))}
      </div>

      <form onSubmit={handleSubmit} className="grid gap-4 rounded-xl border bg-white p-5 md:grid-cols-2 xl:grid-cols-3">
        <h2 className="text-lg font-semibold md:col-span-2 xl:col-span-3">
          {editingId !== null ? "Edit attendance" : "Add attendance"}
        </h2>

        <label className="grid gap-1 text-sm font-medium text-slate-700">
          Employee
          <select
            name="employee_id"
            required
            disabled={editingId !== null}
            value={form.employee_id}
            onChange={changeForm}
            className="rounded-lg border bg-white p-3"
          >
            <option value="">Select employee</option>
            {employees.map((employee) => (
              <option key={employee.id} value={employee.id}>
                {employee.full_name || employee.employee_code} (#{employee.id})
              </option>
            ))}
          </select>
        </label>

        <label className="grid gap-1 text-sm font-medium text-slate-700">
          Attendance date
          <input type="date" name="attendance_date" required value={form.attendance_date}
            onChange={changeForm} className="rounded-lg border p-3" />
        </label>

        <label className="grid gap-1 text-sm font-medium text-slate-700">
          Check-in
          <input type="datetime-local" name="check_in" value={form.check_in}
            onChange={changeForm} className="rounded-lg border p-3" />
        </label>

        <label className="grid gap-1 text-sm font-medium text-slate-700">
          Check-out
          <input type="datetime-local" name="check_out" value={form.check_out}
            onChange={changeForm} className="rounded-lg border p-3" />
        </label>

        <label className="grid gap-1 text-sm font-medium text-slate-700">
          Status
          <select name="status" value={form.status} onChange={changeForm}
            className="rounded-lg border bg-white p-3">
            <option>Present</option>
            <option>Absent</option>
            <option>Late</option>
            <option>On Leave</option>
          </select>
        </label>

        <label className="grid gap-1 text-sm font-medium text-slate-700">
          Remarks
          <input name="remarks" maxLength={500} value={form.remarks}
            onChange={changeForm} placeholder="Optional remarks"
            className="rounded-lg border p-3" />
        </label>

        <div className="flex flex-wrap gap-2 md:col-span-2 xl:col-span-3">
          <button disabled={saving} type="submit"
            className="rounded-lg bg-indigo-600 px-5 py-2.5 font-medium text-white disabled:opacity-50">
            {saving ? "Saving..." : editingId !== null ? "Save changes" : "Add attendance"}
          </button>
          {editingId !== null && (
            <button type="button"
              onClick={() => { setEditingId(null); setForm(emptyForm); }}
              className="rounded-lg border px-5 py-2.5">
              Cancel edit
            </button>
          )}
        </div>
      </form>

      <div className="grid gap-3 rounded-xl border bg-white p-4 md:grid-cols-3">
        <label className="grid gap-1 text-sm text-slate-600">
          Filter by date
          <input type="date" value={filterDate}
            onChange={(e) => setFilterDate(e.target.value)}
            className="rounded-lg border p-3" />
        </label>
        <label className="grid gap-1 text-sm text-slate-600">
          Filter by status
          <select value={filterStatus} onChange={(e) => setFilterStatus(e.target.value)}
            className="rounded-lg border bg-white p-3">
            <option value="">All statuses</option>
            <option>Present</option>
            <option>Absent</option>
            <option>Late</option>
            <option>On Leave</option>
          </select>
        </label>
        <label className="grid gap-1 text-sm text-slate-600">
          Filter by employee
          <select value={filterEmployee} onChange={(e) => setFilterEmployee(e.target.value)}
            className="rounded-lg border bg-white p-3">
            <option value="">All employees</option>
            {employees.map((employee) => (
              <option key={employee.id} value={employee.id}>
                {employee.full_name || employee.employee_code}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className="overflow-x-auto rounded-xl border bg-white">
        <table className="w-full text-left text-sm">
          <thead className="bg-slate-50 text-slate-600">
            <tr>
              {["ID", "Employee", "Date", "Check-in", "Check-out", "Status", "Actions"].map((heading) => (
                <th key={heading} className="whitespace-nowrap px-4 py-3 font-semibold">{heading}</th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y">
            {loading ? (
              <tr><td colSpan="7" className="p-8 text-center">Loading attendance...</td></tr>
            ) : records.length === 0 ? (
              <tr><td colSpan="7" className="p-8 text-center text-slate-500">No attendance records for these filters.</td></tr>
            ) : records.map((record) => {
              const employee = employees.find((item) => Number(item.id) === Number(record.employee_id));
              return (
                <tr key={record.id} className="hover:bg-slate-50">
                  <td className="whitespace-nowrap px-4 py-3">{record.id}</td>
                  <td className="whitespace-nowrap px-4 py-3">
                    <div className="font-medium">{employee?.full_name || `Employee #${record.employee_id}`}</div>
                    <div className="text-xs text-slate-500">ID: {record.employee_id}</div>
                  </td>
                  <td className="whitespace-nowrap px-4 py-3">{record.attendance_date}</td>
                  <td className="whitespace-nowrap px-4 py-3">
                    {record.check_in ? new Date(record.check_in).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) : "—"}
                  </td>
                  <td className="whitespace-nowrap px-4 py-3">
                    {record.check_out ? new Date(record.check_out).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) : "—"}
                  </td>
                  <td className="whitespace-nowrap px-4 py-3">
                    <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium">{record.status}</span>
                  </td>
                  <td className="whitespace-nowrap px-4 py-3">
                    <button onClick={() => startEdit(record)} className="mr-3 font-medium text-indigo-600">Edit</button>
                    <button onClick={() => handleDelete(record)} className="font-medium text-red-600">Delete</button>
                    <div className="mt-2 flex flex-wrap items-center gap-2">
                      {!record.check_in && (
                        <button
                          onClick={() => handlePunch(record.employee_id, "in")}
                          className="rounded border border-emerald-300 px-2 py-1 text-xs text-emerald-700 hover:bg-emerald-50"
                        >
                          Check-in
                        </button>
                      )}

                      {record.check_in && !record.check_out && (
                        <button
                          onClick={() => handlePunch(record.employee_id, "out")}
                          className="rounded border border-indigo-300 px-2 py-1 text-xs text-indigo-700 hover:bg-indigo-50"
                        >
                          Check-out
                        </button>
                      )}

                      {record.check_in && record.check_out && (
                        <span className="rounded-full bg-emerald-50 px-2 py-1 text-xs font-medium text-emerald-700">
                          Completed
                        </span>
                      )}
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </section>
  );
}
