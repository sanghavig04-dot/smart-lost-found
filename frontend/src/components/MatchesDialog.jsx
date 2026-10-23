import { useEffect, useRef } from "react";
import { imageSrc } from "../api";

export default function MatchesDialog({ state, onClose }) {
  const ref = useRef(null);

  useEffect(() => {
    const dialog = ref.current;
    if (state && !dialog.open) dialog.showModal();
    if (!state && dialog.open) dialog.close();
  }, [state]);

  const { item, matches, error } = state || {};

  return (
    <dialog ref={ref} className="sheet" onClose={onClose} aria-labelledby="matches-title">
      <div className="sheet-head">
        <h2 id="matches-title">Possible matches for {item ? `"${item.title}"` : ""}</h2>
        <button type="button" className="btn btn-quiet" onClick={onClose}>
          Close
        </button>
      </div>

      {error && <p className="error" role="alert">{error}</p>}
      {!error && matches === null && <p className="hint">Comparing photos and descriptions…</p>}
      {!error && matches && matches.length === 0 && (
        <p className="hint">
          No likely matches yet. New reports are compared as they arrive, so check back later.
        </p>
      )}

      <ul className="matches">
        {matches?.map(({ score, item: m }) => {
          const pct = Math.round(score * 100);
          const src = imageSrc(m.image_url);
          const subject = encodeURIComponent(`Lost & Found: ${m.title}`);
          return (
            <li key={m.id} className="match">
              {src ? <img src={src} alt={m.title} /> : <div className="match-nophoto">{m.category}</div>}
              <div>
                <h3>{m.title}</h3>
                <p className="tag-meta">{m.location || "Location not given"}</p>
                <div className="bar" role="img" aria-label={`${pct}% match`}>
                  <span style={{ width: `${pct}%` }} />
                </div>
                <p className="pct">{pct}% match</p>
                <p className="tag-meta">{m.reporter_name}: {m.contact_email}</p>
                <div className="tag-actions">
                  <button
                   type="button"
                   className="btn btn-quiet"
                   onClick={() => navigator.clipboard.writeText(m.contact_email)}
                  >
                   Copy email
                  </button>
                  <a
                    className="btn btn-quiet"
                    href={`https://mail.google.com/mail/?view=cm&to=${encodeURIComponent(m.contact_email)}&su=${subject}`}
                    target="_blank"
                    rel="noreferrer"
                  >
                    Open in Gmail
                  </a>
                </div>
              </div>
            </li>
          );
        })}
      </ul>
    </dialog>
  );
}
