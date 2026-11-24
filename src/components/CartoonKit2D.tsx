import React, { useId } from "react";
import { loadFont as loadCaveat } from "@remotion/google-fonts/Caveat";
import { loadFont as loadPermanentMarker } from "@remotion/google-fonts/PermanentMarker";
import { loadFont as loadSpaceGrotesk } from "@remotion/google-fonts/SpaceGrotesk";
import { interpolate, spring, useVideoConfig } from "remotion";
import type { BackdropTheme, CameraMove2D } from "../types";

const { fontFamily: HAND_FONT } = loadCaveat("normal", { weights: ["700"], subsets: ["latin"] });
const { fontFamily: MARKER_FONT } = loadPermanentMarker("normal", { weights: ["400"], subsets: ["latin"] });
const { fontFamily: UI_FONT } = loadSpaceGrotesk("normal", { weights: ["600", "700"], subsets: ["latin"] });

const INK = "#111827";

export const SceneBackdrop2D: React.FC<{
  theme: BackdropTheme;
  frame: number;
  accentHex?: string;
}> = ({ theme, frame, accentHex = "#22C55E" }) => {
  const uid = useId().replace(/:/g, "");
  const gradId = `bg_${uid}`;
  const cloudDrift = (frame * 0.45) % 2100;

  if (theme === "black_title_card") {
    return <rect x={-100} y={-100} width={2200} height={2200} fill="#05070B" />;
  }

  if (theme === "night_mountains") {
    return (
      <g>
        <defs>
          <linearGradient id={gradId} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#09111E" />
            <stop offset="68%" stopColor="#142A3E" />
            <stop offset="100%" stopColor="#1D3E4D" />
          </linearGradient>
        </defs>
        <rect x={-100} y={-100} width={2200} height={2200} fill={`url(#${gradId})`} />
        {[
          [180, 140], [420, 90], [690, 200], [980, 110], [1340, 160], [1680, 100], [1810, 240], [310, 320], [1510, 290],
        ].map(([sx, sy], i) => {
          const tw = 0.35 + 0.65 * Math.abs(Math.sin(frame * 0.05 + i));
          return <circle key={i} cx={sx} cy={sy} r={3 + (i % 2)} fill="#E2E8F0" opacity={tw} />;
        })}
        <polygon points="-50,920 260,640 540,860 890,560 1240,840 1580,620 1980,900 1980,2000 -50,2000" fill="#0F1F2E" stroke={INK} strokeWidth={4} />
        <rect x={-50} y={840} width={2050} height={1200} fill="#182538" stroke={INK} strokeWidth={4} />
      </g>
    );
  }

  if (theme === "sunset_horizon") {
    return (
      <g>
        <defs>
          <linearGradient id={gradId} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#D97762" />
            <stop offset="55%" stopColor="#F4B27A" />
            <stop offset="100%" stopColor="#FDE2A6" />
          </linearGradient>
        </defs>
        <rect x={-100} y={-100} width={2200} height={2200} fill={`url(#${gradId})`} />
        <circle cx={340} cy={310} r={115} fill="#FEF3C7" stroke="#F59E0B" strokeWidth={5} />
        <ellipse cx={(200 + cloudDrift) % 2100 - 100} cy={220} rx={120} ry={34} fill="#FFEAD5" opacity={0.85} />
        <ellipse cx={(1100 + cloudDrift * 0.7) % 2100 - 100} cy={170} rx={150} ry={38} fill="#FFEAD5" opacity={0.75} />
        <polygon points="-40,860 360,560 720,780 1120,520 1540,790 1980,580 1980,2000 -40,2000" fill="#B57B6B" stroke={INK} strokeWidth={4} />
        <rect x={-50} y={820} width={2050} height={1200} fill="#C69262" stroke={INK} strokeWidth={4} />
      </g>
    );
  }

  if (theme === "daylight_city" || theme === "split_3panel") {
    return (
      <g>
        <rect x={-100} y={-100} width={2200} height={2200} fill="#CBE4F5" />
        <ellipse cx={(300 + cloudDrift) % 2100 - 100} cy={180} rx={130} ry={40} fill="#FFFFFF" opacity={0.9} />
        <ellipse cx={(1250 + cloudDrift * 0.6) % 2100 - 100} cy={130} rx={160} ry={44} fill="#FFFFFF" opacity={0.85} />
        <rect x={-50} y={820} width={2050} height={1200} fill="#9CA3AF" stroke={INK} strokeWidth={4} />
      </g>
    );
  }

  if (theme === "graph_paper") {
    return (
      <g>
        <rect x={-100} y={-100} width={2200} height={2200} fill="#EAE6DC" />
        {Array.from({ length: 28 }).map((_, i) => (
          <line key={`v${i}`} x1={i * 80} y1={-50} x2={i * 80} y2={2000} stroke="#D4CFC2" strokeWidth={2} />
        ))}
        {Array.from({ length: 26 }).map((_, i) => (
          <line key={`h${i}`} x1={-50} y1={i * 80} x2={2000} y2={i * 80} stroke="#D4CFC2" strokeWidth={2} />
        ))}
      </g>
    );
  }

  if (theme === "notebook_lined") {
    return (
      <g>
        <rect x={-100} y={-100} width={2200} height={2200} fill="#F7F3E9" />
        <line x1={210} y1={-50} x2={210} y2={2000} stroke="#EF4444" strokeWidth={4} opacity={0.55} />
        {Array.from({ length: 28 }).map((_, i) => (
          <line key={i} x1={-50} y1={120 + i * 68} x2={2000} y2={120 + i * 68} stroke="#93C5FD" strokeWidth={2} opacity={0.65} />
        ))}
      </g>
    );
  }

  if (theme === "world_map") {
    return (
      <g>
        <rect x={-100} y={-100} width={2200} height={2200} fill="#8FB5C9" />
        {Array.from({ length: 14 }).map((_, i) => (
          <line key={`g${i}`} x1={i * 160} y1={-50} x2={i * 160} y2={2000} stroke="#7CA3B8" strokeWidth={2} strokeDasharray="8 8" />
        ))}
      </g>
    );
  }

  if (theme === "warm_office") {
    return (
      <g>
        <rect x={-100} y={-100} width={2200} height={2200} fill="#C9B99F" />
        <rect x={120} y={90} width={380} height={280} fill="#BAE6FD" stroke={INK} strokeWidth={5} />
        <line x1={310} y1={90} x2={310} y2={370} stroke={INK} strokeWidth={4} />
        <rect x={-50} y={760} width={2050} height={1200} fill="#6F4E37" stroke={INK} strokeWidth={5} />
      </g>
    );
  }

  if (theme === "steel_vault") {
    return (
      <g>
        <rect x={-100} y={-100} width={2200} height={2200} fill="#374151" />
        <polygon points="960,-40 240,1200 1680,1200" fill="#FDE68A" opacity={0.14} />
        <rect x={-50} y={840} width={2050} height={1200} fill="#1F2937" stroke={INK} strokeWidth={5} />
      </g>
    );
  }

  if (theme === "news_document") {
    return (
      <g>
        <rect x={-100} y={-100} width={2200} height={2200} fill="#CBD5E1" />
        <rect x={140} y={100} width={1640} height={880} rx={14} fill="#F8FAFC" stroke={INK} strokeWidth={5} />
      </g>
    );
  }

  // dark_industrial default
  return (
    <g>
      <rect x={-100} y={-100} width={2200} height={2200} fill="#1E293B" />
      {[280, 680, 1240, 1640].map((lx, i) => (
        <rect key={i} x={lx - 80} y={40} width={160} height={24} rx={8} fill={accentHex} opacity={0.85} stroke={INK} strokeWidth={3} />
      ))}
      <rect x={-50} y={840} width={2050} height={1200} fill="#334155" stroke={INK} strokeWidth={5} />
      <rect x={-50} y={840} width={2050} height={26} fill="#F59E0B" stroke={INK} strokeWidth={3} />
    </g>
  );
};

