import { useEffect, useState } from "react";
import {
  getDepartments,
  createDepartment,
  updateDepartment,
  deleteDepartment,
} from "../api/departments";

const emptyForm = { name: "", description: "" };

export default function Departments() {
  const [departments, setDepartments] = useState([]);
  const [form, setForm] = useState(emptyForm);
  const [editingId, setEditingId] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function loadDepartments() {
    setLoading(true);
    setError("");

    try {
      const response = await getDepartments({ page: 1, page_size: 100 });
      setDepartments(response.data);
    } catch (err) {
      setError(
        err.response?.data?.detail || "Unable to load departments."
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadDepartments();
  }, []);

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");

    const payload = {
      name: form.name.trim(),
      description: form.description.trim() || null,
    };

    try {
      if (editingId !== null) {
        await updateDepartment(editingId, payload);
      } else {
        await createDepartment(payload);
      }

      setForm(emptyForm);
      setEditingId(null);
      await loadDepartments();
    } catch (err) {
      setError(err.response?.data?.detail || "Unable to save department.");
    }
  }

  async function handleDelete(department) {
    if (!window.confirm(`Delete ${department.name}?`)) return;

    setError("");

    try {
      await deleteDepartment(department.id);
      await loadDepartments();
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        "Unable to delete department. Check whether employees are assigned to it."
      );
    }
  }

  return (
    <section className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Departments</h1>
        <p className="mt-1 text-sm text-slate-500">
          Manage departments using live backend data.
        </p>
      </div>

      {error && (
        <div role="alert" className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit}
        className="grid gap-4 rounded-xl border bg-white p-5 sm:grid-cols-2">
        <h2 className="text-lg font-semibold sm:col-span-2">
          {editingId !== null ? "Edit department" : "Create department"}
        </h2>

        <input required maxLength={100} placeholder="Department name"
          value={form.name}
          onChange={(e) => setForm({ ...form, name: e.target.value })}
          className="rounded-lg border p-3" />

        <input maxLength={500} placeholder="Description"
          value={form.description}
          onChange={(e) => setForm({ ...form, description: e.target.value })}
          className="rounded-lg border p-3" />

        <div className="flex gap-2 sm:col-span-2">
          <button type="submit"
            className="rounded-lg bg-indigo-600 px-5 py-2.5 font-medium text-white">
            {editingId !== null ? "Save changes" : "Create department"}
          </button>

          {editingId !== null && (
            <button type="button"
              onClick={() => { setEditingId(null); setForm(emptyForm); }}
              className="rounded-lg border px-5 py-2.5">
              Cancel
            </button>
          )}
        </div>
      </form>

      <div className="overflow-x-auto rounded-xl border bg-white">
        <table className="w-full text-left text-sm">
          <thead className="bg-slate-50 text-slate-600">
            <tr>
              <th className="px-4 py-3">ID</th>
              <th className="px-4 py-3">Department</th>
              <th className="px-4 py-3">Description</th>
              <th className="px-4 py-3">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {loading ? (
              <tr><td colSpan="4" className="p-8 text-center">Loading departments...</td></tr>
            ) : departments.length === 0 ? (
              <tr><td colSpan="4" className="p-8 text-center">No departments found.</td></tr>
            ) : departments.map((department) => (
              <tr key={department.id} className="hover:bg-slate-50">
                <td className="px-4 py-3">{department.id}</td>
                <td className="px-4 py-3 font-medium">{department.name}</td>
                <td className="px-4 py-3">{department.description || "—"}</td>
                <td className="whitespace-nowrap px-4 py-3">
                  <button
                    onClick={() => {
                      setEditingId(department.id);
                      setForm({
                        name: department.name || "",
                        description: department.description || "",
                      });
                      window.scrollTo({ top: 0, behavior: "smooth" });
                    }}
                    className="mr-3 font-medium text-indigo-600">
                    Edit
                  </button>
                  <button onClick={() => handleDelete(department)}
                    className="font-medium text-red-600">
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <button onClick={loadDepartments}
        className="rounded-lg border bg-white px-4 py-2">
        Refresh departments
      </button>
    </section>
  );
}
