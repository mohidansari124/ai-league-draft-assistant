import { useEffect, useState } from "react";
import type { Champion } from "../types";

export default function Portrait({
  champion,
  large = false,
}: {
  champion?: Champion;
  large?: boolean;
}) {
  const [failed, setFailed] = useState(false);
  useEffect(() => setFailed(false), [champion?.id]);
  return (
    <span className={`portrait ${large ? "portrait-large" : ""}`}>
      {champion && !failed ? (
        <img src={champion.portrait} alt="" onError={() => setFailed(true)} />
      ) : (
        <span>{champion?.name.slice(0, 2).toUpperCase() || "?"}</span>
      )}
    </span>
  );
}