export const Camera2D: React.FC<{
  move: CameraMove2D;
  progress: number;
  frame: number;
  peakTimes?: number[];
  localTime: number;
  children?: React.ReactNode;
}> = ({ move, progress, frame, peakTimes = [], localTime, children }) => {
  const ease = progress * progress * (3 - 2 * progress);
  let scale = 1;
  let tx = 0;
  let ty = 0;

  if (move === "push_in") {
    scale = 1 + ease * 0.08;
  } else if (move === "pull_out") {
    scale = 1.09 - ease * 0.09;
  } else if (move === "pan_right") {
    scale = 1.05;
    tx = 32 - ease * 64;
  } else if (move === "pan_left") {
    scale = 1.05;
    tx = -32 + ease * 64;
  } else if (move === "pan_up") {
    scale = 1.05;
    ty = 26 - ease * 52;
  } else if (move === "shake_hit") {
    scale = 1.04;
  }

  // Punchy human-edited camera impact jolt on vocal emphasis peaks
  let shakeX = 0;
  let shakeY = 0;
  for (const pt of peakTimes) {
    const dt = localTime - pt;
    if (dt >= 0 && dt < 0.28) {
      const decay = 1 - dt / 0.28;
      shakeX += Math.sin(frame * 2.7) * 9 * decay;
      shakeY += Math.cos(frame * 3.1) * 7 * decay;
    }
  }

  const cx = 960;
  const cy = 540;
  const xform = `translate(${cx + tx + shakeX} ${cy + ty + shakeY}) scale(${scale}) translate(${-cx} ${-cy})`;

  return <g transform={xform}>{children}</g>;
};

