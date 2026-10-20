import ChampionToolkit from "./components/ChampionToolkit";
import { useEffect, useRef, useState } from "react";
import {
  ArrowLeft,
  ArrowRight,
  Check,
  CheckCheck,
  ChevronRight,
  CircleHelp,
  Crosshair,
  ExternalLink,
  Info,
  Layers3,
  LoaderCircle,
  Plus,
  RotateCcw,
  Search,
  Shield,
  Sparkles,
  Swords,
  Target,
  Trees,
  X,
  Zap,
} from "lucide-react";
import { analyzeDraft, getChampions } from "./api";
import Portrait from "./components/Portrait";
import Modal from "./components/Modal";
import Build from "./components/Build";
import AdcAdvice from "./components/AdcAdvice";
import Onetricks from "./components/Onetricks";
import SavedDrafts from "./components/SavedDrafts";
import Statistics from "./components/Statistics";
import type { Analysis, Catalog, Draft, Role } from "./types";

const ROLES: Role[] = ["top", "jungle", "mid", "adc", "support"];
const ROLE_NAMES: Record<Role, string> = {
  top: "Top",
  jungle: "Jungle",
  mid: "Mid",
  adc: "ADC",
  support: "Support",
};
const ROLE_ICONS = {
  top: Swords,
  jungle: Trees,
  mid: Sparkles,
  adc: Crosshair,
  support: Shield,
};
const DEFAULT_POOLS: Record<Role, string[]> = {
  top: ["Ornn", "Garen", "Malphite", "Mordekaiser"],
  jungle: ["Jarvan IV", "Amumu", "Vi", "Lee Sin"],
  mid: ["Orianna", "Ahri", "Syndra", "Zed"],
  adc: ["Draven", "Twitch", "Caitlyn", "Ashe"],
  support: ["Lulu", "Nautilus", "Leona", "Janna"],
};
const DEMO: Draft = {
  role: "top",
  championPool: DEFAULT_POOLS.top,
  allies: ["Jarvan IV", "Orianna", "Jinx", "Lulu"],
  enemies: ["Darius", "Lee Sin", "Zed", "Samira", "Nautilus"],
  laneOpponent: "Darius",
  comfort: {},
};
const ADC_DEMO: Draft = {
  role: "adc",
  championPool: DEFAULT_POOLS.adc,
  allies: ["Ornn", "Vi", "Orianna", "Lulu"],
  enemies: ["Garen", "Lee Sin", "Ahri", "Jhin", "Nautilus"],
  laneOpponent: "Jhin",
  comfort: {},
};
type Picker = {
  kind: "pool" | "allies" | "enemies";
  index?: number;
  label: string;
};

