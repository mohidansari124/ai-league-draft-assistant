import { BookOpen, ExternalLink } from "lucide-react";
import type { Champion, Role } from "../types";

function Kit({
  champion,
  compact = false,
}: {
  champion: Champion;
  compact?: boolean;
}) {
  const kit = champion.toolkit;
  if (!kit) return null;
  return (
    <div className="champion-kit">
      <h3>
        {champion.name} <span className="muted">{kit.classes.join(" / ")}</span>
      </h3>
      <p>{kit.resource} · Level 1 base stats, before items or runes</p>
      <div className="statistics-grid">
        <div>
          <strong>{kit.stats.attackrange}</strong>
          <span>Attack range</span>
        </div>
        <div>
          <strong>{kit.stats.movespeed}</strong>
          <span>Move speed</span>
        </div>
        <div>
          <strong>{kit.stats.hp}</strong>
          <span>Health</span>
        </div>
      </div>
      <details open={!compact}>
        <summary>Abilities and passive</summary>
        {kit.abilities.map((ability) => (
          <div className="kit-ability" key={ability.key}>
            <h4>
              <span className="data-label">{ability.key}</span> {ability.name}
            </h4>
            <p>{ability.description}</p>
          </div>
        ))}
      </details>
      <a
        className="text-button"
        href={kit.sourceUrl}
        target="_blank"
        rel="noreferrer"
      >
        Riot Data Dragon source <ExternalLink size={12} />
      </a>
    </div>
  );
}

export default function ChampionToolkit({
  champion,
  opponent,
  patch,
  buildRole,
}: {
  champion?: Champion;
  opponent?: Champion;
  patch?: string | null;
  buildRole?: Role;
}) {
  if (!champion?.toolkit) return null;
  const slug =
    champion.name === "Wukong" ? "wukong" : champion.id.toLowerCase();
  return (
    <section className="panel detail-panel" aria-label="Champion reference">
      <div className="detail-heading">
        <BookOpen size={19} />
        <h2>{buildRole ? "Build research" : "Champion toolkit"}</h2>
        <span className="data-label">Riot {patch}</span>
      </div>
      {buildRole && (
        <>
          <p>
            Use these champion-specific pages to compare current item and rune
            options for your role. The links open the providers; they are not
            imported build recommendations.
          </p>
          <div className="source-actions">
            <a
              className="text-button"
              href={`https://op.gg/lol/champions/${slug}/build/${buildRole}`}
              target="_blank"
              rel="noreferrer"
            >
              OP.GG builds <ExternalLink size={12} />
            </a>
            <a
              className="text-button"
              href={`https://www.onetricks.gg/champions/builds/${champion.id}`}
              target="_blank"
              rel="noreferrer"
            >
              Onetricks builds <ExternalLink size={12} />
            </a>
          </div>
        </>
      )}
      <Kit champion={champion} compact={!!buildRole} />
      {opponent?.toolkit && <Kit champion={opponent} compact />}
      <p className="muted">
        Ability summaries describe the kit. Base stats exclude transformations,
        passive bonuses and level scaling; they do not predict who wins a
        matchup.
      </p>
    </section>
  );
}