export const CartoonCharacter2D: React.FC<{
  x: number;
  y: number;
  scale?: number;
  variant?: "ceo" | "engineer" | "worker" | "suit" | "operator";
  mood?: "neutral" | "shocked" | "worried" | "happy" | "smug" | "angry";
  pose?: "stand" | "point_right" | "point_up" | "hold_up" | "hands_head" | "celebrate";
  glasses?: boolean;
  hardHat?: boolean;
  sweatDrop?: boolean;
  flip?: boolean;
  frame: number;
}> = ({
  x,
  y,
  scale = 1,
  variant = "engineer",
  mood = "neutral",
  pose = "stand",
  glasses = false,
  hardHat = false,
  sweatDrop = false,
  flip = false,
  frame,
}) => {
  const bob = Math.sin(frame * 0.1) * 4;
  const blink = frame % 95 >= 91;
  const wave = Math.sin(frame * 0.16) * 8;
  const dir = flip ? -1 : 1;

  const outfitMap: Record<string, string> = {
    ceo: "#1F2937",
    engineer: "#2563EB",
    worker: "#EA580C",
    suit: "#334155",
    operator: "#059669",
  };
  const bodyColor = outfitMap[variant] || "#2563EB";
  const hairColor = variant === "ceo" ? "#CBD5E1" : "#374151";
  const skinColor = "#F3C69F";
  const sweatY = ((frame * 2.4) % 34);

  return (
    <g transform={`translate(${x} ${y + bob}) scale(${scale * dir} ${scale})`}>
      {/* Ground Shadow */}
      <ellipse cx={0} cy={175} rx={58} ry={14} fill="#000000" opacity={0.28} />
      {/* Stick Legs */}
      <line x1={-18} y1={105} x2={-22} y2={170} stroke={INK} strokeWidth={7} strokeLinecap="round" />
      <line x1={18} y1={105} x2={22} y2={170} stroke={INK} strokeWidth={7} strokeLinecap="round" />
      {/* Torso */}
      <rect x={-46} y={-22} width={92} height={132} rx={44} fill={bodyColor} stroke={INK} strokeWidth={5} />
      {variant === "suit" || variant === "ceo" ? (
        <polygon points="-14,-20 14,-20 6,42 -6,42" fill="#E11D48" stroke={INK} strokeWidth={3} />
      ) : null}

      {/* Stick Arms by Pose */}
      {pose === "point_right" ? (
        <>
          <line x1={-44} y1={18} x2={-78} y2={62} stroke={INK} strokeWidth={6} strokeLinecap="round" />
          <line x1={44} y1={16} x2={115} y2={-6 + wave * 0.5} stroke={INK} strokeWidth={6} strokeLinecap="round" />
        </>
      ) : pose === "point_up" || pose === "hold_up" ? (
        <>
          <line x1={-44} y1={18} x2={-72} y2={-68 + wave * 0.4} stroke={INK} strokeWidth={6} strokeLinecap="round" />
          <line x1={44} y1={18} x2={72} y2={-68 + wave * 0.4} stroke={INK} strokeWidth={6} strokeLinecap="round" />
        </>
      ) : pose === "hands_head" ? (
        <>
          <path d="M -44 16 Q -90 -30 -56 -80" fill="none" stroke={INK} strokeWidth={6} strokeLinecap="round" />
          <path d="M 44 16 Q 90 -30 56 -80" fill="none" stroke={INK} strokeWidth={6} strokeLinecap="round" />
        </>
      ) : pose === "celebrate" ? (
        <>
          <line x1={-44} y1={18} x2={-86} y2={-52 + wave} stroke={INK} strokeWidth={6} strokeLinecap="round" />
          <line x1={44} y1={18} x2={86} y2={-52 - wave} stroke={INK} strokeWidth={6} strokeLinecap="round" />
        </>
      ) : (
        <>
          <line x1={-44} y1={18} x2={-72} y2={68 + wave * 0.3} stroke={INK} strokeWidth={6} strokeLinecap="round" />
          <line x1={44} y1={18} x2={72} y2={68 - wave * 0.3} stroke={INK} strokeWidth={6} strokeLinecap="round" />
        </>
      )}

      {/* Oval Cartoon Head */}
      <circle cx={0} cy={-78} r={54} fill={skinColor} stroke={INK} strokeWidth={5} />
      {/* Hair */}
      <path d="M -52 -88 Q -42 -142 0 -138 Q 42 -142 52 -88 Q 22 -106 0 -100 Q -22 -106 -52 -88 Z" fill={hairColor} stroke={INK} strokeWidth={4} />

      {/* Hard Hat */}
      {hardHat && (
        <g>
          <path d="M -54 -96 Q -48 -150 0 -150 Q 48 -150 54 -96 Z" fill="#FACC15" stroke={INK} strokeWidth={5} />
          <rect x={-64} y={-98} width={128} height={14} rx={7} fill="#EAB308" stroke={INK} strokeWidth={4} />
        </g>
      )}

      {/* Eyes (with automatic blink) */}
      {blink ? (
        <>
          <line x1={-24} y1={-80} x2={-10} y2={-80} stroke={INK} strokeWidth={4} strokeLinecap="round" />
          <line x1={10} y1={-80} x2={24} y2={-80} stroke={INK} strokeWidth={4} strokeLinecap="round" />
        </>
      ) : (
        <>
          <circle cx={-16} cy={-80} r={mood === "shocked" ? 8 : 5.5} fill={INK} />
          <circle cx={16} cy={-80} r={mood === "shocked" ? 8 : 5.5} fill={INK} />
        </>
      )}

      {/* Glasses */}
      {glasses && (
        <g>
          <rect x={-32} y={-92} width={28} height={22} rx={5} fill="none" stroke={INK} strokeWidth={3.5} />
          <rect x={4} y={-92} width={28} height={22} rx={5} fill="none" stroke={INK} strokeWidth={3.5} />
          <line x1={-4} y1={-81} x2={4} y2={-81} stroke={INK} strokeWidth={3.5} />
        </g>
      )}

      {/* Eyebrows + Mouth by Mood */}
      {mood === "shocked" ? (
        <ellipse cx={0} cy={-50} rx={11} ry={14} fill="#7F1D1D" stroke={INK} strokeWidth={3.5} />
      ) : mood === "worried" || mood === "angry" ? (
        <>
          <line x1={-28} y1={-96} x2={-8} y2={-91} stroke={INK} strokeWidth={4} strokeLinecap="round" />
          <line x1={8} y1={-91} x2={28} y2={-96} stroke={INK} strokeWidth={4} strokeLinecap="round" />
          <path d="M -16 -46 Q 0 -60 16 -46" fill="none" stroke={INK} strokeWidth={4.5} strokeLinecap="round" />
        </>
      ) : mood === "happy" || mood === "smug" ? (
        <path d="M -18 -56 Q 0 -38 18 -56" fill="#FFFFFF" stroke={INK} strokeWidth={4} strokeLinecap="round" />
      ) : (
        <line x1={-14} y1={-52} x2={14} y2={-52} stroke={INK} strokeWidth={4.5} strokeLinecap="round" />
      )}

      {/* Animated Sweat Drop */}
      {sweatDrop && (
        <path
          d={`M ${-48} ${-108 + sweatY} Q ${-56} ${-92 + sweatY} ${-48} ${-86 + sweatY} Q ${-40} ${-92 + sweatY} ${-48} ${-108 + sweatY} Z`}
          fill="#38BDF8"
          stroke={INK}
          strokeWidth={2.5}
          opacity={1 - sweatY / 38}
        />
      )}
    </g>
  );
};

export const TitleCard2D: React.FC<{
  text: string;
  progress: number;
  accentHex?: string;
}> = ({ text, progress, accentHex = "#22C55E" }) => {
  const words = text.split(" ");
  const shownCount = Math.max(1, Math.ceil(Math.min(1, progress * 1.65) * words.length));
  const shownText = words.slice(0, shownCount).join(" ");
  const s = 0.94 + Math.min(1, progress * 2.5) * 0.06;

  return (
    <g transform={`translate(960 540) scale(${s}) translate(-960 -540)`}>
      <text
        x={960}
        y={555}
        textAnchor="middle"
        fill="#FFFFFF"
        fontFamily={HAND_FONT}
        fontSize={106}
        fontWeight={700}
      >
        {shownText}
      </text>
      <line
        x1={720}
        y1={592}
        x2={720 + 480 * Math.min(1, progress * 1.5)}
        y2={592}
        stroke={accentHex}
        strokeWidth={7}
        strokeLinecap="round"
      />
    </g>
  );
};

