import { imageSrc } from "../api";

const formatDate = (iso) =>
  new Date(iso).toLocaleDateString(undefined, { day: "numeric", month: "short" });

export default function ItemTag({ item, canResolve, onMatches, onResolve }) {
  const src = imageSrc(item.image_url);
  return (
    <li className={`tag tag-${item.type}`}>
      <div className="tag-photo">
        {src ? (
          <img src={src} alt={item.title} loading="lazy" />
        ) : (
          <span className="tag-nophoto">{item.category}</span>
        )}
      </div>
      <div className="tag-body">
        <p className="tag-kind">{item.type === "lost" ? "Lost" : "Found"}</p>
        <h3>{item.title}</h3>
        {item.description && <p className="tag-desc">{item.description}</p>}
        <p className="tag-meta">
          {item.location || "Location not given"}, {formatDate(item.created_at)}
        </p>
        <div className="tag-actions">
          <button type="button" className="btn btn-quiet" onClick={() => onMatches(item)}>
            See possible matches
          </button>
          {canResolve && (
            <button type="button" className="btn btn-quiet" onClick={() => onResolve(item)}>
              Mark as returned
            </button>
          )}
        </div>
      </div>
    </li>
  );
}
