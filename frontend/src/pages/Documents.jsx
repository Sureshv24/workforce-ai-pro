import { useEffect, useState } from "react";
import api from "../api/client";

export default function Documents({ currentUser }) {
  const [items, setItems] = useState([]);
  const [file, setFile] = useState(null);
  const [category, setCategory] = useState("GENERAL");
  const [description, setDescription] = useState("");
  const [employeeId, setEmployeeId] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [loading, setLoading] = useState(false);
  const canAssign = ["ADMIN", "HR"].includes(String(currentUser?.role || "").toUpperCase());

  async function load() {
    setLoading(true); setError("");
    try { const r = await api.get("/documents/", { params: { limit: 100, offset: 0 } }); setItems(Array.isArray(r.data)?r.data:[]); }
    catch (e) { setError(e.response?.data?.detail || "Unable to load documents."); }
    finally { setLoading(false); }
  }
  useEffect(() => { load(); }, []);

  async function upload(e) {
    e.preventDefault(); if (!file) { setError("Choose a file first."); return; }
    setError(""); setNotice("");
    const data = new FormData();
    data.append("file", file); data.append("category", category);
    data.append("description", description);
    if (canAssign && employeeId) data.append("employee_id", employeeId);
    try {
      await api.post("/documents/", data, { headers: { "Content-Type": "multipart/form-data" } });
      setNotice("Document uploaded."); setFile(null); setDescription(""); setEmployeeId("");
      e.target.reset(); await load();
    } catch (e) { setError(e.response?.data?.detail || "Unable to upload document."); }
  }
  async function download(doc) {
    try {
      const r = await api.get(`/documents/${doc.id}/download`, { responseType: "blob" });
      const url = URL.createObjectURL(r.data); const a = document.createElement("a");
      a.href=url; a.download=doc.original_filename || `document-${doc.id}`; a.click(); URL.revokeObjectURL(url);
    } catch (e) { setError(e.response?.data?.detail || "Unable to download document."); }
  }
  async function remove(doc) {
    if (!window.confirm(`Delete ${doc.original_filename}?`)) return;
    try { await api.delete(`/documents/${doc.id}`); setItems(old=>old.filter(x=>x.id!==doc.id)); setNotice("Document deleted."); }
    catch (e) { setError(e.response?.data?.detail || "Unable to delete document."); }
  }

  return <section className="space-y-5">
    <div className="flex items-center justify-between"><div><h1 className="text-2xl font-bold">Documents</h1><p className="text-sm text-slate-500">Upload and manage your documents.</p></div><button onClick={load} className="rounded-lg border px-3 py-2">Refresh</button></div>
    {error&&<p role="alert" className="rounded-lg bg-red-50 p-3 text-red-700">{String(error)}</p>}{notice&&<p className="rounded-lg bg-green-50 p-3 text-green-700">{notice}</p>}
    <form onSubmit={upload} className="grid gap-3 rounded-xl border bg-white p-4 sm:grid-cols-2"><h2 className="font-semibold sm:col-span-2">Upload document</h2>
      <label className="text-sm">File (max 10 MB)<input required type="file" accept=".pdf,.png,.jpg,.jpeg,.doc,.docx,.txt,.csv,.xlsx" onChange={e=>setFile(e.target.files?.[0]||null)} className="mt-1 block w-full rounded border p-2"/></label>
      <label className="text-sm">Category<input maxLength="50" value={category} onChange={e=>setCategory(e.target.value)} className="mt-1 w-full rounded border p-2"/></label>
      <label className="text-sm sm:col-span-2">Description<textarea maxLength="2000" value={description} onChange={e=>setDescription(e.target.value)} className="mt-1 w-full rounded border p-2"/></label>
      {canAssign&&<label className="text-sm">Employee ID (optional)<input type="number" min="1" value={employeeId} onChange={e=>setEmployeeId(e.target.value)} className="mt-1 w-full rounded border p-2"/></label>}
      <button className="rounded-lg bg-indigo-600 px-4 py-2 text-white sm:col-span-2">Upload document</button>
    </form>
    <div className="overflow-x-auto rounded-xl border bg-white"><table className="min-w-full text-left text-sm"><thead className="bg-slate-50"><tr>{["File","Category","Employee","Size","Actions"].map(x=><th key={x} className="p-3">{x}</th>)}</tr></thead><tbody className="divide-y">{items.map(d=><tr key={d.id}><td className="p-3">{d.original_filename}<div className="text-xs text-slate-500">{d.description}</div></td><td className="p-3">{d.category}</td><td className="p-3">{d.employee_id??"?"}</td><td className="p-3">{Math.round(Number(d.file_size||0)/1024)} KB</td><td className="p-3"><button onClick={()=>download(d)} className="mr-3 text-indigo-600">Download</button><button onClick={()=>remove(d)} className="text-red-600">Delete</button></td></tr>)}</tbody></table>{loading&&<p className="p-4">Loading documents?</p>}{!loading&&!items.length&&<p className="p-4 text-slate-500">No documents found.</p>}</div>
  </section>;
}