export const InkCallout2D: React.FC<{
  x: number;
  y: number;
  text: string;
  color?: string;
  fontSize?: number;
  delaySec?: number;
  localTime: number;
  rotateDeg?: number;
  arrowTo?: [number, number];
}> = ({
  x,
  y,
  text,
  color = "#FFFFFF",
  fontSize = 68,
  delaySec = 0,
  localTime,
  rotateDeg = -3,
  arrowTo,
}) => {
  const { fps } = useVideoConfig();
  const f = Math.max(0, Math.round((localTime - delaySec) * fps));
  const pop = spring({ frame: f, fps, config: { damping: 14, stiffness: 180, mass: 0.75 } });
  if (localTime < delaySec) return null;

  return (
    <g>
      {arrowTo && (
        <line
          x1={x}
          y1={y + 18}
          x2={x + (arrowTo[0] - x) * pop}
          y2={y + 18 + (arrowTo[1] - (y + 18)) * pop}
          stroke={color}
          strokeWidth={6}
          strokeDasharray="12 10"
          strokeLinecap="round"
        />
      )}
      <g transform={`translate(${x} ${y}) rotate(${rotateDeg}) scale(${0.5 + 0.5 * pop})`}>
        <text
          x={0}
          y={0}
          textAnchor="middle"
          fill={INK}
          stroke={INK}
          strokeWidth={12}
          strokeLinejoin="round"
          fontFamily={MARKER_FONT}
          fontSize={fontSize}
        >
          {text}
        </text>
        <text
          x={0}
          y={0}
          textAnchor="middle"
          fill={color}
          fontFamily={MARKER_FONT}
          fontSize={fontSize}
        >
          {text}
        </text>
      </g>
    </g>
  );
};

export const LineChart2D: React.FC<{
  x: number;
  y: number;
  w?: number;
  h?: number;
  label?: string;
  startVal?: number;
  endVal?: number;
  prefix?: string;
  suffix?: string;
  decimals?: number;
  color?: string;
  points?: number[];
  progress: number;
}> = ({
  x,
  y,
  w = 1000,
  h = 460,
  label = "METRIC",
  startVal = 0,
  endVal = 100,
  prefix = "",
  suffix = "",
  decimals = 0,
  color = "#EF4444",
  points = [0.15, 0.22, 0.34, 0.42, 0.65, 0.85, 0.96],
  progress,
}) => {
  const drawProg = Math.min(1, progress * 1.4);
  const pathPts = points.map((p, idx) => {
    const px = x + (idx / Math.max(1, points.length - 1)) * w;
    const py = y + h - p * h * 0.82 - 30;
    return `${idx === 0 ? "M" : "L"} ${px.toFixed(1)} ${py.toFixed(1)}`;
  });
  const d = pathPts.join(" ");
  const totalLen = w * 1.6;
  const val = startVal + (endVal - startVal) * drawProg;
  const formatted = `${prefix}${Number(val.toFixed(decimals)).toLocaleString("en-US", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  })}${suffix}`;

  return (
    <g>
      <rect x={x - 30} y={y - 30} width={w + 60} height={h + 80} rx={16} fill="#FFFFFF" fillOpacity={0.78} stroke={INK} strokeWidth={5} />
      <line x1={x} y1={y + h} x2={x + w} y2={y + h} stroke={INK} strokeWidth={5} />
      <line x1={x} y1={y} x2={x} y2={y + h} stroke={INK} strokeWidth={5} />
      <path
        d={d}
        fill="none"
        stroke={color}
        strokeWidth={11}
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeDasharray={totalLen}
        strokeDashoffset={totalLen * (1 - drawProg)}
      />
      <text x={x + 24} y={y + 42} fill={INK} fontFamily={UI_FONT} fontSize={32} fontWeight={700}>
        {label}
      </text>
      <text x={x + w - 20} y={y + 62} textAnchor="end" fill={color} fontFamily={MARKER_FONT} fontSize={62}>
        {formatted}
      </text>
    </g>
  );
};

export const BarChart2D: React.FC<{
  x: number;
  y: number;
  w?: number;
  h?: number;
  bars: { label: string; value: number; color?: string }[];
  multiplierTag?: string;
  suffix?: string;
  prefix?: string;
  progress: number;
}> = ({ x, y, w = 900, h = 480, bars, multiplierTag, prefix = "", suffix = "", progress }) => {
  const maxVal = Math.max(1, ...bars.map((b) => b.value));
  const barW = Math.min(180, (w / Math.max(1, bars.length)) * 0.56);
  const gap = w / Math.max(1, bars.length);
  const grow = Math.min(1, progress * 1.5);

  return (
    <g>
      <line x1={x} y1={y + h} x2={x + w} y2={y + h} stroke={INK} strokeWidth={6} />
      {bars.map((b, idx) => {
        const bh = Math.max(20, (b.value / maxVal) * (h - 90) * grow);
        const bx = x + idx * gap + (gap - barW) * 0.5;
        const by = y + h - bh;
        const col = b.color || (idx === bars.length - 1 ? "#22C55E" : "#94A3B8");
        const num = Math.round(b.value * grow);
        return (
          <g key={idx}>
            <rect x={bx} y={by} width={barW} height={bh} rx={6} fill={col} stroke={INK} strokeWidth={5} />
            <text x={bx + barW / 2} y={by - 18} textAnchor="middle" fill={col} stroke={INK} strokeWidth={8} paintOrder="stroke" fontFamily={MARKER_FONT} fontSize={46}>
              {prefix}{num.toLocaleString("en-US")}{suffix}
            </text>
            <text x={bx + barW / 2} y={y + h + 46} textAnchor="middle" fill="#1E293B" fontFamily={UI_FONT} fontSize={28} fontWeight={700}>
              {b.label}
            </text>
          </g>
        );
      })}
      {multiplierTag && progress > 0.45 && (
        <g transform={`translate(${x + w - 90} ${y + 110}) rotate(-10)`}>
          <rect x={-72} y={-44} width={144} height={84} rx={10} fill="#FACC15" stroke={INK} strokeWidth={5} />
          <text x={0} y={14} textAnchor="middle" fill={INK} fontFamily={MARKER_FONT} fontSize={48}>
            {multiplierTag}
          </text>
        </g>
      )}
    </g>
  );
};

