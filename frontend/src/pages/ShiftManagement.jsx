import { useCallback, useEffect, useState } from "react";
import api from "../api/client";

const EMPTY_FORM = {
  name: "",
  start_time: "09:00",
  end_time: "18:00",
  break_minutes: "60",
};

const inputClass =
  "w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-sm text-slate-800 outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100";

function formatTime(value) {
  return String(value || "").slice(0, 5);
}

function formatDuration(minutes) {
  const total = Number(minutes || 0);
  return `${Math.floor(total / 60)}h ${total % 60}m`;
}

export default function ShiftManagement({ currentUser }) {
  const role = String(currentUser?.role || "").toUpperCase();
  const canManage = role === "ADMIN" || role === "HR";

  const [shifts, setShifts] = useState([]);
  const [form, setForm] = useState(EMPTY_FORM);
  const [editingId, setEditingId] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [deletingId, setDeletingId] = useState(null);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const loadShifts = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const response = await api.get("/attendance/shifts");
      setShifts(Array.isArray(response.data) ? response.data : []);
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "Unable to load shifts. Please check your login and API connection."
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadShifts();
  }, [loadShifts]);

  function resetForm() {
    setForm(EMPTY_FORM);
    setEditingId(null);
    setShowForm(false);
  }

  function updateForm(event) {
    const { name, value } = event.target;
    setForm((previous) => ({ ...previous, [name]: value }));
  }

  function startEditing(shift) {
    setEditingId(shift.id);
    setForm({
      name: shift.name,
      start_time: formatTime(shift.start_time),
      end_time: formatTime(shift.end_time),
      break_minutes: String(shift.break_minutes),
    });
    setShowForm(true);
    setError("");
    setMessage("");
  }

  async function saveShift(event) {
    event.preventDefault();
    setSaving(true);
    setError("");
    setMessage("");

    const payload = {
      name: form.name.trim(),
      start_time: form.start_time,
      end_time: form.end_time,
      break_minutes: Number(form.break_minutes),
    };

    try {
      if (editingId !== null) {
        await api.patch(`/attendance/shifts/${editingId}`, payload);
        setMessage("Shift updated successfully.");
      } else {
        await api.post("/attendance/shifts", payload);
        setMessage("Shift created successfully.");
      }

      resetForm();
      await loadShifts();
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "Unable to save the shift. Please review the entered values."
      );
    } finally {
      setSaving(false);
    }
  }

  async function deleteShift(shift) {
    const confirmed = window.confirm(
      `Delete the "${shift.name}" shift? If attendance records use this shift, the backend will prevent deletion.`
    );

    if (!confirmed) return;

    setDeletingId(shift.id);
    setError("");
    setMessage("");

    try {
      await api.delete(`/attendance/shifts/${shift.id}`);
      setMessage("Shift deleted successfully.");
      await loadShifts();
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "Unable to delete this shift."
      );
    } finally {
      setDeletingId(null);
    }
  }

  const totalExpectedMinutes = shifts.reduce(
    (sum, shift) => sum + Number(shift.expected_work_minutes || 0),
    0
  );

  return (
    <div className="space-y-6">
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">
            Shift Management
          </h1>
          <p className="mt-1 text-sm text-slate-500">
            Configure work shifts, timings and break durations.
          </p>
        </div>

        {canManage && (
          <button
            type="button"
            onClick={() => {
              if (showForm) {
                resetForm();
              } else {
                setForm(EMPTY_FORM);
                setEditingId(null);
                setShowForm(true);
              }
              setError("");
              setMessage("");
            }}
            className="rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-indigo-700"
          >
            {showForm ? "Cancel" : "+ Create Shift"}
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
          onSubmit={saveShift}
          className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm"
        >
          <h2 className="mb-4 text-lg font-semibold text-slate-900">
            {editingId !== null ? "Edit Shift" : "Create New Shift"}
          </h2>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <label className="space-y-1 text-sm font-medium text-slate-700">
              Shift Name
              <input
                className={inputClass}
                name="name"
                value={form.name}
                onChange={updateForm}
                placeholder="e.g. General Shift"
                maxLength={100}
                required
              />
            </label>

            <label className="space-y-1 text-sm font-medium text-slate-700">
              Start Time
              <input
                className={inputClass}
                type="time"
                name="start_time"
                value={form.start_time}
                onChange={updateForm}
                required
              />
            </label>

            <label className="space-y-1 text-sm font-medium text-slate-700">
              End Time
              <input
                className={inputClass}
                type="time"
                name="end_time"
                value={form.end_time}
                onChange={updateForm}
                required
              />
              <span className="block text-xs font-normal text-slate-500">
                An earlier end time is treated as the following day.
              </span>
            </label>

            <label className="space-y-1 text-sm font-medium text-slate-700">
              Break (minutes)
              <input
                className={inputClass}
                type="number"
                name="break_minutes"
                min="0"
                max="720"
                step="1"
                value={form.break_minutes}
                onChange={updateForm}
                required
              />
            </label>
          </div>

          <div className="mt-5 flex flex-wrap gap-3">
            <button
              type="submit"
              disabled={saving}
              className="rounded-lg bg-indigo-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-indigo-700 disabled:opacity-60"
            >
              {saving
                ? "Saving..."
                : editingId !== null
                  ? "Save Changes"
                  : "Create Shift"}
            </button>

            <button
              type="button"
              onClick={resetForm}
              className="rounded-lg border border-slate-300 px-5 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50"
            >
              Cancel
            </button>
          </div>
        </form>
      )}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <p className="text-sm text-slate-500">Configured Shifts</p>
          <p className="mt-2 text-3xl font-bold text-indigo-600">
            {shifts.length}
          </p>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <p className="text-sm text-slate-500">Combined Expected Work Time</p>
          <p className="mt-2 text-3xl font-bold text-emerald-600">
            {formatDuration(totalExpectedMinutes)}
          </p>
          <p className="mt-1 text-xs text-slate-500">
            Sum of the expected minutes for all configured shifts.
          </p>
        </div>
      </div>

      <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
        <div className="flex items-center justify-between border-b border-slate-200 px-5 py-4">
          <h2 className="font-semibold text-slate-900">Configured Shifts</h2>
          <button
            type="button"
            onClick={loadShifts}
            className="rounded-lg border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
          >
            Refresh
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full min-w-[760px] text-left text-sm">
            <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
              <tr>
                <th className="px-5 py-3">ID</th>
                <th className="px-5 py-3">Shift Name</th>
                <th className="px-5 py-3">Start</th>
                <th className="px-5 py-3">End</th>
                <th className="px-5 py-3">Break</th>
                <th className="px-5 py-3">Expected Work</th>
                {canManage && <th className="px-5 py-3">Actions</th>}
              </tr>
            </thead>

            <tbody className="divide-y divide-slate-100">
              {loading ? (
                <tr>
                  <td
                    colSpan={canManage ? 7 : 6}
                    className="px-5 py-10 text-center text-slate-500"
                  >
                    Loading shifts...
                  </td>
                </tr>
              ) : shifts.length === 0 ? (
                <tr>
                  <td
                    colSpan={canManage ? 7 : 6}
                    className="px-5 py-10 text-center text-slate-500"
                  >
                    No shifts have been configured.
                  </td>
                </tr>
              ) : (
                shifts.map((shift) => (
                  <tr key={shift.id} className="hover:bg-slate-50">
                    <td className="px-5 py-4 text-slate-500">{shift.id}</td>
                    <td className="px-5 py-4 font-medium text-slate-900">
                      {shift.name}
                    </td>
                    <td className="px-5 py-4 text-slate-700">
                      {formatTime(shift.start_time)}
                    </td>
                    <td className="px-5 py-4 text-slate-700">
                      {formatTime(shift.end_time)}
                    </td>
                    <td className="px-5 py-4 text-slate-700">
                      {shift.break_minutes} min
                    </td>
                    <td className="px-5 py-4 font-medium text-emerald-700">
                      {formatDuration(shift.expected_work_minutes)}
                    </td>

                    {canManage && (
                      <td className="px-5 py-4">
                        <div className="flex gap-2">
                          <button
                            type="button"
                            onClick={() => startEditing(shift)}
                            className="rounded-md border border-indigo-200 px-3 py-1.5 text-xs font-semibold text-indigo-700 hover:bg-indigo-50"
                          >
                            Edit
                          </button>
                          <button
                            type="button"
                            disabled={deletingId === shift.id}
                            onClick={() => deleteShift(shift)}
                            className="rounded-md border border-red-200 px-3 py-1.5 text-xs font-semibold text-red-700 hover:bg-red-50 disabled:opacity-60"
                          >
                            {deletingId === shift.id ? "Deleting..." : "Delete"}
                          </button>
                        </div>
                      </td>
                    )}
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
