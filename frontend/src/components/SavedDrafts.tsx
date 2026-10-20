import { useEffect, useState } from "react";
import { listSavedDrafts, saveDraft, deleteSavedDraft } from "../api";
import type { Draft, SavedDraft } from "../types";
export default function SavedDrafts({
  draft,
  onLoad,
}: {
  draft: Draft;
  onLoad: (draft: Draft) => void;
}) {
  const [rows, setRows] = useState<SavedDraft[]>([]);
  const [name, setName] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);
  async function refresh() {
    setRows(await listSavedDrafts());
  }
  useEffect(() => {
    refresh().catch(() =>
      setError(
        "Saved drafts could not be loaded. Try saving again when the API is available.",
      ),
    );
  }, []);
  async function save() {
    setBusy(true);
    setError("");
    setNotice("");
    try {
      await saveDraft(name.trim(), draft);
      await refresh();
      setName("");
      setNotice("Draft saved to the database.");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not save draft.");
    } finally {
      setBusy(false);
    }
  }
  async function remove(id: string) {
    setBusy(true);
    setError("");
    setNotice("");
    try {
      await deleteSavedDraft(id);
      await refresh();
      setNotice("Saved draft deleted.");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not delete draft.");
    } finally {
      setBusy(false);
    }
  }
  return (
    <section className="panel saved-drafts" aria-label="Saved drafts">
      <h2>Saved drafts</h2>
      <p>
        Keep your pool, comfort ratings and team picks for later. Saved for this
        browser; clearing its cookies removes access.
      </p>
      <div className="save-form">
        <input
          aria-label="Draft name"
          placeholder="e.g. ADC vs Jhin / Nautilus"
          value={name}
          maxLength={80}
          onChange={(e) => setName(e.target.value)}
        />
        <button
          className="button secondary"
          disabled={busy || !name.trim() || !draft.championPool.length}
          onClick={save}
        >
          Save draft
        </button>
      </div>
      {error && (
        <p role="alert" className="stats-warning">
          {error}
        </p>
      )}
      <p role="status">{notice}</p>
      {!rows.length && <p>No saved drafts yet.</p>}
      {rows.map((row) => (
        <div className="saved-row" key={row.id}>
          <div>
            <strong>{row.name}</strong>
            <small>
              {row.draft.role.toUpperCase()} ·{" "}
              {new Date(row.createdAt).toLocaleDateString()}
            </small>
          </div>
          <button
            className="text-button"
            disabled={busy}
            onClick={() => {
              onLoad(row.draft);
              setNotice(`Loaded ${row.name}.`);
            }}
          >
            Load {row.name}
          </button>
          <button
            className="text-button"
            disabled={busy}
            aria-label={`Delete ${row.name}`}
            onClick={() => remove(row.id)}
          >
            Delete
          </button>
        </div>
      ))}
    </section>
  );
}
