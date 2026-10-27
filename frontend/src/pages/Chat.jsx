import { useEffect, useState } from "react";
import api from "../api/client";

export default function Chat({ currentUser }) {
  const [recipient, setRecipient] = useState("");
  const [messages, setMessages] = useState([]);
  const [draft, setDraft] = useState("");
  const [unread, setUnread] = useState(0);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function loadUnread() {
    try { const r = await api.get("/chat/unread-count"); setUnread(Number(r.data?.unread_count || 0)); } catch {}
  }
  async function loadConversation() {
    if (!recipient || Number(recipient) <= 0) { setError("Enter a recipient user ID."); return; }
    setLoading(true); setError("");
    try {
      const r = await api.get("/chat/messages", { params: { with_user_id: Number(recipient), limit: 100 } });
      const list = Array.isArray(r.data) ? r.data : [];
      setMessages(list);
      for (const m of list) {
        if (Number(m.recipient_id) === Number(currentUser?.id) && !m.is_read) {
          try { await api.patch(`/chat/messages/${m.id}/read`); } catch {}
        }
      }
      await loadUnread();
    } catch (e) { setError(e.response?.data?.detail || "Unable to load conversation."); }
    finally { setLoading(false); }
  }
  useEffect(() => { loadUnread(); }, []);

  async function send(e) {
    e.preventDefault(); if (!draft.trim() || !recipient) return;
    setError("");
    try {
      await api.post("/chat/messages", { recipient_id: Number(recipient), message: draft.trim() });
      setDraft(""); await loadConversation();
    } catch (e) { setError(e.response?.data?.detail || "Unable to send message."); }
  }

  return <section className="space-y-5">
    <div><h1 className="text-2xl font-bold">Chat</h1><p className="text-sm text-slate-500">{unread} unread messages</p></div>
    <div className="grid gap-4 lg:grid-cols-[260px_1fr]">
      <aside className="rounded-xl border bg-white p-4"><label className="text-sm font-medium">Recipient user ID<input type="number" min="1" value={recipient} onChange={e=>setRecipient(e.target.value)} className="mt-1 w-full rounded border p-2"/></label><button onClick={loadConversation} className="mt-3 w-full rounded-lg border px-3 py-2">Load conversation</button><p className="mt-3 text-xs text-slate-500">Use the account user ID, not the employee ID. You cannot message yourself.</p></aside>
      <div className="flex min-h-96 flex-col rounded-xl border bg-white">
        <div className="border-b p-3 font-semibold">{recipient?`Conversation with user ${recipient}`:"Choose a recipient"}</div>
        {error&&<p role="alert" className="m-3 rounded bg-red-50 p-3 text-sm text-red-700">{String(error)}</p>}
        <div className="flex-1 space-y-3 overflow-y-auto p-4">{messages.map(m=><div key={m.id} className={`flex ${Number(m.sender_id)===Number(currentUser?.id)?"justify-end":"justify-start"}`}><div className={`max-w-[80%] rounded-xl p-3 ${Number(m.sender_id)===Number(currentUser?.id)?"bg-indigo-600 text-white":"bg-slate-100"}`}><p className="whitespace-pre-wrap break-words text-sm">{m.message}</p><p className="mt-1 text-xs opacity-70">{m.created_at?new Date(m.created_at).toLocaleString():""} {m.is_read?"? Read":""}</p></div></div>)}{loading&&<p className="text-sm text-slate-500">Loading?</p>}</div>
        <form onSubmit={send} className="flex gap-2 border-t p-3"><input value={draft} onChange={e=>setDraft(e.target.value)} maxLength="5000" placeholder="Write a message?" className="min-w-0 flex-1 rounded-lg border p-3" disabled={!recipient}/><button disabled={!recipient||!draft.trim()} className="rounded-lg bg-indigo-600 px-4 text-white disabled:opacity-40">Send</button></form>
      </div>
    </div>
  </section>;
}
