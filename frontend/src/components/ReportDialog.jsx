import { useEffect, useRef, useState } from "react";
import { createItem } from "../api";

const CATEGORIES = ["electronics", "bags", "documents", "keys", "clothing", "stationery", "other"];
const EMPTY = { title: "", description: "", category: "other", location: "", reporter_name: "", contact_email: "" };

export default function ReportDialog({ type, onTypeChange, onClose, onCreated }) {
  const ref = useRef(null);
  const [form, setForm] = useState(EMPTY);
  const [image, setImage] = useState(null);
  const [preview, setPreview] = useState(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    const dialog = ref.current;
    if (type && !dialog.open) dialog.showModal();
    if (!type && dialog.open) dialog.close();
  }, [type]);

  useEffect(() => {
    if (!image) return setPreview(null);
    const url = URL.createObjectURL(image);
    setPreview(url);
    return () => URL.revokeObjectURL(url);
  }, [image]);

  const set = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }));

  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    setError("");
    const data = new FormData();
    data.append("type", type);
    Object.entries(form).forEach(([k, v]) => data.append(k, v));
    if (image) data.append("image", image);
    try {
      const created = await createItem(data);
      setForm(EMPTY);
      setImage(null);
      onCreated(created);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <dialog ref={ref} className="sheet" onClose={onClose} aria-labelledby="report-title">
      <form onSubmit={submit}>
        <div className="sheet-head">
          <h2 id="report-title">{type === "found" ? "I found something" : "I lost something"}</h2>
          <button type="button" className="btn btn-quiet" onClick={onClose}>
            Close
          </button>
        </div>

        <div className="segmented" role="group" aria-label="Report type">
          {["lost", "found"].map((t) => (
            <button
              key={t}
              type="button"
              aria-pressed={type === t}
              className={`seg seg-${t}`}
              onClick={() => onTypeChange(t)}
            >
              {t === "lost" ? "Lost" : "Found"}
            </button>
          ))}
        </div>

        <label>
          What is it?
          <input required value={form.title} onChange={set("title")} placeholder="Blue steel water bottle" />
        </label>
        <label>
          Details that help identify it
          <textarea rows={3} value={form.description} onChange={set("description")} placeholder="Brand, colour, stickers, scratches" />
        </label>
        <div className="row">
          <label>
            Category
            <select value={form.category} onChange={set("category")}>
              {CATEGORIES.map((c) => (
                <option key={c} value={c}>
                  {c[0].toUpperCase() + c.slice(1)}
                </option>
              ))}
            </select>
          </label>
          <label>
            {type === "found" ? "Where did you find it?" : "Where did you last see it?"}
            <input value={form.location} onChange={set("location")} placeholder="Library, 2nd floor" />
          </label>
        </div>

        <label>
          Photo (a clear photo gives better matches)
          <input type="file" accept="image/jpeg,image/png,image/webp" onChange={(e) => setImage(e.target.files[0] || null)} />
        </label>
        {preview && <img className="preview" src={preview} alt="Selected item preview" />}

        <div className="row">
          <label>
            Your name
            <input required value={form.reporter_name} onChange={set("reporter_name")} />
          </label>
          <label>
            Email
            <input required type="email" value={form.contact_email} onChange={set("contact_email")} />
          </label>
        </div>
        <p className="hint">Your email is only shown to people whose items might match yours.</p>

        {error && (
          <p className="error" role="alert">
            {error}
          </p>
        )}
        <button type="submit" className={`btn btn-${type || "lost"}`} disabled={busy}>
          {busy ? "Saving and comparing photos…" : type === "found" ? "Report found item" : "Report lost item"}
        </button>
      </form>
    </dialog>
  );
}
