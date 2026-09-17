import { Sparkles, Layers3, Shield, Plus } from "lucide-react";
import AdcAdvice from "./AdcAdvice";
import type { Recommendation } from "../types";

export default function Build({ result }: { result: Recommendation }) {
  return (
    <>
      {result.adcAdvice && (
        <AdcAdvice advice={result.adcAdvice} decisionsOnly />
      )}
      <section className="panel detail-panel">
        <div className="detail-heading">
          <Sparkles size={19} />
          <h2>Rune page</h2>
          <span className="data-label">{result.runeSource}</span>
        </div>
        <div className="rune-page">
          <div className="keystone">
            <span className="rune-symbol">✧</span>
            <small>{result.runes.primary}</small>
            <h3>{result.runes.keystone}</h3>
          </div>
          <div className="rune-trees">
            <h3>{result.runes.primary}</h3>
            {result.runes.runes.slice(0, 3).map((r) => (
              <p key={r}>
                <span />
                {r}
              </p>
            ))}
            <h3>{result.runes.secondary}</h3>
            {result.runes.runes.slice(3).map((r) => (
              <p key={r}>
                <span />
                {r}
              </p>
            ))}
          </div>
        </div>
        <div className="shards">
          {result.runes.shards.map((s, i) => (
            <span key={i}>{s}</span>
          ))}
        </div>
      </section>
      <section className="panel detail-panel">
        <div className="detail-heading">
          <Layers3 size={19} />
          <h2>Core items</h2>
          <span className="data-label">{result.buildSource}</span>
        </div>
        <p>
          {result.coreItems.length
            ? "Adapt the observed or sample build to your game; item completion depends on gold and game length."
            : "No verified build was returned for this champion. No item recommendations have been invented."}
        </p>
        <div className="item-list">
          {result.coreItems.map((item, i) => (
            <div key={item.name}>
              <span className="item-number">0{i + 1}</span>
              <div>
                <h3>{item.name}</h3>
                <p>{item.reason}</p>
              </div>
            </div>
          ))}
        </div>
      </section>
      <section className="panel detail-panel">
        <div className="detail-heading">
          <Shield size={19} />
          <h2>Situational choices</h2>
          <span className="data-label">HEURISTIC ADVICE</span>
        </div>
        {result.situationalItems.length ? (
          <div className="item-list">
            {result.situationalItems.map((item) => (
              <div key={item.name}>
                <span className="item-number">
                  <Plus size={16} />
                </span>
                <div>
                  <h3>{item.name}</h3>
                  <p>{item.reason}</p>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p>
            No additional reviewed situational suggestions are available.
            Reassess defensive items as the game develops.
          </p>
        )}
      </section>
    </>
  );
}
