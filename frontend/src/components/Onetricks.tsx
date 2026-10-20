import { ExternalLink, BookOpen } from "lucide-react";
import type { OnetricksEvidence } from "../types";
export default function Onetricks({
  evidence,
}: {
  evidence: OnetricksEvidence;
}) {
  return (
    <section
      className="panel detail-panel adc-advice"
      aria-label="Onetricks matchup evidence"
    >
      <div className="detail-heading">
        <BookOpen size={19} />
        <h2>Onetricks matchup evidence</h2>
      </div>
      <p>{evidence.notice}</p>
      {!evidence.records.length && (
        <p className="stats-warning">
          {evidence.opponent
            ? `No imported evidence for this pick against ${evidence.opponent}.`
            : "Select an opposing ADC to look up imported evidence."}{" "}
          Overall OP.GG builds remain separate.
        </p>
      )}
      {evidence.records.map((record, i) => (
        <article key={`${record.sourceUrl}-${record.observedAt}-${i}`}>
          <h3>
            {record.champion} vs. {record.opponent}
          </h3>
          <p className="data-label">
            {record.cohort} · ADC · {record.region}
          </p>
          {record.winRate !== null && (
            <div className="statistics-grid">
              <div>
                <strong>{(record.winRate * 100).toFixed(1)}%</strong>
                <span>{record.champion} match wins</span>
              </div>
              <div>
                <strong>{record.games?.toLocaleString()}</strong>
                <span>Matchup games</span>
              </div>
              <div>
                <strong>
                  {record.goldDiff15 === null
                    ? "—"
                    : Math.round(record.goldDiff15).toLocaleString()}
                </strong>
                <span>{record.champion} gold diff @15</span>
              </div>
            </div>
          )}
          <p>
            Patch: {record.patch || "Unknown"} · Reviewed{" "}
            {new Date(record.observedAt).toLocaleDateString()} ·{" "}
            {record.freshness}
          </p>
          <p>{record.notes}</p>
          {record.reportedPerspective === "opponent" && (
            <p>
              Converted from the opponent’s reported win rate and gold
              difference to {record.champion}’s perspective.
            </p>
          )}
          {record.build ? (
            <>
              <h3>Imported matchup build</h3>
              <p>
                {record.build.items.join(" → ")} · {record.build.games} build
                observations
              </p>
              {record.build.runes && (
                <p>
                  Runes: {record.build.runes.keystone} ·{" "}
                  {record.build.runes.primary} / {record.build.runes.secondary}{" "}
                  · {record.build.runes.runes.join(", ")} · Shards:{" "}
                  {record.build.runes.shards.join(", ")}
                </p>
              )}
              <p className="stats-warning">
                {record.buildEligible
                  ? "Meets local patch, sample and review-age checks. This is specialist build evidence, not proof of the best purchase order."
                  : "Reference only: patch differs/is unknown, review is older than seven days, or build sample is below 100."}
              </p>
            </>
          ) : (
            <p className="stats-warning">
              No verified matchup-specific item or rune record in this
              observation.
            </p>
          )}
          <a
            className="text-button"
            href={record.sourceUrl}
            target="_blank"
            rel="noreferrer"
          >
            View observation source <ExternalLink size={12} />
          </a>
        </article>
      ))}
      <div className="source-actions">
        <a
          className="text-button"
          href={evidence.counterUrl}
          target="_blank"
          rel="noreferrer"
        >
          Onetricks counters <ExternalLink size={12} />
        </a>
        <a
          className="text-button"
          href={evidence.buildUrl}
          target="_blank"
          rel="noreferrer"
        >
          Onetricks builds — choose matchup <ExternalLink size={12} />
        </a>
      </div>
    </section>
  );
}