export const PieChart2D: React.FC<{
  x: number;
  y: number;
  radius?: number;
  slicePct: number;
  label: string;
  color?: string;
  progress: number;
}> = ({ x, y, radius = 230, slicePct, label, color = "#F59E0B", progress }) => {
  const pull = Math.min(1, progress * 1.7) * 48;
  const angle = (Math.min(90, Math.max(5, slicePct)) / 100) * Math.PI * 2;
  const x2 = Math.cos(angle) * radius;
  const y2 = Math.sin(angle) * radius;
  const shownPct = Math.round(slicePct * Math.min(1, progress * 1.5));

  return (
    <g transform={`translate(${x} ${y})`}>
      <ellipse cx={0} cy={28} rx={radius} ry={radius * 0.65} fill="#94A3B8" stroke={INK} strokeWidth={5} />
      <ellipse cx={0} cy={0} rx={radius} ry={radius * 0.65} fill="#E5E7EB" stroke={INK} strokeWidth={5} />
      <g transform={`translate(${pull * 0.7} ${-pull * 0.55})`}>
        <path
          d={`M 0 0 L ${radius} 0 A ${radius} ${radius * 0.65} 0 0 1 ${x2.toFixed(1)} ${(y2 * 0.65).toFixed(1)} Z`}
          fill={color}
          stroke={INK}
          strokeWidth={5}
        />
      </g>
      <text x={radius * 0.45} y={-radius * 0.72} textAnchor="middle" fill={color} stroke={INK} strokeWidth={9} paintOrder="stroke" fontFamily={MARKER_FONT} fontSize={74}>
        {shownPct}%
      </text>
      <text x={radius * 0.45} y={-radius * 0.45} textAnchor="middle" fill="#1E293B" fontFamily={UI_FONT} fontSize={30} fontWeight={700}>
        {label}
      </text>
    </g>
  );
};

export const BalanceScale2D: React.FC<{
  x: number;
  y: number;
  leftLabel: string;
  rightLabel: string;
  tiltDeg?: number;
  leftColor?: string;
  rightColor?: string;
  progress: number;
}> = ({ x, y, leftLabel, rightLabel, tiltDeg = 16, leftColor = "#22C55E", rightColor = "#EF4444", progress }) => {
  const ease = Math.min(1, progress * 1.6);
  const angle = tiltDeg * ease;
  const rad = (angle * Math.PI) / 180;
  const arm = 270;
  const lx = -Math.cos(rad) * arm;
  const ly = -Math.sin(rad) * arm;
  const rx = Math.cos(rad) * arm;
  const ry = Math.sin(rad) * arm;

  return (
    <g transform={`translate(${x} ${y})`}>
      <rect x={-90} y={210} width={180} height={30} rx={8} fill="#64748B" stroke={INK} strokeWidth={5} />
      <rect x={-14} y={-20} width={28} height={235} fill="#94A3B8" stroke={INK} strokeWidth={5} />
      <line x1={lx} y1={ly} x2={rx} y2={ry} stroke="#F59E0B" strokeWidth={16} strokeLinecap="round" />
      <circle cx={0} cy={0} r={22} fill="#FACC15" stroke={INK} strokeWidth={5} />
      {/* Left Pan */}
      <g transform={`translate(${lx} ${ly})`}>
        <line x1={0} y1={0} x2={-75} y2={135} stroke={INK} strokeWidth={4} />
        <line x1={0} y1={0} x2={75} y2={135} stroke={INK} strokeWidth={4} />
        <rect x={-105} y={135} width={210} height={24} rx={8} fill="#F59E0B" stroke={INK} strokeWidth={4} />
        <rect x={-85} y={70} width={170} height={65} rx={8} fill={leftColor} stroke={INK} strokeWidth={4} />
        <text x={0} y={112} textAnchor="middle" fill="#FFFFFF" fontFamily={UI_FONT} fontSize={26} fontWeight={700}>{leftLabel}</text>
      </g>
      {/* Right Pan */}
      <g transform={`translate(${rx} ${ry})`}>
        <line x1={0} y1={0} x2={-75} y2={135} stroke={INK} strokeWidth={4} />
        <line x1={0} y1={0} x2={75} y2={135} stroke={INK} strokeWidth={4} />
        <rect x={-105} y={135} width={210} height={24} rx={8} fill="#F59E0B" stroke={INK} strokeWidth={4} />
        <rect x={-95} y={42} width={190} height={93} rx={8} fill={rightColor} stroke={INK} strokeWidth={4} />
        <text x={0} y={98} textAnchor="middle" fill="#FFFFFF" fontFamily={UI_FONT} fontSize={26} fontWeight={700}>{rightLabel}</text>
      </g>
    </g>
  );
};

export const ConveyorBelt2D: React.FC<{
  x: number;
  y: number;
  w?: number;
  items: string[];
  accentHex?: string;
  frame: number;
  progress: number;
}> = ({ x, y, w = 1320, items, accentHex = "#22C55E", frame, progress }) => {
  const shift = (frame * 5) % 240;
  const stampDip = Math.abs(Math.sin(frame * 0.12)) * 45;

  return (
    <g transform={`translate(${x} ${y})`}>
      {/* Overhead Robotic Arm Stamping */}
      <g transform={`translate(${w * 0.5} ${-160 + stampDip})`}>
        <rect x={-26} y={-140} width={52} height={140} fill="#F97316" stroke={INK} strokeWidth={5} />
        <rect x={-64} y={0} width={128} height={30} rx={8} fill="#334155" stroke={INK} strokeWidth={5} />
      </g>
      {/* Belt Track */}
      <rect x={0} y={0} width={w} height={64} rx={32} fill="#374151" stroke={INK} strokeWidth={6} />
      {Array.from({ length: 6 }).map((_, ri) => (
        <circle key={ri} cx={60 + (ri / 5) * (w - 120)} cy={32} r={20} fill="#94A3B8" stroke={INK} strokeWidth={4} />
      ))}
      {/* Moving Items */}
      {items.map((lbl, idx) => {
        const ix = ((idx * 340 + shift) % (w - 160)) + 40;
        return (
          <g key={idx} transform={`translate(${ix} -96)`}>
            <rect x={0} y={0} width={140} height={96} rx={12} fill={accentHex} stroke={INK} strokeWidth={5} />
            <text x={70} y={60} textAnchor="middle" fill="#FFFFFF" fontFamily={MARKER_FONT} fontSize={34}>
              {lbl}
            </text>
          </g>
        );
      })}
      <line x1={0} y1={-4} x2={w} y2={-4} stroke="#FACC15" strokeWidth={8} strokeDasharray="24 18" strokeDashoffset={-shift} />
      <rect x={0} y={64} width={w} height={18} fill="#1F2937" opacity={0.4 + progress * 0.1} />
    </g>
  );
};

