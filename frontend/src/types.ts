export type Role = "top" | "jungle" | "mid" | "adc" | "support";
export type Champion = {
  id: string;
  name: string;
  roles: Role[];
  archetype: string;
  physicalShare: number | null;
  traits: Record<string, number | null>;
  tags: string[];
  title: string;
  portrait: string;
  traitSource: string;
  roleSource: string;
};
export type Catalog = {
  champions: Champion[];
  notice: string;
  dataVersion: string;
  metadataVersion: string | null;
  statisticsProvider: string;
};
export type Draft = {
  role: Role;
  championPool: string[];
  allies: string[];
  enemies: string[];
  laneOpponent: string | null;
  comfort: Record<string, number>;
};
export type Factor = {
  key: string;
  label: string;
  points: number;
  maximum: number;
  reason: string;
};
export type AdcAdvice = {
  identity: string;
  reviewedAt: string;
  basis: string;
  opponentCovered: boolean;
  coverage: string;
  notes: {
    title: string;
    text: string;
    sources: { title: string; url: string }[];
  }[];
  decisions: string[];
  limitations: string;
};
export type Recommendation = {
  adcAdvice: AdcAdvice | null;
  champion: string;
  score: number;
  rank: number;
  factors: Factor[];
  explanation: string;
  explanationSource: string;
  statistics: ChampionStatistics | null;
  buildSource: string;
  runeSource: string;
  traitSource: string;
  matchup: {
    opponent: string | null;
    rating: string;
    known: boolean;
    explanation: string;
    source: string;
    winRate: number | null;
    games: number | null;
  };
  runes: {
    primary: string;
    secondary: string;
    keystone: string;
    runes: string[];
    shards: string[];
  };
  coreItems: { name: string; reason: string }[];
  situationalItems: { name: string; reason: string }[];
  gamePlan: string[];
};
export type Analysis = {
  recommendations: Recommendation[];
  composition: {
    traits: Record<string, number | null>;
    physicalShare: number | null;
    strengths: string[];
    needs: string[];
    unratedChampions: string[];
  };
  warnings: string[];
  excluded: string[];
  dataVersion: string;
  explanationMode: string;
  statisticsMode: string;
};

export type ChampionStatistics = {
  source: string;
  sourceUrl: string;
  role: string;
  patch: string | null;
  tier: string;
  region: string;
  queue: string;
  winRate: number;
  games: number;
  fetchedAt: string;
  sourceUpdatedAt: string | null;
  status: string;
  usedForScoring: boolean;
};
