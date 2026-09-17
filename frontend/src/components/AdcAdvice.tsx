import { BookOpen, ExternalLink } from "lucide-react";
import type { AdcAdvice as Advice } from "../types";
export default function AdcAdvice({
  advice,
  decisionsOnly = false,
}: {
  advice: Advice;
  decisionsOnly?: boolean;
}) {
  return (
    <section
      className="panel detail-panel adc-advice"
      aria-label={
        decisionsOnly ? "ADC build decisions" : "ADC matchup notebook"
      }
    >
      <div className="detail-heading">
        <BookOpen size={19} />
        <h2>{decisionsOnly ? "Before you shop" : "ADC matchup notebook"}</h2>
      </div>
      <p className="data-label">
        REVIEWED GUIDE SUMMARIES · {advice.reviewedAt}
      </p>
      {decisionsOnly ? (
        <ul>
          {advice.decisions.map((note) => (
            <li key={note}>{note}</li>
          ))}
        </ul>
      ) : (
        <>
          <h3>{advice.identity}</h3>
          <p>{advice.coverage}</p>
          {advice.notes.map((note) => (
            <article key={note.title}>
              <h3>{note.title}</h3>
              <p>{note.text}</p>
              {note.sources.map((source) => (
                <a
                  className="text-button"
                  key={source.url}
                  href={source.url}
                  target="_blank"
                  rel="noreferrer"
                >
                  {source.title} <ExternalLink size={12} />
                </a>
              ))}
            </article>
          ))}
          <p className="stats-warning">{advice.limitations}</p>
          <small>{advice.basis}</small>
        </>
      )}
    </section>
  );
}