export const WorldMapArc2D: React.FC<{
  x: number;
  y: number;
  w?: number;
  h?: number;
  startPct?: [number, number];
  endPct?: [number, number];
  accentHex?: string;
  zoomLabel?: string;
  progress: number;
  frame: number;
}> = ({
  x,
  y,
  w = 1280,
  h = 640,
  startPct = [24, 48],
  endPct = [78, 52],
  accentHex = "#EF4444",
  zoomLabel = "GLOBAL LINK",
  progress,
  frame,
}) => {
  const sx = x + (startPct[0] / 100) * w;
  const sy = y + (startPct[1] / 100) * h;
  const ex = x + (endPct[0] / 100) * w;
  const ey = y + (endPct[1] / 100) * h;
  const mx = (sx + ex) * 0.5;
  const my = Math.min(sy, ey) - h * 0.25;
  const d = `M ${sx} ${sy} Q ${mx} ${my} ${ex} ${ey}`;
  const arcLen = w * 1.2;
  const draw = Math.min(1, progress * 1.4);

  return (
    <g>
      <rect x={x} y={y} width={w} height={h} rx={18} fill="#7DA8BE" stroke={INK} strokeWidth={6} />
      {/* Stylized Vector Continents */}
      <polygon points={`${x+100},${y+120} ${x+380},${y+100} ${x+430},${y+290} ${x+260},${y+480} ${x+140},${y+310}`} fill="#D6C49D" stroke={INK} strokeWidth={4} />
      <polygon points={`${x+560},${y+90} ${x+1120},${y+80} ${x+1180},${y+340} ${x+920},${y+420} ${x+620},${y+490} ${x+540},${y+250}`} fill="#D6C49D" stroke={INK} strokeWidth={4} />
      {/* Animated Curved Route */}
      <path d={d} fill="none" stroke={accentHex} strokeWidth={8} strokeDasharray="18 12" strokeDashoffset={-frame * 3} opacity={0.95} />
      <circle cx={sx} cy={sy} r={14} fill="#FACC15" stroke={INK} strokeWidth={4} />
      <circle cx={ex} cy={ey} r={16 * (0.7 + 0.4 * draw)} fill={accentHex} stroke={INK} strokeWidth={4} />
      {/* Magnifying Glass Loupe */}
      {progress > 0.3 && (
        <g transform={`translate(${ex - 30} ${ey - 20})`}>
          <circle cx={0} cy={0} r={96} fill="#FFFFFF" fillOpacity={0.22} stroke={INK} strokeWidth={8} />
          <line x1={68} y1={68} x2={132} y2={132} stroke={INK} strokeWidth={16} strokeLinecap="round" />
          <text x={0} y={-118} textAnchor="middle" fill="#FFFFFF" stroke={INK} strokeWidth={8} paintOrder="stroke" fontFamily={MARKER_FONT} fontSize={36}>
            {zoomLabel}
          </text>
        </g>
      )}
    </g>
  );
};

export const QuoteHighlight2D: React.FC<{
  x: number;
  y: number;
  w?: number;
  sourceTag: string;
  quoteBefore: string;
  highlightText: string;
  quoteAfter?: string;
  markStamp?: string;
  progress: number;
}> = ({
  x,
  y,
  w = 1160,
  sourceTag,
  quoteBefore,
  highlightText,
  quoteAfter = "",
  markStamp = "?!",
  progress,
}) => {
  const hiFrac = Math.max(0, Math.min(1, (progress - 0.15) / 0.35));
  const circleShow = progress > 0.48;

  return (
    <g transform={`translate(${x} ${y})`}>
      <rect x={0} y={0} width={w} height={460} rx={18} fill="#FFFFFF" stroke={INK} strokeWidth={6} />
      <rect x={0} y={0} width={w} height={74} rx={14} fill="#1E293B" stroke={INK} strokeWidth={5} />
      <circle cx={42} cy={37} r={14} fill="#22C55E" />
      <text x={78} y={48} fill="#FFFFFF" fontFamily={UI_FONT} fontSize={30} fontWeight={700}>
        {sourceTag}
      </text>
      <text x={70} y={175} fill="#475569" fontFamily={HAND_FONT} fontSize={54}>
        {quoteBefore}
      </text>
      {/* Animated Yellow Highlighter Sweep */}
      <rect x={64} y={208} width={Math.min(w - 140, highlightText.length * 29) * hiFrac} height={68} rx={8} fill="#FDE047" />
      <text x={70} y={260} fill={INK} fontFamily={HAND_FONT} fontSize={62} fontWeight={700}>
        {highlightText}
      </text>
      {quoteAfter && (
        <text x={70} y={355} fill="#475569" fontFamily={HAND_FONT} fontSize={50}>
          {quoteAfter}
        </text>
      )}
      {circleShow && (
        <g>
          <ellipse cx={260} cy={240} rx={220} ry={58} fill="none" stroke="#EF4444" strokeWidth={8} transform="rotate(-2 260 240)" />
          <text x={w - 120} y={180} fill="#EF4444" fontFamily={MARKER_FONT} fontSize={86} transform={`rotate(12 ${w - 120} 180)`}>
            {markStamp}
          </text>
        </g>
      )}
    </g>
  );
};

