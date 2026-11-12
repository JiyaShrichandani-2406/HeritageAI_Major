import { useEffect, useMemo, useRef, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import NavBar from "../components/NavBar.jsx";
import Footer from "../components/Footer.jsx";
import Card from "../components/ui/Card.jsx";
import Badge from "../components/ui/Badge.jsx";
import Button from "../components/ui/button.jsx";
import Thinking from "../components/Thinking.jsx";
import ErrorBanner from "../components/ErrorBanner.jsx";
import MonumentArt from "../components/MonumentArt.jsx";
import { api } from "../lib/api.js";
import { findMonument, MONUMENT_CATALOG } from "../lib/catalog.js";

const CONVO_KEY = "heritageai:conversations:v1";
const SUGGESTED = [
  "Who built the Red Fort?",
  "History of Khajuraho",
  "Best time to visit Agra",
];

function loadConvos() {
  try { return JSON.parse(localStorage.getItem(CONVO_KEY) || "[]"); } catch { return []; }
}
function saveConvos(list) {
  try { localStorage.setItem(CONVO_KEY, JSON.stringify(list.slice(0, 40))); } catch { /* ignore */ }
}

export default function Chat() {
  const [params, setParams] = useSearchParams();
  const monumentHint = findMonument(params.get("monument"));

  const [conversations, setConversations] = useState(() => loadConvos());
  // On every page load / refresh, the main chat window starts blank.
  // activeId stays null until the user either types a new question
  // (creates a fresh conversation) or clicks a saved one in the sidebar
  // (opens it as a read-view).
  const [activeId, setActiveId] = useState(null);
  // True when the current activeId was opened by clicking the sidebar,
  // not by typing a new message. Typing while viewing history starts a
  // brand-new conversation instead of appending to the old one.
  const [isViewingHistory, setIsViewingHistory] = useState(false);
  const [input, setInput] = useState(params.get("q") || "");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const scrollerRef = useRef(null);

  const active = useMemo(
    () => conversations.find((c) => c.id === activeId) || null,
    [conversations, activeId]
  );

  useEffect(() => { saveConvos(conversations); }, [conversations]);
  useEffect(() => { if (scrollerRef.current) scrollerRef.current.scrollTop = scrollerRef.current.scrollHeight; }, [active?.messages?.length, loading]);

  function newConversation() {
    setActiveId(null);
    setIsViewingHistory(false);
    setError(null);
    setInput("");
  }

  function openHistory(id) {
    setActiveId(id);
    setIsViewingHistory(true);
    setError(null);
  }

  async function send(e, overrideText) {
    if (e) e.preventDefault();
    const text = (overrideText ?? input).trim();
    if (!text || loading) return;
    setError(null);
    setInput("");

    // If the user is viewing a historical conversation, typing a new
    // question starts a BRAND-NEW chat rather than appending to the old one.
    let convo = isViewingHistory ? null : active;
    let convoList = conversations;
    if (isViewingHistory) {
      setIsViewingHistory(false);
      setActiveId(null);
    }

    // Ensure a conversation exists
    if (!convo) {
      convo = {
        id: `c_${Date.now()}_${Math.random().toString(36).slice(2,7)}`,
        title: text.slice(0, 48),
        createdAt: Date.now(),
        messages: [],
      };
      convoList = [convo, ...conversations];
      setConversations(convoList);
      setActiveId(convo.id);
    }

    const userMsg = { role: "user", text, ts: Date.now() };
    convoList = convoList.map((c) => c.id === convo.id ? { ...c, messages: [...c.messages, userMsg] } : c);
    setConversations(convoList);

    setLoading(true);
    try {
      const resp = await api.chat({ question: text, top_k: 3 });
      const aiMsg = {
        role: "assistant",
        text: resp.answer,
        sources: resp.sources || [],
        grounded: !!resp.grounded,
        message: resp.message || "",
        ts: Date.now(),
      };
      setConversations((prev) => prev.map((c) => c.id === convo.id ? { ...c, messages: [...c.messages, aiMsg] } : c));
    } catch (err) {
      setError(err);
      // Drop empty assistant turn — show error banner instead.
    } finally {
      setLoading(false);
    }
  }

  // Autosend if landed with ?q=
  useEffect(() => {
    const q = params.get("q");
    if (q && !active) {
      // Remove q from URL to avoid re-sending on refresh
      params.delete("q");
      setParams(params, { replace: true });
      send(null, q);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const messages = active?.messages || [];
  const lastAi = [...messages].reverse().find((m) => m.role === "assistant");
  const bestRelevance = lastAi?.sources?.reduce((acc, s) => Math.max(acc, s.relevance_score ?? 0), 0) ?? null;

  return (
    <div>
      <NavBar />

      <main className="container-page py-8 grid lg:grid-cols-[260px_minmax(0,1fr)_300px] gap-6">
        {/* Left: conversations */}
        <aside className="lg:sticky lg:top-24 h-fit">
          <Button variant="teal" onClick={newConversation} className="w-full">
            <svg viewBox="0 0 24 24" className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M12 5v14"/><path d="M5 12h14"/></svg>
            New Chat
          </Button>
          <div className="mt-3 relative">
            <svg viewBox="0 0 24 24" className="w-4 h-4 absolute left-3 top-3 text-ink-400" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="11" cy="11" r="7"/><path d="M20 20l-3.5-3.5"/></svg>
            <input placeholder="Search conversations" className="w-full pl-9 pr-3 py-2.5 rounded-field border border-cream-300 bg-white text-sm outline-none focus:border-saffron-500" />
          </div>
          <div className="mt-5">
            <div className="eyebrow mb-2">History</div>
            <ul className="space-y-1">
              {conversations.length === 0 && <li className="text-xs text-ink-400">Your conversations will appear here.</li>}
              {conversations.map((c) => {
                const activeItem = c.id === activeId;
                return (
                  <li key={c.id}>
                    <button
                      onClick={() => openHistory(c.id)}
                      className={`w-full text-left px-3 py-2 rounded-xl text-sm ${activeItem ? "bg-teal-50 text-ink-900 font-semibold" : "hover:bg-cream-100 text-ink-700"}`}
                    >
                      {c.title}
                      <div className="text-[11px] text-ink-400 font-normal">Stored in this browser</div>
                    </button>
                  </li>
                );
              })}
            </ul>
          </div>
        </aside>

        {/* Center: chat */}
        <section>
          <Card padding="p-0" className="overflow-hidden flex flex-col min-h-[70vh]">
            <div className="flex items-center gap-3 p-5 border-b border-cream-300">
              <div className="w-10 h-10 rounded-xl bg-teal-900 text-white grid place-items-center">
                <svg viewBox="0 0 24 24" className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="1.8"><path d="M4 21h16"/><rect x="8" y="10" width="8" height="11"/><path d="M8 10 Q12 4 16 10"/></svg>
              </div>
              <div>
                <div className="font-heading font-bold">AI Heritage Guide</div>
                <div className="text-xs text-ink-500">Answers grounded in indexed sources</div>
              </div>
            </div>

            <div ref={scrollerRef} className="flex-1 overflow-y-auto p-5 md:p-6 space-y-4 bg-cream-50">
              {messages.length === 0 && (
                <div className="text-center py-10">
                  <div className="mx-auto w-14 h-14 rounded-full bg-teal-900 text-white grid place-items-center mb-3">
                    <svg viewBox="0 0 24 24" className="w-6 h-6" fill="none" stroke="currentColor" strokeWidth="1.8"><path d="M4 5h16v10H9l-5 4V5z"/></svg>
                  </div>
                  <h3 className="font-heading text-2xl font-bold">Ask about India's heritage</h3>
                  <p className="text-ink-500 text-sm mt-1 max-w-sm mx-auto">Get source-backed answers with citations and relevance scores.</p>
                </div>
              )}

              {messages.map((m, i) => (
                m.role === "user" ? (
                  <div key={i} className="flex justify-end animate-fade-in">
                    <div className="max-w-[80%] px-4 py-2.5 rounded-2xl rounded-br-sm bg-teal-800 text-white text-sm">{m.text}</div>
                  </div>
                ) : (
                  <div key={i} className="flex items-start gap-3 animate-fade-in">
                    <div className="w-9 h-9 rounded-full bg-teal-900 text-white text-xs font-bold grid place-items-center shrink-0">AI</div>
                    <div className="max-w-[88%] bg-white border border-cream-300 rounded-2xl rounded-bl-sm p-4 text-sm leading-relaxed">
                      <div className="text-ink-900 whitespace-pre-wrap">{m.text}</div>

                      {monumentHint && (
                        <div className="mt-3 flex items-center gap-3 p-3 rounded-xl bg-cream-50 border border-cream-200">
                          <MonumentArt art={monumentHint.art} palette={monumentHint.palette} className="w-14 h-10" rounded="rounded-md" />
                          <div className="flex-1">
                            <div className="font-semibold text-sm">{monumentHint.name} <span className="text-ink-400 font-normal">|  {monumentHint.city}</span></div>
                            <Link to={`/monuments/${monumentHint.id}`} className="text-xs text-teal-800 font-semibold">View monument details ›</Link>
                          </div>
                        </div>
                      )}

                      {m.sources?.length > 0 && (
                        <div className="mt-3">
                          <div className="eyebrow !text-ink-400 mb-2">Sources</div>
                          <div className="flex flex-wrap gap-2">
                            {m.sources.map((s, j) => (
                              <a key={j} href={s.url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full border border-cream-300 text-xs text-ink-700 hover:border-saffron-500 hover:text-saffron-600">
                                <svg viewBox="0 0 24 24" className="w-3.5 h-3.5" fill="none" stroke="currentColor" strokeWidth="2"><path d="M10 14a5 5 0 0 1 0-7l3-3a5 5 0 0 1 7 7l-1 1"/><path d="M14 10a5 5 0 0 1 0 7l-3 3a5 5 0 0 1-7-7l1-1"/></svg>
                                {s.title}
                              </a>
                            ))}
                          </div>
                        </div>
                      )}

                      <div className="mt-3 flex items-center gap-3 text-xs">
                        <Badge variant={m.grounded ? "verified" : "unknown"} size="sm">{m.grounded ? "Grounded" : "Not grounded"}</Badge>
                        {m.sources?.[0]?.relevance_score !== undefined && m.sources?.[0]?.relevance_score !== null && (
                          <div className="flex items-center gap-2 text-ink-500">
                            <span>Relevance</span>
                            <div className="w-24 h-1.5 rounded-full bg-cream-200 overflow-hidden">
                              <div className="h-full bg-saffron-500" style={{ width: `${Math.round((m.sources[0].relevance_score || 0) * 100)}%` }} />
                            </div>
                            <span className="font-semibold text-ink-700">{(m.sources[0].relevance_score || 0).toFixed(2)}</span>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                )
              ))}

              {loading && (
                <div className="flex items-center gap-3 animate-fade-in">
                  <div className="w-9 h-9 rounded-full bg-teal-900 text-white text-xs font-bold grid place-items-center">AI</div>
                  <Thinking />
                </div>
              )}

              {error && <ErrorBanner title="The heritage service is unavailable" message={error.message} onRetry={() => { if (messages.length) send(null, [...messages].reverse().find(m=>m.role==="user")?.text); }} />}
            </div>

            {/* Suggested + input */}
            <div className="p-4 md:p-5 border-t border-cream-300 bg-white">
              <div className="mb-3">
                <div className="eyebrow !text-ink-400 mb-1.5">Suggested questions</div>
                <div className="flex flex-wrap gap-2">
                  {SUGGESTED.map((s) => (
                    <button key={s} onClick={() => send(null, s)} className="px-3.5 py-1.5 rounded-full border border-cream-300 text-xs text-ink-700 hover:border-saffron-500 hover:text-saffron-600">{s}</button>
                  ))}
                </div>
              </div>
              <form onSubmit={send} className="flex items-center gap-2 bg-cream-50 border border-cream-300 rounded-full p-1 pl-4">
                <input
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="Ask about a monument, its history or culture..."
                  className="flex-1 bg-transparent outline-none text-sm py-2 text-ink-900 placeholder:text-ink-400"
                />
                <button type="submit" disabled={loading || !input.trim()} className="w-10 h-10 rounded-full bg-saffron-500 text-white grid place-items-center hover:bg-saffron-600 disabled:opacity-50">
                  <svg viewBox="0 0 24 24" className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12h14"/><path d="M13 6l6 6-6 6"/></svg>
                </button>
              </form>
            </div>
          </Card>
        </section>

        {/* Right: context */}
        <aside className="space-y-4">
          {monumentHint && (
            <Card padding="p-0" className="overflow-hidden">
              <MonumentArt art={monumentHint.art} palette={monumentHint.palette} className="aspect-[16/9]" rounded="rounded-none" />
              <div className="p-4">
                <div className="eyebrow mb-1">Context</div>
                <div className="font-semibold">{monumentHint.name}</div>
                <div className="text-xs text-ink-500">{monumentHint.city}, {monumentHint.state}</div>
                <Link to={`/monuments/${monumentHint.id}`} className="inline-flex items-center gap-1 mt-2 text-teal-800 font-semibold text-sm">View details ›</Link>
              </div>
            </Card>
          )}

          <Card>
            <div className="eyebrow mb-2">Sources ({lastAi?.sources?.length || 0})</div>
            {lastAi?.sources?.length ? (
              <ul className="space-y-2.5">
                {lastAi.sources.map((s, i) => (
                  <li key={i}>
                    <a href={s.url} target="_blank" rel="noreferrer" className="flex items-start gap-2 hover:text-saffron-600">
                      <svg viewBox="0 0 24 24" className="w-4 h-4 mt-0.5 shrink-0 text-ink-400" fill="none" stroke="currentColor" strokeWidth="2"><path d="M10 14a5 5 0 0 1 0-7l3-3a5 5 0 0 1 7 7l-1 1"/><path d="M14 10a5 5 0 0 1 0 7l-3 3a5 5 0 0 1-7-7l1-1"/></svg>
                      <div>
                        <div className="font-semibold text-sm">{s.title}</div>
                        <div className="text-xs text-ink-400 break-all">{s.url.replace(/^https?:\/\//, "").split("/")[0]}</div>
                      </div>
                    </a>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-xs text-ink-400">Sources will appear here after you ask a question.</p>
            )}
          </Card>

          <Card>
            <div className="eyebrow mb-2">Answer quality</div>
            <div className="flex items-center gap-2 mb-2">
              <Badge variant={lastAi?.grounded ? "verified" : "unknown"} size="sm">{lastAi ? (lastAi.grounded ? "Grounded" : "Not grounded") : "Awaiting answer"}</Badge>
            </div>
            <div className="text-xs text-ink-500 mb-1">Relevance score</div>
            <div className="w-full h-2 rounded-full bg-cream-200 overflow-hidden">
              <div className="h-full bg-saffron-500 transition-all" style={{ width: `${Math.round((bestRelevance || 0) * 100)}%` }} />
            </div>
          </Card>

          {!loading && !error && messages.length === 0 && (
            <Card className="!bg-cream-100">
              <div className="text-xs text-ink-500">Tip: try asking about a monument's history, its architectural style, or the best time to visit.</div>
            </Card>
          )}

          {/* Quick-pick monuments */}
          <Card>
            <div className="eyebrow mb-2">Jump to a monument</div>
            <div className="flex flex-wrap gap-2">
              {MONUMENT_CATALOG.slice(0,4).map((m) => (
                <Link key={m.id} to={`/chat?monument=${m.id}`} className="px-3 py-1 rounded-full border border-cream-300 text-xs hover:border-saffron-500 hover:text-saffron-600">{m.name}</Link>
              ))}
            </div>
          </Card>
        </aside>
      </main>

      <Footer />
    </div>
  );
}
