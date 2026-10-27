import { useEffect, useState } from "react";
import api from "../api/client";

export default function Notifications() {
  const [items, setItems] = useState([]);
  const [unread, setUnread] = useState(0);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function load() {
    setLoading(true); setError("");
    try {
      const [list, count] = await Promise.all([
        api.get("/notifications/"), api.get("/notifications/unread-count")
      ]);
      setItems(Array.isArray(list.data) ? list.data : []);
      setUnread(Number(count.data?.unread_count || 0));
    } catch (e) { setError(e.response?.data?.detail || "Unable to load notifications."); }
    finally { setLoading(false); }
  }
  useEffect(() => { load(); }, []);

  async function markOne(item) {
    try {
      await api.patch(`/notifications/${item.id}/read`);
      await load();
    } catch (e) { setError(e.response?.data?.detail || "Unable to mark as read."); }
  }
  async function markAll() {
    try {
      await api.patch("/notifications/read-all");
      await load();
    } catch (e) { setError(e.response?.data?.detail || "Unable to mark all as read."); }
  }

  return <section className="space-y-5">
    <div className="flex items-center justify-between gap-3"><div><h1 className="text-2xl font-bold">Notifications</h1><p className="text-sm text-slate-500">{unread} unread notifications</p></div><div className="flex gap-2"><button onClick={load} className="rounded-lg border px-3 py-2">Refresh</button><button onClick={markAll} disabled={!unread} className="rounded-lg bg-indigo-600 px-3 py-2 text-white disabled:opacity-40">Mark all read</button></div></div>
    {error&&<p role="alert" className="rounded-lg bg-red-50 p-3 text-red-700">{String(error)}</p>}
    <div className="space-y-3">{items.map(n=><article key={n.id} className="rounded-xl border bg-white p-4"><div className="flex items-start justify-between gap-3"><div><h2 className="font-semibold">{n.title || n.subject || n.category || "Notification"} {!n.is_read&&<span className="text-xs text-indigo-600">NEW</span>}</h2><p className="mt-1 text-sm text-slate-600">{n.message}</p><p className="mt-2 text-xs text-slate-400">{n.created_at?new Date(n.created_at).toLocaleString():""}</p></div>{!n.is_read&&<button onClick={()=>markOne(n)} className="rounded border px-3 py-2 text-sm">Mark read</button>}</div></article>)}
    {loading&&<p className="p-4 text-slate-500">Loading?</p>}{!loading&&!items.length&&<p className="rounded-xl border bg-white p-6 text-slate-500">No notifications found.</p>}</div>
  </section>;
}
