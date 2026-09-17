export type Role = "top" | "jungle" | "mid" | "adc" | "support";
export type Champion = {
  id: string;
  name: string;
  roles: Role[];
  archetype: string;
  physicalShare: number;
  traits: Record<string, number>;
  tags: string[];
  title: string;
  portrait: string;
};
export type Catalog = {
  champions: Champion[];
  notice: string;
  dataVersion: string;
  metadataVersion: string | null;
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
export type Recommendation = {
  champion: string;
  score: number;
  rank: number;
  factors: Factor[];
  explanation: string;
  explanationSource: string;
  matchup: {
    opponent: string | null;
    rating: string;
    known: boolean;
    explanation: string;
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
    traits: Record<string, number>;
    physicalShare: number | null;
    strengths: string[];
    needs: string[];
  };
  warnings: string[];
  excluded: string[];
  dataVersion: string;
  explanationMode: string;
};