export const CalendarFlip2D: React.FC<{
  x: number;
  y: number;
  pages: { month: string; day: string }[];
  progress: number;
}> = ({ x, y, pages, progress }) => {
  const idx = Math.min(pages.length - 1, Math.floor(progress * pages.length));
  const cur = pages[idx] || { month: "NOV", day: "30" };
  return (
    <g transform={`translate(${x} ${y})`}>
      <rect x={-140} y={-160} width={280} height={310} rx={14} fill="#FFFFFF" stroke={INK} strokeWidth={6} />
      <rect x={-140} y={-160} width={280} height={84} rx={12} fill="#DC2626" stroke={INK} strokeWidth={6} />
      <text x={0} y={-100} textAnchor="middle" fill="#FFFFFF" fontFamily={MARKER_FONT} fontSize={50}>{cur.month}</text>
      <text x={0} y={74} textAnchor="middle" fill={INK} fontFamily={MARKER_FONT} fontSize={128}>{cur.day}</text>
      {progress > 0.65 && (
        <circle cx={0} cy={30} r={88} fill="none" stroke="#EF4444" strokeWidth={10} />
      )}
    </g>
  );
};

export const Stopwatch2D: React.FC<{
  x: number;
  y: number;
  radius?: number;
  maxSecLabel?: string;
  progress: number;
}> = ({ x, y, radius = 125, maxSecLabel = "6:00", progress }) => {
  const deg = progress * 360;
  return (
    <g transform={`translate(${x} ${y})`}>
      <rect x={-22} y={-radius - 32} width={44} height={32} rx={6} fill="#94A3B8" stroke={INK} strokeWidth={5} />
      <circle cx={0} cy={0} r={radius} fill="#F8FAFC" stroke={INK} strokeWidth={8} />
      <circle cx={0} cy={0} r={radius * 0.84} fill="none" stroke="#CBD5E1" strokeWidth={4} strokeDasharray="8 12" />
      <line x1={0} y1={0} x2={0} y2={-radius * 0.72} stroke="#EF4444" strokeWidth={8} strokeLinecap="round" transform={`rotate(${deg})`} />
      <circle cx={0} cy={0} r={12} fill={INK} />
      <text x={0} y={radius + 64} textAnchor="middle" fill="#1E293B" stroke="#FFFFFF" strokeWidth={8} paintOrder="stroke" fontFamily={MARKER_FONT} fontSize={48}>
        {maxSecLabel}
      </text>
    </g>
  );
};

export const SplitScreen3Panel: React.FC<{
  progress: number;
  panel1: React.ReactNode;
  panel2: React.ReactNode;
  panel3: React.ReactNode;
}> = ({ progress, panel1, panel2, panel3 }) => {
  const show2 = progress >= 0.25;
  const show3 = progress >= 0.52;
  return (
    <g>
      <g>{panel1}</g>
      {show2 && <g>{panel2}</g>}
      {show3 && <g>{panel3}</g>}
      <line x1={640} y1={0} x2={640} y2={1080} stroke={INK} strokeWidth={10} />
      <line x1={1280} y1={0} x2={1280} y2={1080} stroke={INK} strokeWidth={10} />
    </g>
  );
};

export const ReactorVessel2D: React.FC<{
  x: number;
  y: number;
  scale?: number;
  accentHex?: string;
  frame: number;
  progress: number;
}> = ({ x, y, scale = 1, accentHex = "#38BDF8", frame, progress }) => {
  const rodOffset = Math.sin(frame * 0.14) * 28;
  const lidLift = Math.min(1, progress * 1.5) * 40;
  return (
    <g transform={`translate(${x} ${y}) scale(${scale})`}>
      <path d="M -130 -60 Q -130 -230 0 -230 Q 130 -230 130 -60 L 130 160 L -130 160 Z" fill="#64748B" stroke={INK} strokeWidth={6} />
      {/* Cutaway Cherenkov Core Window */}
      <rect x={-90} y={-80} width={180} height={210} rx={16} fill="#0EA5E9" stroke={INK} strokeWidth={5} />
      <rect x={-76} y={-40} width={152} height={155} rx={10} fill={accentHex} opacity={0.75 + Math.sin(frame * 0.2) * 0.2} />
      {/* Oscillating Control Rods */}
      {[-42, 0, 42].map((rx, i) => (
        <rect key={i} x={rx - 10} y={-110 + rodOffset * (i % 2 === 0 ? 1 : -1)} width={20} height={140} rx={6} fill="#FACC15" stroke={INK} strokeWidth={4} />
      ))}
      <rect x={-148} y={-180 - lidLift} width={296} height={28} rx={8} fill="#475569" stroke={INK} strokeWidth={5} />
    </g>
  );
};

export const CoolingTower2D: React.FC<{
  x: number;
  y: number;
  scale?: number;
  accentHex?: string;
  frame: number;
}> = ({ x, y, scale = 1, accentHex = "#38BDF8", frame }) => {
  const puff = (frame * 2.1) % 120;
  return (
    <g transform={`translate(${x} ${y}) scale(${scale})`}>
      <polygon points="-130,170 -85,-140 85,-140 130,170" fill="#94A3B8" stroke={INK} strokeWidth={6} />
      <rect x={-92} y={80} width={184} height={74} rx={8} fill={accentHex} stroke={INK} strokeWidth={4} />
      {/* Rising Steam Clouds */}
      {[0, 40, 80].map((off, i) => {
        const py = -165 - ((puff + off) % 120);
        const op = 1 - ((puff + off) % 120) / 130;
        return <circle key={i} cx={-25 + i * 26} cy={py} r={34} fill="#F8FAFC" stroke={INK} strokeWidth={4} opacity={op} />;
      })}
    </g>
  );
};

