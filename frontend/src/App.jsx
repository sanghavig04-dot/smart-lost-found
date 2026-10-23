import { useCallback, useEffect, useState } from "react";
import { getMatches, listItems, resolveItem } from "./api";
import ItemTag from "./components/ItemTag.jsx";
import MatchesDialog from "./components/MatchesDialog.jsx";
import ReportDialog from "./components/ReportDialog.jsx";

const TOKEN_KEY = "lostfound.tokens";
const loadTokens = () => {
  try {
    return JSON.parse(localStorage.getItem(TOKEN_KEY)) || {};
  } catch {
    return {};
  }
};

const FILTERS = [
  ["all", "All"],
  ["lost", "Lost"],
  ["found", "Found"],
];

export default function App() {
  const [items, setItems] = useState([]);
  const [filter, setFilter] = useState("all");
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("loading");
  const [reportType, setReportType] = useState(null);
  const [matchState, setMatchState] = useState(null);
  const [tokens, setTokens] = useState(loadTokens);
  const [notice, setNotice] = useState("");

  const reload = useCallback(async () => {
    try {
      setItems(await listItems({ type: filter, q: query.trim() }));
      setStatus("ready");
    } catch {
      setStatus("error");
    }
  }, [filter, query]);

  useEffect(() => {
    const t = setTimeout(reload, 250);
    return () => clearTimeout(t);
  }, [reload]);

  async function openMatches(item) {
    setMatchState({ item, matches: null, error: null });
    try {
      setMatchState({ item, matches: await getMatches(item.id), error: null });
    } catch (err) {
      setMatchState({ item, matches: null, error: err.message });
    }
  }

  function handleCreated(item) {
    const next = { ...tokens, [item.id]: item.manage_token };
    localStorage.setItem(TOKEN_KEY, JSON.stringify(next));
    setTokens(next);
    setReportType(null);
    reload();
    openMatches(item);
  }

  async function handleResolve(item) {
    try {
      await resolveItem(item.id, tokens[item.id]);
      setNotice(`"${item.title}" marked as returned.`);
      reload();
    } catch (err) {
      setNotice(err.message);
    }
  }

  return (
    <>
      <header className="masthead">
        <div>
          <h1>Lost &amp; Found</h1>
          <p>
            Report what you lost or found. We compare photos and descriptions and suggest likely
            matches.
          </p>
        </div>
        <div className="masthead-actions">
          <button className="btn btn-lost" onClick={() => setReportType("lost")}>
            I lost something
          </button>
          <button className="btn btn-found" onClick={() => setReportType("found")}>
            I found something
          </button>
        </div>
      </header>

      <main>
        <div className="toolbar">
          <div className="segmented" role="group" aria-label="Filter items">
            {FILTERS.map(([value, label]) => (
              <button
                key={value}
                type="button"
                className="seg"
                aria-pressed={filter === value}
                onClick={() => setFilter(value)}
              >
                {label}
              </button>
            ))}
          </div>
          <input
            type="search"
            className="search"
            placeholder="Search title, details or place"
            aria-label="Search items"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        </div>

        <p className="notice" role="status" aria-live="polite">
          {notice}
        </p>

        {status === "loading" && <p className="hint">Loading items…</p>}
        {status === "error" && (
          <p className="error" role="alert">
            Can't reach the server. Check that the backend is running on port 8000.
          </p>
        )}
        {status === "ready" && items.length === 0 && (
          <p className="hint">Nothing here yet. Report the first lost or found item.</p>
        )}

        <ul className="grid">
          {items.map((item) => (
            <ItemTag
              key={item.id}
              item={item}
              canResolve={Boolean(tokens[item.id])}
              onMatches={openMatches}
              onResolve={handleResolve}
            />
          ))}
        </ul>
      </main>

      <ReportDialog
        type={reportType}
        onTypeChange={setReportType}
        onClose={() => setReportType(null)}
        onCreated={handleCreated}
      />
      <MatchesDialog state={matchState} onClose={() => setMatchState(null)} />
    </>
  );
}
