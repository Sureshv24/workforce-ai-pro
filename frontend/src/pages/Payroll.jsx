import { useEffect, useState } from "react";
import api from "../api/client";

export default function Payroll({ currentUser }) {
  const [rows, setRows] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [employeeId, setEmployeeId] = useState("");
  const [start, setStart] = useState("");
  const [end, setEnd] = useState("");
  const [salary, setSalary] = useState("");
  const [allowances, setAllowances] = useState("0");
  const [deductions, setDeductions] = useState("0");
  const [notice, setNotice] = useState("");
  const canManage = ["ADMIN", "HR"].includes(String(currentUser?.role || "").toUpperCase());

  async function load() {
    setLoading(true); setError("");
    try {
      const r = await api.get("/payroll/");
      setRows(Array.isArray(r.data) ? r.data : []);
    } catch (e) {
      setError(e.response?.data?.detail || "Unable to load payroll.");
    } finally { setLoading(false); }
  }
  useEffect(() => { load(); }, []);

  async function create(e) {
    e.preventDefault(); setError(""); setNotice("");
    try {
      await api.post("/payroll/", {
        employee_id: Number(employeeId),
        pay_period_start: start, pay_period_end: end,
        basic_salary: Number(salary), allowances: Number(allowances || 0),
        deductions: Number(deductions || 0), currency: "INR", status: "DRAFT"
      });
      setNotice("Payroll record created.");
      setEmployeeId(""); setStart(""); setEnd(""); setSalary("");
      setAllowances("0"); setDeductions("0");
      await load();
    } catch (e) {
      setError(e.response?.data?.detail || "Unable to create payroll.");
    }
  }

  async function update(row) {
    const status = window.prompt("Enter status: DRAFT, APPROVED, PAID or CANCELLED", row.status);
    if (!status) return;
    const next = status.trim().toUpperCase();
    if (!["DRAFT", "APPROVED", "PAID", "CANCELLED"].includes(next)) {
      setError("Invalid payroll status."); return;
    }
    const payload = { status: next };
    if (next === "PAID") {
      const date = window.prompt("Payment date (YYYY-MM-DD):", row.payment_date || new Date().toISOString().slice(0,10));
      if (!date) return;
      payload.payment_date = date;
    }
    try {
      await api.patch(`/payroll/${row.id}`, payload);
      setNotice("Payroll updated."); await load();
    } catch (e) { setError(e.response?.data?.detail || "Unable to update payroll."); }
  }

  async function remove(row) {
    if (!window.confirm(`Delete payroll #${row.id}?`)) return;
    try {
      await api.delete(`/payroll/${row.id}`);
      setNotice("Payroll deleted."); await load();
    } catch (e) { setError(e.response?.data?.detail || "Unable to delete payroll."); }
  }

  const money = (v, c = "INR") => {
    try { return new Intl.NumberFormat("en-IN", { style: "currency", currency: c }).format(Number(v || 0)); }
    catch { return String(v ?? "?"); }
  };

  return <section className="space-y-5">
    <div className="flex items-center justify-between gap-3"><div><h1 className="text-2xl font-bold">Payroll</h1><p className="text-sm text-slate-500">Payroll records from the backend.</p></div><button onClick={load} className="rounded-lg border px-4 py-2">Refresh</button></div>
    {error && <p role="alert" className="rounded-lg bg-red-50 p-3 text-red-700">{String(error)}</p>}
    {notice && <p className="rounded-lg bg-green-50 p-3 text-green-700">{notice}</p>}
    {canManage && <form onSubmit={create} className="grid gap-3 rounded-xl border bg-white p-4 sm:grid-cols-3">
      <h2 className="font-semibold sm:col-span-3">Create payroll record</h2>
      <label className="text-sm">Employee ID<input required type="number" min="1" value={employeeId} onChange={e=>setEmployeeId(e.target.value)} className="mt-1 w-full rounded border p-2"/></label>
      <label className="text-sm">Period start<input required type="date" value={start} onChange={e=>setStart(e.target.value)} className="mt-1 w-full rounded border p-2"/></label>
      <label className="text-sm">Period end<input required type="date" value={end} onChange={e=>setEnd(e.target.value)} className="mt-1 w-full rounded border p-2"/></label>
      <label className="text-sm">Basic salary<input required type="number" min="0" step=".01" value={salary} onChange={e=>setSalary(e.target.value)} className="mt-1 w-full rounded border p-2"/></label>
      <label className="text-sm">Allowances<input type="number" min="0" step=".01" value={allowances} onChange={e=>setAllowances(e.target.value)} className="mt-1 w-full rounded border p-2"/></label>
      <label className="text-sm">Deductions<input type="number" min="0" step=".01" value={deductions} onChange={e=>setDeductions(e.target.value)} className="mt-1 w-full rounded border p-2"/></label>
      <button className="rounded-lg bg-indigo-600 px-4 py-2 text-white sm:col-span-3">Create payroll</button>
    </form>}
    <div className="overflow-x-auto rounded-xl border bg-white"><table className="min-w-full text-left text-sm">
      <thead className="bg-slate-50"><tr>{["ID","Employee","Period","Gross","Net","Status","Payment date",...(canManage?["Actions"]:[])].map(x=><th key={x} className="p-3">{x}</th>)}</tr></thead>
      <tbody className="divide-y">{rows.map(r=><tr key={r.id}><td className="p-3">{r.id}</td><td className="p-3">{r.employee_id}</td><td className="p-3">{r.pay_period_start} ? {r.pay_period_end}</td><td className="p-3">{money(r.gross_salary,r.currency)}</td><td className="p-3">{money(r.net_salary,r.currency)}</td><td className="p-3">{r.status}</td><td className="p-3">{r.payment_date || "?"}</td>{canManage&&<td className="p-3"><button onClick={()=>update(r)} className="mr-3 text-indigo-600">Update</button><button onClick={()=>remove(r)} className="text-red-600">Delete</button></td>}</tr>)}</tbody>
    </table>{loading&&<p className="p-4">Loading payroll?</p>}{!loading&&!rows.length&&<p className="p-4 text-slate-500">No payroll records found.</p>}</div>
  </section>;
}
