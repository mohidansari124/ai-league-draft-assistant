import { ExternalLink, Info } from "lucide-react";
import type { Recommendation } from "../types";
export default function Statistics({ result }: { result: Recommendation }) {
  const stats = result.statistics;
  if (!stats) return null;
  return (
    <section
      className="panel statistics-panel"
      aria-label="Recommendation statistics"
    >
      <div className="detail-heading">
        <Info size={18} />
        <h2>Observed performance</h2>
        {stats && (
          <a
            href={stats.sourceUrl}
            target="_blank"
            rel="noreferrer"
            className="text-button ml-auto"
          >
            OP.GG <ExternalLink size={12} />
          </a>
        )}
      </div>
      {stats ? (
        <>
          <div className="statistics-grid">
            <div>
              <strong>{(stats.winRate * 100).toFixed(1)}%</strong>
              <span>Match win rate</span>
            </div>
            <div>
              <strong>{stats.games.toLocaleString()}</strong>
              <span>{stats.role} games</span>
            </div>
            <div>
              <strong>{stats.patch || "Unknown"}</strong>
              <span>Provider patch</span>
            </div>
          </div>
          <p>Ranked · All ranks · Region: {stats.region}</p>
          <p>
            {stats.status === "cached"
              ? "Cached response (up to 6 hours)"
              : "Fetched from OP.GG"}{" "}
            · Retrieved {new Date(stats.fetchedAt).toLocaleString()}
          </p>
          {stats.sourceUpdatedAt && (
            <p>
              Provider update:{" "}
              {new Date(stats.sourceUpdatedAt).toLocaleString()}
            </p>
          )}
          {!stats.usedForScoring && (
            <p className="stats-warning">
              Not used for scoring or builds: patch is unknown/different, or
              sample is under 100 games.
            </p>
          )}
          <small>
            Observed outcomes, not your predicted win chance. The provider may
            round rates. Composition and situational advice remain heuristics.
          </small>
        </>
      ) : null}
    </section>
  );
}