export const ServerRack2D: React.FC<{
  x: number;
  y: number;
  scale?: number;
  accentHex?: string;
  frame: number;
}> = ({ x, y, scale = 1, accentHex = "#22D3EE", frame }) => (
  <g transform={`translate(${x} ${y}) scale(${scale})`}>
    <rect x={-105} y={-190} width={210} height={380} rx={12} fill="#1E293B" stroke={INK} strokeWidth={6} />
    {[-140, -80, -20, 40, 100].map((ry, i) => {
      const active = Math.sin(frame * 0.25 - i * 0.9) > -0.2;
      return (
        <g key={i}>
          <rect x={-82} y={ry} width={164} height={44} rx={6} fill="#334155" stroke={INK} strokeWidth={4} />
          <circle cx={-56} cy={ry + 22} r={8} fill={active ? accentHex : "#475569"} />
          <rect x={-28} y={ry + 15} width={86} height={14} rx={4} fill={active ? "#38BDF8" : "#475569"} />
        </g>
      );
    })}
  </g>
);

export const Microchip2D: React.FC<{
  x: number;
  y: number;
  scale?: number;
  color?: string;
  cracked?: boolean;
  overheating?: boolean;
  frame: number;
  progress: number;
}> = ({ x, y, scale = 1, color = "#22C55E", cracked = false, overheating = false, frame, progress }) => {
  const fillCol = overheating ? "#F97316" : color;
  const crackProg = Math.min(1, progress * 1.6);
  return (
    <g transform={`translate(${x} ${y}) scale(${scale})`}>
      {[-120, -60, 0, 60, 120].map((p, i) => (
        <React.Fragment key={i}>
          <rect x={p - 12} y={-188} width={24} height={36} fill="#FACC15" stroke={INK} strokeWidth={4} />
          <rect x={p - 12} y={152} width={24} height={36} fill="#FACC15" stroke={INK} strokeWidth={4} />
          <rect x={-188} y={p - 12} width={36} height={24} fill="#FACC15" stroke={INK} strokeWidth={4} />
          <rect x={152} y={p - 12} width={36} height={24} fill="#FACC15" stroke={INK} strokeWidth={4} />
        </React.Fragment>
      ))}
      <rect x={-154} y={-154} width={308} height={308} rx={20} fill="#14532D" stroke={INK} strokeWidth={7} />
      <rect x={-105} y={-105} width={210} height={210} rx={12} fill={fillCol} stroke={INK} strokeWidth={5} opacity={0.85 + Math.sin(frame * 0.25) * 0.15} />
      {cracked && (
        <path
          d="M 85 -85 L 25 -20 L 55 15 L -30 90"
          fill="none"
          stroke="#FEF08A"
          strokeWidth={9}
          strokeLinecap="round"
          strokeDasharray={300}
          strokeDashoffset={300 * (1 - crackProg)}
        />
      )}
    </g>
  );
};

export const PowerPylon2D: React.FC<{
  x: number;
  y: number;
  scale?: number;
  accentHex?: string;
  frame: number;
}> = ({ x, y, scale = 1, accentHex = "#F59E0B", frame }) => {
  const pulse = 0.6 + 0.4 * Math.sin(frame * 0.3);
  return (
    <g transform={`translate(${x} ${y}) scale(${scale})`}>
      <polygon points="-90,190 -24,-190 24,-190 90,190" fill="none" stroke={INK} strokeWidth={8} />
      <line x1={-125} y1={-90} x2={125} y2={-90} stroke={INK} strokeWidth={10} strokeLinecap="round" />
      <line x1={-95} y1={-150} x2={95} y2={-150} stroke={INK} strokeWidth={10} strokeLinecap="round" />
      <circle cx={-120} cy={-78} r={14} fill={accentHex} stroke={INK} strokeWidth={4} opacity={pulse} />
      <circle cx={120} cy={-78} r={14} fill={accentHex} stroke={INK} strokeWidth={4} opacity={pulse} />
    </g>
  );
};

export const BatteryBank2D: React.FC<{
  x: number;
  y: number;
  scale?: number;
  accentHex?: string;
  frame: number;
  progress: number;
}> = ({ x, y, scale = 1, accentHex = "#10B981", frame, progress }) => {
  const lvl = Math.max(0.25, Math.min(1, progress + 0.15 * Math.sin(frame * 0.12)));
  return (
    <g transform={`translate(${x} ${y}) scale(${scale})`}>
      <rect x={-140} y={-110} width={280} height={220} rx={16} fill="#E2E8F0" stroke={INK} strokeWidth={6} />
      <rect x={-105} y={-72} width={140} height={144} rx={8} fill="#334155" stroke={INK} strokeWidth={4} />
      <rect x={58} y={76 - lvl * 144} width={44} height={lvl * 144} rx={6} fill={accentHex} stroke={INK} strokeWidth={4} />
    </g>
  );
};

export const AnimatedPipe2D: React.FC<{
  d: string;
  color?: string;
  fluidColor?: string;
  strokeWidth?: number;
  frame: number;
}> = ({ d, color = "#475569", fluidColor = "#22D3EE", strokeWidth = 28, frame }) => (
  <g>
    <path d={d} fill="none" stroke={INK} strokeWidth={strokeWidth + 10} strokeLinecap="round" strokeLinejoin="round" />
    <path d={d} fill="none" stroke={color} strokeWidth={strokeWidth} strokeLinecap="round" strokeLinejoin="round" />
    <path
      d={d}
      fill="none"
      stroke={fluidColor}
      strokeWidth={strokeWidth * 0.45}
      strokeDasharray="24 22"
      strokeDashoffset={-frame * 5}
      strokeLinecap="round"
    />
  </g>
);

export const ExplosionBurst2D: React.FC<{
  x: number;
  y: number;
  color?: string;
  triggerSec: number;
  localTime: number;
}> = ({ x, y, color = "#FACC15", triggerSec, localTime }) => {
  const dt = localTime - triggerSec;
  if (dt < 0 || dt > 0.65) return null;
  const s = 0.4 + (dt / 0.65) * 1.4;
  const op = 1 - dt / 0.65;
  return (
    <g transform={`translate(${x} ${y}) scale(${s})`} opacity={op}>
      <polygon
        points="0,-90 22,-28 86,-42 36,10 82,66 14,38 -20,92 -28,26 -90,12 -32,-22"
        fill={color}
        stroke={INK}
        strokeWidth={5}
      />
    </g>
  );
};