export default function App() {
  const [catalog, setCatalog] = useState<Catalog | null>(null);
  const [catalogError, setCatalogError] = useState("");
  const [draft, setDraft] = useState<Draft>({ ...ADC_DEMO });
  const [picker, setPicker] = useState<Picker | null>(null);
  const [search, setSearch] = useState("");
  const [help, setHelp] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [selected, setSelected] = useState(0);
  const [tab, setTab] = useState("overview");
  const [announcement, setAnnouncement] = useState(
    "Your ADC pool is loaded with an example lane. Change picks to match your game.",
  );
  const resultHeading = useRef<HTMLHeadingElement>(null);
  const fetchCatalog = () => {
    setCatalogError("");
    getChampions()
      .then(setCatalog)
      .catch((e) => setCatalogError(e.message));
  };
  useEffect(fetchCatalog, []);
  useEffect(() => {
    if (analysis) resultHeading.current?.focus();
  }, [analysis]);
  const champion = (name: string) =>
    catalog?.champions.find((c) => c.name === name);
  const allies = draft.allies.filter(Boolean);
  const enemies = draft.enemies.filter(Boolean);
  const otherRoles = ROLES.filter((r) => r !== draft.role);
  const availablePool = draft.championPool.filter(
    (n) =>
      ![...allies, ...enemies].includes(n) &&
      champion(n)?.roles.includes(draft.role),
  );
  const totals = Object.fromEntries(
    ["frontline", "engage", "peel", "control", "scaling"].map((key) => [
      key,
      allies.reduce((sum, name) => sum + (champion(name)?.traits[key] || 0), 0),
    ]),
  );
  const openPicker = (value: Picker) => {
    setSearch("");
    setPicker(value);
  };
  function changeRole(role: Role) {
    setDraft({
      role,
      championPool: DEFAULT_POOLS[role],
      allies: [],
      enemies: [],
      laneOpponent: null,
      comfort: {},
    });
    setError("");
    setAnnouncement(
      `${ROLE_NAMES[role]} selected. Draft cleared and a starter pool loaded.`,
    );
  }
  function loadExample() {
    setDraft({ ...DEMO, comfort: {} });
    setAnalysis(null);
    setError("");
    setAnnouncement("Example draft loaded. Ready to analyze.");
  }
  function choose(name: string) {
    if (!picker) return;
    if (picker.kind === "pool") {
      setDraft((d) => {
        const removing = d.championPool.includes(name);
        const comfort = { ...d.comfort };
        if (removing) delete comfort[name];
        return {
          ...d,
          comfort,
          championPool: removing
            ? d.championPool.filter((n) => n !== name)
            : [...d.championPool, name],
        };
      });
    } else {
      setDraft((d) => {
        const picks = [...d[picker.kind as "allies" | "enemies"]];
        const old = picks[picker.index!];
        picks[picker.index!] = name;
        return {
          ...d,
          [picker.kind]: picks,
          laneOpponent:
            picker.kind === "enemies" && old === d.laneOpponent
              ? null
              : d.laneOpponent,
        };
      });
      setPicker(null);
    }
    setError("");
  }
  function clearPick(kind: "allies" | "enemies", index: number) {
    setDraft((d) => {
      const picks = [...d[kind]];
      const old = picks[index];
      picks[index] = "";
      return {
        ...d,
        [kind]: picks,
        laneOpponent:
          kind === "enemies" && old === d.laneOpponent ? null : d.laneOpponent,
      };
    });
  }
  async function submit() {
    setBusy(true);
    setError("");
    try {
      const data = await analyzeDraft({ ...draft, allies, enemies });
      setAnalysis(data);
      setSelected(0);
      setTab("overview");
      window.scrollTo({ top: 0, behavior: "smooth" });
    } catch (e) {
      setError(
        e instanceof Error ? e.message : "Analysis failed. Please try again.",
      );
    } finally {
      setBusy(false);
    }
  }
  const result = analysis?.recommendations[selected];
  const blocked = (name: string) =>
    picker?.kind === "pool"
      ? [...allies, ...enemies].includes(name)
      : [...allies, ...enemies].includes(name) &&
        draft[picker!.kind as "allies" | "enemies"][picker!.index!] !== name;
  const pickerChampions =
    catalog?.champions.filter(
      (c) =>
        (picker?.kind !== "pool" || c.roles.includes(draft.role)) &&
        `${c.name} ${c.archetype}`.toLowerCase().includes(search.toLowerCase()),
    ) || [];

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <a
          className="brand"
          href="#"
          onClick={(e) => {
            e.preventDefault();
            setAnalysis(null);
          }}
        >
          <span className="brand-mark">
            <Layers3 size={23} />
          </span>
          draftwise<span className="brand-dot">.</span>
        </a>
        <div className="workspace-label">YOUR WORKSPACE</div>
        <nav aria-label="Main navigation">
          <button className="nav-item active" onClick={() => setAnalysis(null)}>
            <Layers3 size={18} /> Draft builder <ChevronRight size={15} />
          </button>
          <button className="nav-item" onClick={() => setHelp(true)}>
            <CircleHelp size={18} /> How it works
          </button>
        </nav>
        <div className="sidebar-bottom">
          <div className="sidebar-note">
            <span className="small-symbol">✧</span>
            <h3>
              A little more context.
              <br />A better next pick.
            </h3>
            <p>
              Your champion pool.
              <br />
              Your team. Your game.
            </p>
          </div>
          <a
            className="repo-link"
            href="https://github.com/mohidansari124/ai-league-draft-assistant"
            target="_blank"
            rel="noreferrer"
          >
            View project <ExternalLink size={14} />
          </a>
          <div className="course-tag">
            <span className="status-dot" /> CS4800 PROJECT <span>v0.1</span>
          </div>
        </div>
      </aside>
      <div className="workspace">
        <header className="topbar">
          <div className="breadcrumb">
            Workspace <ChevronRight size={13} />
            <span>{analysis ? "Draft analysis" : "Draft builder"}</span>
          </div>
          <div className="topbar-right">
            <span className="sample-badge">
              <span className="status-dot" />{" "}
              {catalog?.statisticsProvider === "OP.GG"
                ? "OP.GG enabled"
                : "Heuristic mode"}
            </span>
            <span className="avatar">MA</span>
          </div>
        </header>
        <main>
          {!analysis ? (
            <>
              <section className="page-intro">
                <div>
                  <div className="eyebrow">
                    <span /> THE EDGE STARTS IN CHAMP SELECT
                  </div>
                  <h1>
                    Make your next pick count<span>.</span>
                  </h1>
                  <p>
                    A familiar champion. A smarter fit. Build your draft and
                    find the pick that brings it together.
                  </p>
                </div>
                <button
                  className="button secondary example-button"
                  onClick={loadExample}
                >
                  <RotateCcw size={15} /> Load example
                </button>
              </section>
              {catalogError ? (
                <div className="error-state" role="alert">
                  <Info />
                  <h2>Let’s reconnect to the backend.</h2>
                  <p>{catalogError}</p>
                  <button className="button primary" onClick={fetchCatalog}>
                    Try again
                  </button>
                </div>
              ) : !catalog ? (
                <div className="loading-state" role="status">
                  <LoaderCircle className="spin" /> Loading champion catalog…
                </div>
              ) : (
                <div className="builder-grid">
                  <div className="builder-main">
                    <SavedDrafts
                      draft={draft}
                      onLoad={(saved) => {
                        setDraft(saved);
                        setAnalysis(null);
                        setError("");
                        setAnnouncement(
                          "Saved draft loaded. Analyze again for current results.",
                        );
                      }}
                    />
                    <section className="panel role-panel">
                      <div className="section-heading">
                        <span className="step-number">01</span>
                        <h2>Choose your role</h2>
                        <span className="heading-note">Where do you play?</span>
                      </div>
                      <div className="role-options" aria-label="Your role">
                        {ROLES.map((role) => {
                          const Icon = ROLE_ICONS[role];
                          return (
                            <button
                              key={role}
                              aria-pressed={draft.role === role}
                              onClick={() => changeRole(role)}
                              className={`role-button ${draft.role === role ? "selected" : ""}`}
                            >
                              <Icon size={20} />
                              {ROLE_NAMES[role]}
                              {draft.role === role && (
                                <span className="selected-dot" />
                              )}
                            </button>
                          );
                        })}
                      </div>
                    </section>
                    <section className="panel pool-panel">
                      <div className="section-heading">
                        <span className="step-number">02</span>
                        <h2>Your champion pool</h2>
                        <span className="count-badge">
                          {draft.championPool.length}
                        </span>
                        <button
                          className="text-button ml-auto"
                          onClick={() =>
                            openPicker({
                              kind: "pool",
                              label: "Edit your champion pool",
                            })
                          }
                        >
                          <Plus size={15} /> Edit pool
                        </button>
                      </div>
                      {draft.role === "adc" && (
                        <p className="stats-warning">
                          ADC notebook: Draven, Twitch, Caitlyn and Ashe.
                          Reviewed mechanics notes for 10 ADC opponents; all
                          champions remain selectable.
                        </p>
                      )}
                      <p className="section-description">
                        Start with champions you know. Set your comfort from 1
                        to 5.
                      </p>
                      <div className="pool-grid">
                        {draft.championPool.map((name) => (
                          <div
                            className={`pool-card ${availablePool.includes(name) ? "" : "unavailable"}`}
                            key={name}
                          >
                            <Portrait champion={champion(name)} />
                            <div className="pool-details">
                              <strong>{name}</strong>
                              <span>
                                {availablePool.includes(name)
                                  ? champion(name)?.archetype.replace("-", " ")
                                  : "Unavailable for this draft"}
                              </span>
                              <label className="comfort-label">
                                Comfort{" "}
                                <select
                                  aria-label={`${name} comfort`}
                                  value={draft.comfort[name] || 3}
                                  onChange={(e) =>
                                    setDraft((d) => ({
                                      ...d,
                                      comfort: {
                                        ...d.comfort,
                                        [name]: Number(e.target.value),
                                      },
                                    }))
                                  }
                                >
                                  {[1, 2, 3, 4, 5].map((n) => (
                                    <option key={n} value={n}>
                                      {n} / 5
                                    </option>
                                  ))}
                                </select>
                              </label>
                            </div>
                          </div>
                        ))}
                        {draft.championPool.length === 0 && (
                          <button
                            className="empty-pool"
                            onClick={() =>
                              openPicker({
                                kind: "pool",
                                label: "Add champions to your pool",
                              })
                            }
                          >
                            <Plus /> Add your first champion
                          </button>
                        )}
                      </div>
                    </section>
                    <section className="panel draft-panel">
                      <div className="section-heading">
                        <span className="step-number">03</span>
                        <h2>Build the draft</h2>
                        <span className="heading-note">
                          Partial drafts work, too
                        </span>
                      </div>
                      <div className="team-heading">
                        <span className="team-label allied">
                          <span /> YOUR TEAM
                        </span>
                        <span>{allies.length} / 4 allies selected</span>
                      </div>
                      <div className="team-grid">
                        {ROLES.map((role) => {
                          const Icon = ROLE_ICONS[role];
                          if (role === draft.role)
                            return (
                              <div key={role} className="pick-slot you-slot">
                                <Icon size={23} />
                                <strong>Your pick</strong>
                                <span>{ROLE_NAMES[role]}</span>
                                <small>We’ll find your fit</small>
                              </div>
                            );
                          const i = otherRoles.indexOf(role);
                          const name = draft.allies[i];
                          return (
                            <div className="pick-wrapper" key={role}>
                              <button
                                className={`pick-slot ${name ? "filled" : ""}`}
                                aria-label={`Select allied ${ROLE_NAMES[role]}${name ? ": " + name : ""}`}
                                onClick={() =>
                                  openPicker({
                                    kind: "allies",
                                    index: i,
                                    label: `Select allied ${ROLE_NAMES[role]}`,
                                  })
                                }
                              >
                                {name ? (
                                  <Portrait champion={champion(name)} />
                                ) : (
                                  <Plus size={24} />
                                )}
                                <strong>{name || "Add champion"}</strong>
                                <span>{ROLE_NAMES[role]}</span>
                              </button>
                              {name && (
                                <button
                                  className="remove-pick"
                                  aria-label={`Remove allied ${name}`}
                                  onClick={() => clearPick("allies", i)}
                                >
                                  <X size={12} />
                                </button>
                              )}
                            </div>
                          );
                        })}
                      </div>
                      <div className="versus-divider">
                        <span />
                        <b>VS</b>
                        <span />
                      </div>
                      <div className="team-heading">
                        <span className="team-label enemy">
                          <span /> ENEMY TEAM
                        </span>
                        <span>{enemies.length} / 5 enemies selected</span>
                      </div>
                      <div className="team-grid enemy-grid">
                        {ROLES.map((role, i) => {
                          const name = draft.enemies[i];
                          return (
                            <div className="pick-wrapper" key={role}>
                              <button
                                className={`pick-slot ${name ? "filled" : ""} ${draft.laneOpponent === name ? "lane-selected" : ""}`}
                                aria-label={`Select enemy ${ROLE_NAMES[role]}${name ? ": " + name : ""}`}
                                onClick={() =>
                                  openPicker({
                                    kind: "enemies",
                                    index: i,
                                    label: `Select enemy ${ROLE_NAMES[role]}`,
                                  })
                                }
                              >
                                {name ? (
                                  <Portrait champion={champion(name)} />
                                ) : (
                                  <Plus size={24} />
                                )}
                                <strong>{name || "Add champion"}</strong>
                                <span>{ROLE_NAMES[role]}</span>
                              </button>
                              {name && (
                                <button
                                  className="remove-pick"
                                  aria-label={`Remove enemy ${name}`}
                                  onClick={() => clearPick("enemies", i)}
                                >
                                  <X size={12} />
                                </button>
                              )}
                            </div>
                          );
                        })}
                      </div>
                      <div className="lane-row">
                        <div>
                          <Target size={17} />
                          <label htmlFor="lane-opponent">
                            Your lane opponent
                          </label>
                        </div>
                        <select
                          id="lane-opponent"
                          disabled={draft.role === "jungle"}
                          value={draft.laneOpponent || ""}
                          onChange={(e) =>
                            setDraft((d) => ({
                              ...d,
                              laneOpponent: e.target.value || null,
                            }))
                          }
                        >
                          <option value="">
                            {draft.role === "jungle"
                              ? "Not applicable for jungle"
                              : "Not selected / unknown"}
                          </option>
                          {enemies.map((name) => (
                            <option key={name} value={name}>
                              {name}
                            </option>
                          ))}
                        </select>
                      </div>
                    </section>
                  </div>
                  <aside className="summary-column">
                    <section className="panel summary-panel">
                      <div className="summary-title">
                        <span className="summary-icon">
                          <Zap size={18} />
                        </span>
                        <h2>Draft overview</h2>
                        <span className="live-label">LIVE</span>
                      </div>
                      <p className="section-description">
                        A quick read on your allies so far.
                      </p>
                      {allies.some(
                        (n) => champion(n)?.traitSource === "unrated",
                      ) && (
                        <p className="stats-warning">
                          Some allied traits are unreviewed. These bars show
                          known contributions only.
                        </p>
                      )}
                      <div className="trait-bars">
                        {[
                          ["frontline", "Frontline"],
                          ["engage", "Engage"],
                          ["peel", "Carry protection"],
                          ["control", "Crowd control"],
                          ["scaling", "Scaling"],
                        ].map(([key, label]) => (
                          <div className="trait-row" key={key}>
                            <div>
                              <span>{label}</span>
                              <small>
                                {totals[key] >=
                                (key === "scaling"
                                  ? 7
                                  : key === "control"
                                    ? 5
                                    : 4)
                                  ? "Covered"
                                  : "Room to improve"}
                              </small>
                            </div>
                            <div className="segmented-bar">
                              {Array.from({ length: 6 }, (_, i) => (
                                <span
                                  key={i}
                                  className={
                                    i < Math.min(6, Math.ceil(totals[key] / 2))
                                      ? "lit"
                                      : ""
                                  }
                                />
                              ))}
                            </div>
                          </div>
                        ))}
                      </div>
                      <div className="summary-insight">
                        <Sparkles size={17} />
                        <p>
                          {allies.length
                            ? "The best pick fills your team’s gaps without leaving your comfort zone."
                            : "Add allied picks to see what your team needs."}
                        </p>
                      </div>
                      <div className="readiness">
                        <div>
                          <Check size={15} /> {ROLE_NAMES[draft.role]} selected
                        </div>
                        <div className={!availablePool.length ? "muted" : ""}>
                          {availablePool.length ? (
                            <Check size={15} />
                          ) : (
                            <Info size={15} />
                          )}{" "}
                          {availablePool.length} available champions in pool
                        </div>
                        <div>
                          <Info size={15} /> {allies.length + enemies.length} of
                          9 other picks entered
                        </div>
                      </div>
                      {error && (
                        <p className="error-message" role="alert">
                          {error}
                        </p>
                      )}
                      <button
                        className="button primary analyze-button"
                        disabled={busy || !availablePool.length}
                        onClick={submit}
                      >
                        {busy ? (
                          <LoaderCircle size={18} className="spin" />
                        ) : (
                          <Sparkles size={18} />
                        )}
                        {busy ? "Analyzing draft…" : "Analyze draft"}
                        {!busy && <ArrowRight size={18} />}
                      </button>
                      <p className="button-caption">
                        Your top picks, with the reasoning behind them.
                      </p>
                    </section>
                    <div className="transparency-note">
                      <Shield size={19} />
                      <div>
                        <h3>Reasoning you can inspect</h3>
                        <p>
                          OP.GG statistics with transparent scoring. No API key
                          needed.
                        </p>
                        <button
                          className="text-button"
                          onClick={() => setHelp(true)}
                        >
                          See how it works <ArrowRight size={13} />
                        </button>
                      </div>
                    </div>
                    <p className="demo-note">
                      RIOT ROSTER{" "}
                      <span>
                        {catalog.champions.length} champions · Patch{" "}
                        {catalog.metadataVersion}
                      </span>
                    </p>
                  </aside>
                </div>
              )}
              <div className="draft-status" aria-live="polite">
                <CheckCheck size={14} />
                {announcement}
              </div>
            </>
          ) : (
            result && (
              <>
                <button
                  className="text-button back-button"
                  onClick={() => setAnalysis(null)}
                >
                  <ArrowLeft size={16} /> Back to draft
                </button>
                <section className="page-intro result-intro">
                  <div>
                    <div className="eyebrow">
                      <span /> YOUR DRAFT, DECODED
                    </div>
                    <h1 ref={resultHeading} tabIndex={-1}>
                      A pick with a purpose<span>.</span>
                    </h1>
                    <p>
                      Ranked from your {ROLE_NAMES[draft.role].toLowerCase()}{" "}
                      pool. Every score has a reason.
                    </p>
                  </div>
                  <span className="mode-badge">
                    <Sparkles size={14} />
                    {analysis.statisticsMode === "opgg"
                      ? "OP.GG statistics + heuristics"
                      : "Heuristic fallback"}
                  </span>
                </section>
                <div
                  className={`recommendation-grid ${analysis.recommendations.length === 4 ? "four-picks" : ""}`}
                >
                  {analysis.recommendations.map((r, i) => (
                    <button
                      className={`recommendation-card ${selected === i ? "selected" : ""}`}
                      key={r.champion}
                      onClick={() => setSelected(i)}
                      aria-pressed={selected === i}
                    >
                      <span className="rank">0{r.rank}</span>
                      <Portrait champion={champion(r.champion)} />
                      <div>
                        <small>
                          {i === 0 ? "BEST DRAFT FIT" : "ALTERNATIVE PICK"}
                        </small>
                        <strong>{r.champion}</strong>
                        <span>
                          {champion(r.champion)?.archetype.replace("-", " ")}
                        </span>
                      </div>
                      <b className="recommendation-score">
                        {r.score.toFixed(1)}
                        <small>/ 100</small>
                      </b>
                    </button>
                  ))}
                </div>
                <div className="results-layout">
                  <div>
                    <section className="panel result-hero">
                      <div className="result-hero-top">
                        <Portrait large champion={champion(result.champion)} />
                        <div>
                          <div className="eyebrow">
                            RANK #{result.rank} ·{" "}
                            {ROLE_NAMES[draft.role].toUpperCase()}
                          </div>
                          <h2>{result.champion}</h2>
                          <p>{champion(result.champion)?.title}</p>
                        </div>
                        <div className="big-score">
                          {result.score.toFixed(1)}
                          <span>DRAFT FIT / 100</span>
                        </div>
                      </div>
                      <div className="why-label">
                        <Sparkles size={15} /> WHY IT WORKS{" "}
                        <span>
                          {result.explanationSource === "openai"
                            ? "AI explanation"
                            : "Rule-based explanation"}
                        </span>
                      </div>
                      <p className="explanation">{result.explanation}</p>
                    </section>
                    <Statistics result={result} />
                    {result.onetricks && (
                      <Onetricks evidence={result.onetricks} />
                    )}
                    <div
                      className="result-tabs"
                      role="tablist"
                      aria-label="Recommendation details"
                    >
                      {[
                        ["overview", "Game plan"],
                        ["build", "Build & runes"],
                        ["score", "Score breakdown"],
                      ].map(([value, label]) => (
                        <button
                          key={value}
                          id={`tab-${value}`}
                          role="tab"
                          aria-selected={tab === value}
                          aria-controls="detail-panel"
                          onClick={() => setTab(value)}
                        >
                          {label}
                        </button>
                      ))}
                    </div>
                    <div
                      id="detail-panel"
                      role="tabpanel"
                      aria-labelledby={`tab-${tab}`}
                    >
                      {tab === "overview" && (
                        <>
                          {result.matchup.known && (
                            <section className="panel detail-panel">
                              <div className="detail-heading">
                                <Target size={19} />
                                <h2>Lane matchup</h2>
                                <span
                                  className={`matchup-badge ${result.matchup.rating === "Difficult" ? "difficult" : ""}`}
                                >
                                  {result.matchup.rating}
                                </span>
                              </div>
                              <h3>
                                {result.champion}{" "}
                                <span className="muted">vs.</span>{" "}
                                {result.matchup.opponent || "Unknown opponent"}
                              </h3>
                              <p>{result.matchup.explanation}</p>
                              <span className="data-label">
                                {result.matchup.known
                                  ? result.matchup.source === "OP.GG"
                                    ? "OP.GG match outcomes · not lane-win statistics"
                                    : "Historical sample matchup · not statistical data"
                                  : "Unrated matchup · neutral scoring applied"}
                              </span>
                            </section>
                          )}
                          <ChampionToolkit
                            champion={champion(result.champion)}
                            opponent={champion(result.matchup.opponent || "")}
                            patch={catalog?.metadataVersion}
                          />
                          {result.adcAdvice && (
                            <AdcAdvice advice={result.adcAdvice} />
                          )}
                          <section className="panel detail-panel">
                            <div className="detail-heading">
                              <Layers3 size={19} />
                              <h2>Your game plan</h2>
                              <span className="data-label">
                                HEURISTIC ADVICE
                              </span>
                            </div>
                            <ol className="game-plan">
                              {(result.adcAdvice
                                ? [
                                    result.adcAdvice.notes[0].text,
                                    result.adcAdvice.notes[
                                      result.adcAdvice.notes.length - 1
                                    ].text,
                                  ]
                                : result.gamePlan
                              ).map((step, i) => (
                                <li key={i}>
                                  <span>0{i + 1}</span>
                                  <div>
                                    <h3>
                                      {
                                        [
                                          "Play the early game",
                                          "Find your moment",
                                          "Close together",
                                        ][i]
                                      }
                                    </h3>
                                    <p>{step}</p>
                                  </div>
                                </li>
                              ))}
                            </ol>
                          </section>
                        </>
                      )}
                      {tab === "build" && (
                        <>
                          <Build result={result} />
                          <ChampionToolkit
                            champion={champion(result.champion)}
                            patch={catalog?.metadataVersion}
                            buildRole={draft.role}
                          />
                        </>
                      )}
                      {tab === "score" && (
                        <section className="panel detail-panel">
                          <div className="detail-heading">
                            <Layers3 size={19} />
                            <h2>Every point, explained</h2>
                          </div>
                          <p>
                            Eleven weighted factors add up to 100. This is a fit
                            score, not a win rate.
                          </p>
                          <div className="factor-list">
                            {result.factors.map((f) => (
                              <div className="factor" key={f.key}>
                                <div>
                                  <strong>{f.label}</strong>
                                  <b>
                                    {f.points.toFixed(1)}{" "}
                                    <span>/ {f.maximum}</span>
                                  </b>
                                </div>
                                <div className="meter">
                                  <span
                                    style={{
                                      width: `${(f.points / f.maximum) * 100}%`,
                                    }}
                                  />
                                </div>
                                <p>{f.reason}</p>
                              </div>
                            ))}
                          </div>
                        </section>
                      )}
                    </div>
                  </div>
                  <aside className="results-side">
                    <section className="panel detail-panel">
                      <div className="detail-heading">
                        <Shield size={19} />
                        <h2>Team composition</h2>
                      </div>
                      <p>Allied picks before your selection.</p>
                      <h3 className="small-heading">ALREADY COVERED</h3>
                      <div className="tag-list">
                        {analysis.composition.strengths.length ? (
                          analysis.composition.strengths.map((s) => (
                            <span key={s}>
                              <Check size={12} />
                              {s}
                            </span>
                          ))
                        ) : (
                          <p>More picks needed to establish strengths.</p>
                        )}
                      </div>
                      <h3 className="small-heading">OPPORTUNITIES TO FILL</h3>
                      <div className="tag-list needs">
                        {analysis.composition.needs.map((n) => (
                          <span key={n}>{n}</span>
                        ))}
                      </div>
                      {analysis.composition.unratedChampions.length > 0 && (
                        <p className="stats-warning">
                          Incomplete trait coverage:{" "}
                          {analysis.composition.unratedChampions.join(", ")}.
                          Unreviewed traits are not zero strength.
                        </p>
                      )}
                      {analysis.composition.physicalShare !== null && (
                        <div className="damage-mix">
                          <div>
                            <span>Physical</span>
                            <span>Magic</span>
                          </div>
                          <div className="damage-bar">
                            <span
                              style={{
                                width: `${analysis.composition.physicalShare * 100}%`,
                              }}
                            />
                          </div>
                          <div>
                            <b>
                              {Math.round(
                                analysis.composition.physicalShare * 100,
                              )}
                              %
                            </b>
                            <b>
                              {Math.round(
                                (1 - analysis.composition.physicalShare) * 100,
                              )}
                              %
                            </b>
                          </div>
                          <small>
                            Illustrative profiles, equally weighted.
                          </small>
                        </div>
                      )}
                    </section>
                    <section className="analysis-notes">
                      <div>
                        <Info size={17} />
                        <h3>Keep the context</h3>
                      </div>
                      {analysis.warnings.map((w) => (
                        <p key={w}>{w}</p>
                      ))}
                    </section>
                  </aside>
                </div>
              </>
            )
          )}
          <footer>
            <span>Built for better decisions, not guaranteed wins.</span>
            <span>Draftwise · AI League Draft Assistant</span>
            <p>
              Draftwise is not endorsed by Riot Games and does not reflect the
              views or opinions of Riot Games or anyone officially involved in
              producing or managing Riot Games properties. Riot Games and all
              associated properties are trademarks or registered trademarks of
              Riot Games, Inc.
            </p>
          </footer>
        </main>
      </div>
      {picker && (
        <Modal title={picker.label} close={() => setPicker(null)}>
          <div className="picker-body">
            <div className="search-field">
              <Search size={18} />
              <input
                autoFocus
                placeholder="Search champions…"
                aria-label="Search champions"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
            <div className="picker-subtitle">
              <span>
                {picker.kind === "pool"
                  ? `${ROLE_NAMES[draft.role]} champions · select multiple`
                  : "All supported champions · already-picked champions are disabled"}
              </span>
              <span>{pickerChampions.length} available in catalog</span>
            </div>
            <div className="champion-picker">
              {pickerChampions.map((c) => (
                <button
                  key={c.name}
                  disabled={blocked(c.name)}
                  aria-pressed={
                    picker.kind === "pool"
                      ? draft.championPool.includes(c.name)
                      : undefined
                  }
                  className={
                    picker.kind === "pool" &&
                    draft.championPool.includes(c.name)
                      ? "chosen"
                      : ""
                  }
                  onClick={() => choose(c.name)}
                >
                  <Portrait champion={c} />
                  <span>
                    <strong>{c.name}</strong>
                    <small>
                      {blocked(c.name)
                        ? "Already picked"
                        : c.roles.map((r) => ROLE_NAMES[r]).join(" / ")}
                    </small>
                  </span>
                  {picker.kind === "pool" &&
                    draft.championPool.includes(c.name) && <Check size={16} />}
                </button>
              ))}
            </div>
            {!pickerChampions.length && (
              <p className="no-results">
                No matching champions in the Riot roster.
              </p>
            )}
            <div className="picker-footer">
              <small>
                Riot roster · {catalog?.champions.length || 0} champions
              </small>
              <button
                className="button primary"
                onClick={() => setPicker(null)}
              >
                Done <Check size={15} />
              </button>
            </div>
          </div>
        </Modal>
      )}
      {help && (
        <Modal
          title="How Draftwise makes a recommendation"
          close={() => setHelp(false)}
        >
          <div className="help-body">
            <span className="mode-badge">TRANSPARENT BY DESIGN</span>
            <h3>Game data → scoring → explanations</h3>
            <p>
              The engine filters your pool by role and availability, then scores
              every eligible champion on eleven factors. Your top three picks
              are sorted by total score, with alphabetical tie-breaking.
            </p>
            <div className="help-weights">
              {[
                ["Observed role performance", 10],
                ["Lane matchup", 20],
                ["Your comfort", 15],
                ["Frontline", 8],
                ["Damage balance", 8],
                ["Enemy threats", 9],
                ["Engage", 6],
                ["Carry protection", 6],
                ["Crowd control", 6],
                ["Scaling", 6],
                ["Ally synergy", 6],
              ].map(([label, weight]) => (
                <div key={label}>
                  <span>{label}</span>
                  <b>{weight} pts</b>
                </div>
              ))}
            </div>
            <p>
              Unknown matchups earn neutral credit. Team traits earn bonuses for
              filling gaps. Comfort defaults to 3 / 5 and can be changed on each
              champion card.
            </p>
            <p>
              <strong>Real statistics, explicit limits.</strong> The full Riot
              roster is available. OP.GG supplies role performance, selected
              matchup samples, observed builds and runes. Only matching-patch
              samples with at least 100 games affect scores; small samples are
              shrunk toward neutral. The API does not expose its region filter.
              Composition traits and situational advice remain heuristics;
              unreviewed traits receive neutral credit.
            </p>
            <p>
              The app fetches statistics without an API key and falls back
              safely when offline. An optional AI service can explain the same
              scored facts; it never controls the rankings or builds.
            </p>
            <button className="button primary" onClick={() => setHelp(false)}>
              Got it <Check size={16} />
            </button>
          </div>
        </Modal>
      )}
    </div>
  );
}
