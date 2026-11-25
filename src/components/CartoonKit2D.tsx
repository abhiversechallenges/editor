import React from "react";
import { loadFont as loadSpaceGrotesk } from "@remotion/google-fonts/SpaceGrotesk";
import { loadFont as loadJetBrainsMono } from "@remotion/google-fonts/JetBrainsMono";
import { spring, useVideoConfig } from "remotion";
import type { BackdropTheme, CameraMove2D } from "../types";

const { fontFamily: UI_FONT } = loadSpaceGrotesk("normal", { weights: ["600", "700"], subsets: ["latin"] });
const { fontFamily: MONO_FONT } = loadJetBrainsMono("normal", { weights: ["500", "700"], subsets: ["latin"] });
const INK = "#060A12";
const BLUEPRINT_LINE = "#18243A";

function formatNumber(val: number, decimals = 0, prefix = "", suffix = ""): string {
  const fixed = Number(val.toFixed(decimals));
  return `${prefix}${fixed.toLocaleString("en-US", { minimumFractionDigits: decimals, maximumFractionDigits: decimals })}${suffix}`;
}

export const SceneBackdrop2D: React.FC<{
  theme: BackdropTheme;
  frame: number;
  accentHex?: string;
  chapterTag?: string;
}> = ({ theme, frame, accentHex = "#00F0FF", chapterTag = "01 // CORE TO GRID" }) => {
  if (theme === "black_title_card") {
    return <rect x={-100} y={-100} width={2200} height={2200} fill="#04070E" />;
  }
  const pillW = Math.max(320, chapterTag.length * 14 + 70);
  const chapterOverlay = (
    <g transform="translate(52 38)">
      <rect x={0} y={0} width={pillW} height={46} rx={8} fill="#09101E" fillOpacity={0.94} stroke={accentHex} strokeWidth={2} />
      <circle cx={24} cy={23} r={6} fill={accentHex} opacity={0.6 + 0.4 * Math.sin(frame * 0.25)} />
      <text x={44} y={29} fill="#F8FAFC" fontFamily={MONO_FONT} fontSize={19} fontWeight={700} letterSpacing={1}>{chapterTag.toUpperCase()}</text>
    </g>
  );

  if (theme === "isometric_blueprint" || theme === "thermal_flow") {
    return (
      <g>
        <rect x={-100} y={-100} width={2200} height={2200} fill="#070C16" />
        {Array.from({ length: 30 }).map((_, i) => <line key={`a${i}`} x1={-200 + i * 120} y1={-100} x2={-200 + i * 120 + 1200} y2={2100} stroke={BLUEPRINT_LINE} strokeWidth={1.5} strokeDasharray="4 8" />)}
        {Array.from({ length: 30 }).map((_, i) => <line key={`b${i}`} x1={2200 - i * 120} y1={-100} x2={2200 - i * 120 - 1200} y2={2100} stroke={BLUEPRINT_LINE} strokeWidth={1.5} strokeDasharray="4 8" />)}
        <rect x={36} y={24} width={1848} height={1032} rx={12} fill="none" stroke="#1E293B" strokeWidth={2} />
        {chapterOverlay}
      </g>
    );
  }
  if (theme === "spec_document" || theme === "us_grid_map" || theme === "xray_cutaway" || theme === "split_3panel") {
    return (
      <g>
        <rect x={-100} y={-100} width={2200} height={2200} fill="#08101E" />
        {Array.from({ length: 24 }).map((_, i) => <line key={i} x1={i * 90} y1={-50} x2={i * 90} y2={2050} stroke="#132036" strokeWidth={1.5} />)}
        <rect x={44} y={28} width={1832} height={1024} fill="none" stroke={accentHex} strokeWidth={2} strokeOpacity={0.22} strokeDasharray="10 8" />
        {chapterOverlay}
      </g>
    );
  }
  if (theme === "substation_grid") {
    return (
      <g>
        <rect x={-100} y={-100} width={2200} height={2200} fill="#080C16" />
        <rect x={-50} y={770} width={2100} height={1300} fill="#0F172A" stroke={INK} strokeWidth={4} />
        {[-40, 20, 80].map((yOff, i) => <line key={i} x1={-100} y1={260 + yOff} x2={2100} y2={260 + yOff} stroke="#F59E0B" strokeWidth={3} strokeDasharray="18 12" strokeDashoffset={-frame * 2.5} />)}
        {chapterOverlay}
      </g>
    );
  }
  return (
    <g>
      <rect x={-100} y={-100} width={2200} height={2200} fill="#080D17" />
      {[240, 640, 1280, 1680].map((lx, i) => <rect key={i} x={lx - 60} y={24} width={120} height={12} rx={4} fill={accentHex} opacity={0.85} />)}
      <rect x={-50} y={830} width={2100} height={1200} fill="#111827" stroke={INK} strokeWidth={4} />
      <line x1={-50} y1={830} x2={2050} y2={830} stroke={accentHex} strokeWidth={4} />
      {chapterOverlay}
    </g>
  );
};

export const Camera2D: React.FC<{
  move: CameraMove2D; progress: number; frame: number; peakTimes?: number[]; localTime: number; children?: React.ReactNode;
}> = ({ move, progress, frame, peakTimes = [], localTime, children }) => {
  const ease = progress * progress * (3 - 2 * progress);
  let scale = 1, tx = 0, ty = 0;
  if (move === "push_in") scale = 1 + ease * 0.06;
  else if (move === "pull_out") scale = 1.07 - ease * 0.07;
  else if (move === "pan_right") { scale = 1.03; tx = 24 - ease * 48; }
  else if (move === "pan_left") { scale = 1.03; tx = -24 + ease * 48; }
  else if (move === "pan_up") { scale = 1.03; ty = 20 - ease * 40; }

  let shake = 0;
  for (const pt of peakTimes) {
    const dt = localTime - pt;
    if (dt >= 0 && dt < 0.25) shake += Math.sin(frame * 2.8) * 6 * (1 - dt / 0.25);
  }
  return <g transform={`translate(${960 + tx + shake} ${540 + ty + shake}) scale(${scale}) translate(-960 -540)`}>{children}</g>;
};

export const TelemetryHUD2D: React.FC<{
  x: number; y: number; w?: number; title: string;
  metrics: { label: string; value: string; unit?: string; alert?: boolean; barPct?: number }[]; progress: number;
}> = ({ x, y, w = 540, title, metrics, progress }) => {
  const p = Math.min(1, progress * 1.6);
  const h = 76 + metrics.length * 78;
  return (
    <g transform={`translate(${x} ${y}) scale(${0.94 + 0.06 * p})`} opacity={p}>
      <rect x={12} y={14} width={w} height={h} rx={14} fill="#000000" opacity={0.55} />
      <rect x={0} y={0} width={w} height={h} rx={14} fill="#09101F" fillOpacity={0.95} stroke="#38BDF8" strokeWidth={2.5} />
      <rect x={0} y={0} width={w} height={48} rx={14} fill="#111D35" />
      <circle cx={24} cy={24} r={6} fill="#00F0FF" />
      <text x={44} y={30} fill="#F1F5F9" fontFamily={UI_FONT} fontSize={20} fontWeight={700}>{title}</text>
      {metrics.map((m, idx) => {
        const col = m.alert ? "#EF4444" : "#00F0FF";
        const pct = Math.max(12, Math.min(100, m.barPct ?? (m.alert ? 92 : 68))) * p;
        return (
          <g key={idx} transform={`translate(24 ${76 + idx * 78})`}>
            <text x={0} y={18} fill="#94A3B8" fontFamily={MONO_FONT} fontSize={17}>{m.label}</text>
            <text x={w - 48} y={20} textAnchor="end" fill={col} fontFamily={MONO_FONT} fontSize={26} fontWeight={700}>{m.value} {m.unit || ""}</text>
            <rect x={0} y={34} width={w - 48} height={8} rx={4} fill="#1E293B" />
            <rect x={0} y={34} width={((w - 48) * pct) / 100} height={8} rx={4} fill={col} />
          </g>
        );
      })}
    </g>
  );
};

export const StatCounter2D: React.FC<{
  x: number; y: number; w?: number; label: string; startVal: number; endVal: number;
  prefix?: string; suffix?: string; decimals?: number; color?: string; localTime: number; triggerSec?: number;
}> = ({ x, y, w = 540, label, startVal, endVal, prefix = "", suffix = "", decimals = 0, color = "#00F0FF", localTime, triggerSec = 0.1 }) => {
  const { fps } = useVideoConfig();
  const elapsed = Math.max(0, localTime - triggerSec);
  const ease = 1 - Math.pow(1 - Math.min(1, elapsed / 0.85), 3);
  const pop = spring({ frame: Math.max(0, Math.round(elapsed * fps)), fps, config: { damping: 14, stiffness: 200 } });
  return (
    <g transform={`translate(${x} ${y}) scale(${0.92 + 0.08 * pop})`}>
      <rect x={-w / 2 + 10} y={-68} width={w} height={160} rx={14} fill="#000000" opacity={0.55} />
      <rect x={-w / 2} y={-80} width={w} height={160} rx={14} fill="#0A1222" fillOpacity={0.96} stroke={color} strokeWidth={3} />
      <text x={0} y={-32} textAnchor="middle" fill="#94A3B8" fontFamily={MONO_FONT} fontSize={20} fontWeight={700}>{label.toUpperCase()}</text>
      <text x={0} y={42} textAnchor="middle" fill={color} fontFamily={MONO_FONT} fontSize={64} fontWeight={700}>{formatNumber(startVal + (endVal - startVal) * ease, decimals, prefix, suffix)}</text>
    </g>
  );
};

export const BlueprintStamp2D: React.FC<{
  x: number; y: number; text: string; color?: string; rotateDeg?: number; localTime: number; triggerSec?: number;
}> = ({ x, y, text, color = "#EF4444", rotateDeg = -7, localTime, triggerSec = 0.6 }) => {
  const { fps } = useVideoConfig();
  if (localTime < triggerSec) return null;
  const slam = spring({ frame: Math.max(0, Math.round((localTime - triggerSec) * fps)), fps, config: { damping: 11, stiffness: 280, mass: 0.7 } });
  const stampW = Math.max(300, text.length * 26 + 64);
  return (
    <g transform={`translate(${x} ${y}) rotate(${rotateDeg}) scale(${1.65 - 0.65 * slam})`} opacity={Math.min(1, slam * 1.4)}>
      <rect x={-stampW / 2 + 8} y={-36} width={stampW} height={88} rx={10} fill="#000000" opacity={0.65} />
      <rect x={-stampW / 2} y={-44} width={stampW} height={88} rx={10} fill="#080D18" fillOpacity={0.94} stroke={color} strokeWidth={6} />
      <rect x={-stampW / 2 + 8} y={-36} width={stampW - 16} height={72} rx={6} fill="none" stroke={color} strokeWidth={2} strokeDasharray="8 6" />
      <text x={0} y={14} textAnchor="middle" fill={color} fontFamily={MONO_FONT} fontSize={36} fontWeight={700}>{text.toUpperCase()}</text>
    </g>
  );
};

export const ServerRack800kW2D: React.FC<{
  x: number; y: number; scale?: number; accentHex?: string; frame: number; progress: number;
}> = ({ x, y, scale = 1, accentHex = "#00F0FF", frame, progress }) => (
  <g transform={`translate(${x} ${y}) scale(${scale})`}>
    <polygon points="-100,255 115,255 150,235 -65,235" fill="#000000" opacity={0.6} />
    <polygon points="100,-240 132,-260 132,230 100,250" fill="#070B14" stroke="#334155" strokeWidth={3} />
    <polygon points="-100,-240 -68,-260 132,-260 100,-240" fill="#1E293B" stroke="#475569" strokeWidth={3} />
    <rect x={-100} y={-240} width={200} height={490} rx={4} fill="#0D1424" stroke="#475569" strokeWidth={4} />
    <rect x={-10} y={-225} width={20} height={460 * Math.min(1, progress + 0.2)} fill="#B45309" stroke="#F59E0B" strokeWidth={2} />
    {[-195, -130, -65, 0, 65, 130, 195].map((ry, i) => {
      const active = Math.sin(frame * 0.2 - i) > -0.15;
      return (
        <g key={i}>
          <rect x={-84} y={ry - 22} width={168} height={44} rx={3} fill="#162033" stroke="#334155" strokeWidth={2} />
          <circle cx={-66} cy={ry} r={5} fill={active ? accentHex : "#334155"} />
          <line x1={-48} y1={ry} x2={52} y2={ry} stroke={active ? "#38BDF8" : "#334155"} strokeWidth={3} strokeDasharray="8 6" />
        </g>
      );
    })}
  </g>
);

export const AnimatedFluidPipe2D: React.FC<{
  d: string; color?: string; fluidColor?: string; strokeWidth?: number; label?: string; labelX?: number; labelY?: number; frame: number;
}> = ({ d, color = "#24324B", fluidColor = "#00F0FF", strokeWidth = 24, label, labelX, labelY, frame }) => {
  const badgeW = label ? Math.max(240, label.length * 12.5 + 36) : 0;
  return (
    <g>
      <path d={d} fill="none" stroke="#04070E" strokeWidth={strokeWidth + 8} strokeLinecap="round" strokeLinejoin="round" />
      <path d={d} fill="none" stroke={color} strokeWidth={strokeWidth} strokeLinecap="round" strokeLinejoin="round" />
      <path d={d} fill="none" stroke={fluidColor} strokeWidth={strokeWidth * 0.42} strokeDasharray="22 16" strokeDashoffset={-frame * 6.5} strokeLinecap="round" />
      {label && labelX !== undefined && labelY !== undefined && (
        <g transform={`translate(${labelX} ${labelY})`}>
          <rect x={-badgeW / 2} y={-20} width={badgeW} height={38} rx={6} fill="#080E1B" fillOpacity={0.95} stroke={fluidColor} strokeWidth={2} />
          <text x={0} y={5} textAnchor="middle" fill={fluidColor} fontFamily={MONO_FONT} fontSize={16} fontWeight={700}>{label}</text>
        </g>
      )}
    </g>
  );
};

export const DataHall25D: React.FC<{
  accentHex?: string; frame: number; progress: number; isVertical?: boolean;
}> = ({ accentHex = "#00F0FF", frame, progress, isVertical = false }) => {
  const backRow = isVertical ? [220, 420, 620, 820] : [170, 360, 550, 740, 930, 1120];
  const frontRow = isVertical ? [270, 490, 710] : [230, 430, 630, 830, 1030];
  return (
    <g>
      <polygon points={isVertical ? "60,640 1020,640 1050,1240 30,1240" : "70,480 1230,480 1260,860 40,860"} fill="#0B1222" stroke="#1E293B" strokeWidth={3} />
      <AnimatedFluidPipe2D d={isVertical ? "M 140 520 L 940 520" : "M 120 260 L 1180 260"} color="#334155" fluidColor="#F59E0B" strokeWidth={18} label="48V DC BUSWAY" labelX={isVertical ? 540 : 650} labelY={isVertical ? 485 : 225} frame={frame} />
      {backRow.map((rx, i) => <ServerRack800kW2D key={`br${i}`} x={rx} y={isVertical ? 760 : 480} scale={0.48} accentHex={accentHex} frame={frame + i * 3} progress={progress} />)}
      {frontRow.map((rx, i) => <ServerRack800kW2D key={`fr${i}`} x={rx} y={isVertical ? 1020 : 690} scale={0.62} accentHex={accentHex} frame={frame + i * 5} progress={progress} />)}
      <AnimatedFluidPipe2D d={isVertical ? "M 100 1320 L 980 1320" : "M 80 910 L 1220 910"} fluidColor="#00F0FF" strokeWidth={22} label="CHILLED COOLANT IN -> 18C" labelX={isVertical ? 540 : 420} labelY={isVertical ? 1278 : 872} frame={frame} />
      <AnimatedFluidPipe2D d={isVertical ? "M 980 1420 L 100 1420" : "M 1220 995 L 80 995"} fluidColor="#EF4444" strokeWidth={22} label="<- HEATED RETURN 45C" labelX={isVertical ? 540 : 880} labelY={isVertical ? 1465 : 1035} frame={frame} />
    </g>
  );
};

export const SpecDocument2D: React.FC<{
  x: number; y: number; w?: number; title: string; subtitle?: string;
  items: { label: string; value: string; pct: number; color?: string }[]; progress: number;
}> = ({ x, y, w = 1120, title, subtitle = "ARCHITECTURAL ALLOCATION", items, progress }) => {
  const ease = Math.min(1, progress * 1.45);
  const h = 150 + items.length * 135;
  return (
    <g transform={`translate(${x} ${y})`}>
      <rect x={16} y={18} width={w} height={h} rx={16} fill="#000000" opacity={0.6} />
      <rect x={0} y={0} width={w} height={h} rx={16} fill="#0A1120" fillOpacity={0.96} stroke="#38BDF8" strokeWidth={3} />
      <rect x={0} y={0} width={w} height={74} rx={14} fill="#111C33" />
      <circle cx={38} cy={37} r={10} fill="#00F0FF" />
      <text x={68} y={44} fill="#F8FAFC" fontFamily={UI_FONT} fontSize={28} fontWeight={700}>{title}</text>
      <text x={w - 36} y={44} textAnchor="end" fill="#38BDF8" fontFamily={MONO_FONT} fontSize={18} fontWeight={700}>{subtitle}</text>
      {items.map((it, idx) => {
        const col = it.color || "#00F0FF";
        return (
          <g key={idx} transform={`translate(48 ${115 + idx * 135})`}>
            <text x={0} y={24} fill="#E2E8F0" fontFamily={UI_FONT} fontSize={26} fontWeight={700}>{it.label}</text>
            <text x={w - 96} y={26} textAnchor="end" fill={col} fontFamily={MONO_FONT} fontSize={32} fontWeight={700}>{it.value}</text>
            <rect x={0} y={46} width={w - 96} height={30} rx={6} fill="#162238" stroke="#1E293B" strokeWidth={2} />
            <rect x={0} y={46} width={((w - 96) * Math.min(100, it.pct) * ease) / 100} height={30} rx={6} fill={col} />
          </g>
        );
      })}
    </g>
  );
};

export const USGridMap2D: React.FC<{
  x: number; y: number; w?: number; h?: number; accentHex?: string; frame: number; progress: number;
}> = ({ x, y, w = 1140, h = 680, accentHex = "#F59E0B", frame, progress }) => {
  const nodes = [
    { nx: x + 0.16 * w, ny: y + 0.48 * h, tag: "WEST 500 kV", col: "#00F0FF" },
    { nx: x + 0.48 * w, ny: y + 0.72 * h, tag: "ERCOT TEXAS", col: "#EF4444" },
    { nx: x + 0.62 * w, ny: y + 0.34 * h, tag: "MIDWEST SMR", col: "#10B981" },
    { nx: x + 0.82 * w, ny: y + 0.42 * h, tag: "PJM VIRGINIA", col: "#F59E0B" },
  ];
  return (
    <g>
      <rect x={x + 12} y={y + 14} width={w} height={h} rx={16} fill="#000000" opacity={0.55} />
      <rect x={x} y={y} width={w} height={h} rx={16} fill="#08101E" stroke="#1E293B" strokeWidth={3} />
      <polygon points={`${x + 0.08 * w},${y + 0.22 * h} ${x + 0.45 * w},${y + 0.18 * h} ${x + 0.75 * w},${y + 0.22 * h} ${x + 0.92 * w},${y + 0.16 * h} ${x + 0.88 * w},${y + 0.56 * h} ${x + 0.78 * w},${y + 0.84 * h} ${x + 0.65 * w},${y + 0.72 * h} ${x + 0.48 * w},${y + 0.88 * h} ${x + 0.24 * w},${y + 0.68 * h} ${x + 0.08 * w},${y + 0.54 * h}`} fill="#101B30" stroke="#38BDF8" strokeWidth={3} />
      <path d={`M ${nodes[0].nx} ${nodes[0].ny} L ${nodes[1].nx} ${nodes[1].ny} L ${nodes[3].nx} ${nodes[3].ny} L ${nodes[2].nx} ${nodes[2].ny} Z`} fill="none" stroke={accentHex} strokeWidth={5} strokeDasharray="16 12" strokeDashoffset={-frame * 4} />
      {nodes.map((n, i) => (
        <g key={i} transform={`translate(${n.nx} ${n.ny})`}>
          <circle cx={0} cy={0} r={(18 + Math.sin(frame * 0.2 + i) * 6) * Math.min(1, progress * 1.5)} fill={n.col} opacity={0.25} />
          <circle cx={0} cy={0} r={12} fill={n.col} stroke="#060A12" strokeWidth={3} />
          <rect x={-78} y={-48} width={156} height={28} rx={5} fill="#060B15" stroke={n.col} strokeWidth={2} />
          <text x={0} y={-29} textAnchor="middle" fill="#F8FAFC" fontFamily={MONO_FONT} fontSize={14} fontWeight={700}>{n.tag}</text>
        </g>
      ))}
    </g>
  );
};

export const MicrochannelColdPlate2D: React.FC<{
  x: number; y: number; scale?: number; coolantTempC?: number; frame: number; progress: number;
}> = ({ x, y, scale = 1, coolantTempC = 45, frame, progress }) => {
  const lift = Math.min(1, progress * 1.4) * 58;
  const shift = (frame * 3) % 24;
  return (
    <g transform={`translate(${x} ${y}) scale(${scale})`}>
      <polygon points="180,60 210,42 210,102 180,120" fill="#0F172A" stroke="#00F0FF" strokeWidth={2} />
      <rect x={-180} y={60} width={360} height={60} rx={4} fill="#1E293B" stroke="#00F0FF" strokeWidth={3} />
      <text x={0} y={98} textAnchor="middle" fill="#00F0FF" fontFamily={MONO_FONT} fontSize={20} fontWeight={700}>SILICON DIE // {coolantTempC}C EXIT</text>
      <polygon points="210,0 240,-18 240,30 210,48" fill="#78350F" stroke="#F59E0B" strokeWidth={2} />
      <rect x={-210} y={0} width={420} height={48} rx={4} fill="#B45309" stroke="#F59E0B" strokeWidth={3} />
      {Array.from({ length: 32 }).map((_, i) => <rect key={i} x={-190 + i * 12} y={-40} width={6} height={40} fill={i % 2 === 0 ? "#D97706" : "#38BDF8"} opacity={0.75 + 0.25 * Math.sin(shift + i)} />)}
      <g transform={`translate(0 ${-lift})`}>
        <polygon points="-220,-90 -190,-108 250,-108 220,-90" fill="#475569" stroke="#94A3B8" strokeWidth={2} />
        <polygon points="220,-90 250,-108 250,-62 220,-44" fill="#1E293B" stroke="#94A3B8" strokeWidth={2} />
        <rect x={-220} y={-90} width={440} height={46} rx={6} fill="#334155" stroke="#94A3B8" strokeWidth={3} />
        <circle cx={-130} cy={-67} r={18} fill="#00F0FF" />
        <text x={-130} y={-62} textAnchor="middle" fill="#060A12" fontFamily={MONO_FONT} fontSize={12} fontWeight={700}>18C</text>
        <circle cx={130} cy={-67} r={18} fill="#EF4444" />
        <text x={130} y={-62} textAnchor="middle" fill="#060A12" fontFamily={MONO_FONT} fontSize={12} fontWeight={700}>{coolantTempC}C</text>
      </g>
    </g>
  );
};

export const TransformerSubstation2D: React.FC<{
  x: number; y: number; scale?: number; voltageKV?: number; frame: number;
}> = ({ x, y, scale = 1, voltageKV = 345, frame }) => (
  <g transform={`translate(${x} ${y}) scale(${scale})`}>
    <polygon points="-150,165 165,165 205,140 -110,140" fill="#000000" opacity={0.55} />
    <polygon points="160,-100 198,-124 198,136 160,160" fill="#0D1424" stroke="#475569" strokeWidth={4} />
    <polygon points="-160,-100 -122,-124 198,-124 160,-100" fill="#334155" stroke="#64748B" strokeWidth={3} />
    <rect x={-160} y={-100} width={320} height={260} rx={8} fill="#1E293B" stroke="#475569" strokeWidth={5} />
    {[-140, -100, -60, 60, 100, 140].map((fx, i) => <line key={i} x1={fx} y1={-80} x2={fx} y2={140} stroke="#334155" strokeWidth={8} />)}
    {[-80, 0, 80].map((bx, i) => (
      <g key={i} transform={`translate(${bx} -100)`}>
        <polygon points="-16,0 16,0 8,-90 -8,-90" fill="#94A3B8" stroke="#334155" strokeWidth={3} />
        <circle cx={0} cy={-98} r={12} fill="#F59E0B" opacity={0.7 + 0.3 * Math.sin(frame * 0.3 + i)} />
        <line x1={0} y1={-100} x2={bx * 1.5} y2={-160} stroke="#F59E0B" strokeWidth={4} strokeDasharray="6 4" />
      </g>
    ))}
    <rect x={-95} y={36} width={190} height={44} rx={6} fill="#080E1B" stroke="#F59E0B" strokeWidth={2.5} />
    <text x={0} y={65} textAnchor="middle" fill="#F59E0B" fontFamily={MONO_FONT} fontSize={18} fontWeight={700}>{voltageKV} kV STEP-DOWN</text>
  </g>
);

export const NuclearSMRVessel2D: React.FC<{
  x: number; y: number; scale?: number; cherenkovGlow?: boolean; frame: number; progress: number;
}> = ({ x, y, scale = 1, cherenkovGlow = true, frame, progress }) => (
  <g transform={`translate(${x} ${y}) scale(${scale})`}>
    <ellipse cx={16} cy={186} rx={138} ry={22} fill="#000000" opacity={0.55} />
    <path d="M 120 -80 L 148 -98 L 148 162 L 120 180 Z" fill="#0B1120" stroke="#475569" strokeWidth={4} />
    <path d="M -120 -80 Q -120 -220 0 -220 Q 120 -220 120 -80 L 120 180 L -120 180 Z" fill="#1E293B" stroke="#475569" strokeWidth={6} />
    <rect x={-75} y={-30} width={150} height={160} rx={12} fill="#0284C7" stroke="#38BDF8" strokeWidth={4} />
    {cherenkovGlow && <rect x={-65} y={-20} width={130} height={140} rx={8} fill="#00F0FF" opacity={(0.75 + 0.25 * Math.sin(frame * 0.2)) * 0.85} />}
    {[-32, 0, 32].map((rx, i) => <rect key={i} x={rx - 8} y={-110 + Math.sin(frame * 0.1) * 18 * Math.min(1, progress * 1.5)} width={16} height={110} rx={4} fill="#FACC15" stroke="#713F12" strokeWidth={2} />)}
  </g>
);

export const TechnicalCallout2D: React.FC<{
  x: number; y: number; text: string; subtext?: string; color?: string; localTime: number; delaySec?: number; arrowTo?: [number, number];
}> = ({ x, y, text, subtext, color = "#00F0FF", localTime, delaySec = 0, arrowTo }) => {
  const { fps } = useVideoConfig();
  if (localTime < delaySec) return null;
  const pop = spring({ frame: Math.max(0, Math.round((localTime - delaySec) * fps)), fps, config: { damping: 14, stiffness: 180 } });
  const w = Math.max(220, text.length * 14 + 32);
  return (
    <g transform={`translate(${x} ${y}) scale(${pop})`}>
      {arrowTo && <line x1={0} y1={0} x2={arrowTo[0] - x} y2={arrowTo[1] - y} stroke={color} strokeWidth={2.5} strokeDasharray="5 5" />}
      <rect x={-16} y={-26} width={w} height={subtext ? 64 : 42} rx={6} fill="#080E1B" stroke={color} strokeWidth={2.5} />
      <text x={0} y={0} fill={color} fontFamily={MONO_FONT} fontSize={19} fontWeight={700}>{text}</text>
      {subtext && <text x={0} y={24} fill="#94A3B8" fontFamily={UI_FONT} fontSize={14}>{subtext}</text>}
    </g>
  );
};

export const TitleCard2D: React.FC<{ text: string; progress: number; accentHex?: string }> = ({ text, progress, accentHex = "#00F0FF" }) => (
  <g transform={`translate(960 540) scale(${0.94 + Math.min(1, progress * 2.2) * 0.06})`}>
    <text x={0} y={10} textAnchor="middle" fill="#FFFFFF" fontFamily={UI_FONT} fontSize={84} fontWeight={700}>{text}</text>
    <line x1={-340 * Math.min(1, progress * 1.6)} y1={64} x2={340 * Math.min(1, progress * 1.6)} y2={64} stroke={accentHex} strokeWidth={7} strokeLinecap="round" />
  </g>
);

export const LineChart2D: React.FC<{
  x: number; y: number; w?: number; h?: number; label?: string; startVal?: number; endVal?: number;
  prefix?: string; suffix?: string; decimals?: number; color?: string; progress: number;
}> = ({ x, y, w = 960, h = 440, label = "SURGE", startVal = 0, endVal = 100, prefix = "", suffix = "", decimals = 0, color = "#EF4444", progress }) => {
  const drawProg = Math.min(1, progress * 1.4);
  const d = `M ${x + 40} ${y + h - 30} Q ${x + w * 0.45} ${y + h * 0.72} ${x + w - 40} ${y + 90}`;
  return (
    <g>
      <rect x={x - 12} y={y - 12} width={w + 24} height={h + 44} rx={12} fill="#080E1B" fillOpacity={0.95} stroke="#1E293B" strokeWidth={3} />
      <path d={d} fill="none" stroke={color} strokeWidth={9} strokeLinecap="round" strokeDasharray={w * 1.5} strokeDashoffset={w * 1.5 * (1 - drawProg)} />
      <text x={x + 28} y={y + 42} fill="#E2E8F0" fontFamily={UI_FONT} fontSize={26} fontWeight={700}>{label}</text>
      <text x={x + w - 28} y={y + 54} textAnchor="end" fill={color} fontFamily={MONO_FONT} fontSize={48} fontWeight={700}>{formatNumber(startVal + (endVal - startVal) * drawProg, decimals, prefix, suffix)}</text>
    </g>
  );
};

export const BarChart2D: React.FC<{
  x: number; y: number; w?: number; h?: number;
  bars: { label: string; value: number; prefix?: string; suffix?: string; decimals?: number; color?: string }[]; progress: number;
}> = ({ x, y, w = 960, h = 460, bars, progress }) => {
  const max = Math.max(1, ...bars.map((b) => b.value));
  const bw = Math.min(180, (w / Math.max(1, bars.length)) * 0.54);
  const grow = Math.min(1, progress * 1.55);
  return (
    <g>
      <rect x={x - 20} y={y - 20} width={w + 40} height={h + 110} rx={12} fill="#080E1B" fillOpacity={0.92} stroke="#1E293B" strokeWidth={2.5} />
      <line x1={x} y1={y + h} x2={x + w} y2={y + h} stroke="#475569" strokeWidth={4} />
      {bars.map((b, i) => {
        const bh = Math.max(16, (b.value / max) * (h - 90) * grow);
        const gap = w / Math.max(1, bars.length);
        const bx = x + i * gap + (gap - bw) / 2;
        const col = b.color || "#00F0FF";
        return (
          <g key={i}>
            <polygon points={`${bx + bw},${y + h - bh} ${bx + bw + 18},${y + h - bh - 12} ${bx + bw + 18},${y + h - 12} ${bx + bw},${y + h}`} fill="#060A12" stroke={col} strokeWidth={2} />
            <rect x={bx} y={y + h - bh} width={bw} height={bh} rx={4} fill={col} />
            <text x={bx + bw / 2} y={y + h - bh - 18} textAnchor="middle" fill={col} fontFamily={MONO_FONT} fontSize={30} fontWeight={700}>{formatNumber(b.value * grow, b.decimals ?? 0, b.prefix ?? "", b.suffix ?? "")}</text>
            <text x={bx + bw / 2} y={y + h + 44} textAnchor="middle" fill="#E2E8F0" fontFamily={UI_FONT} fontSize={22} fontWeight={700}>{b.label}</text>
          </g>
        );
      })}
    </g>
  );
};

export const BalanceScale2D: React.FC<{
  x: number; y: number; leftLabel: string; rightLabel: string; tiltDeg?: number; leftColor?: string; rightColor?: string; progress: number;
}> = ({ x, y, leftLabel, rightLabel, tiltDeg = 15, leftColor = "#10B981", rightColor = "#EF4444", progress }) => {
  const tilt = tiltDeg * Math.min(1, progress * 1.5);
  return (
    <g transform={`translate(${x} ${y})`}>
      <line x1={-250} y1={tilt} x2={250} y2={-tilt} stroke="#94A3B8" strokeWidth={12} strokeLinecap="round" />
      <polygon points="0,-10 -32,170 32,170" fill="#334155" />
      <rect x={-275} y={tilt + 14} width={190} height={68} rx={8} fill={leftColor} />
      <text x={-180} y={tilt + 55} textAnchor="middle" fill="#FFFFFF" fontFamily={UI_FONT} fontSize={20} fontWeight={700}>{leftLabel}</text>
      <rect x={85} y={-tilt + 14} width={190} height={68} rx={8} fill={rightColor} />
      <text x={180} y={-tilt + 55} textAnchor="middle" fill="#FFFFFF" fontFamily={UI_FONT} fontSize={20} fontWeight={700}>{rightLabel}</text>
    </g>
  );
};

export const Microchip2D: React.FC<{
  x: number; y: number; scale?: number; color?: string; cracked?: boolean; overheating?: boolean; frame: number; progress: number;
}> = ({ x, y, scale = 1, color = "#00F0FF", overheating = false, frame }) => (
  <g transform={`translate(${x} ${y}) scale(${scale})`}>
    <polygon points="120,-120 146,-138 146,102 120,120" fill="#060A12" stroke={overheating ? "#EF4444" : color} strokeWidth={3} />
    <polygon points="-120,-120 -94,-138 146,-138 120,-120" fill="#1E293B" stroke={overheating ? "#EF4444" : color} strokeWidth={3} />
    <rect x={-120} y={-120} width={240} height={240} rx={8} fill="#090E17" stroke={overheating ? "#EF4444" : color} strokeWidth={5} />
    <rect x={-80} y={-80} width={160} height={160} rx={6} fill={overheating ? "#EF4444" : color} opacity={0.75 + 0.25 * Math.sin(frame * 0.25)} />
    <text x={0} y={8} textAnchor="middle" fill="#060A12" fontFamily={MONO_FONT} fontSize={22} fontWeight={700}>BLACKWELL</text>
  </g>
);

export const PowerPylon2D: React.FC<{ x: number; y: number; scale?: number; accentHex?: string; frame: number }> = ({ x, y, scale = 1, accentHex = "#F59E0B", frame }) => (
  <g transform={`translate(${x} ${y}) scale(${scale})`}>
    <polygon points="-80,180 -20,-180 20,-180 80,180" fill="none" stroke="#94A3B8" strokeWidth={6} />
    <line x1={-120} y1={-80} x2={120} y2={-80} stroke="#94A3B8" strokeWidth={8} />
    <circle cx={-120} cy={-70} r={12} fill={accentHex} opacity={0.7 + 0.3 * Math.sin(frame * 0.3)} />
    <circle cx={120} cy={-70} r={12} fill={accentHex} opacity={0.7 + 0.3 * Math.sin(frame * 0.3)} />
  </g>
);

export const BatteryBank2D: React.FC<{ x: number; y: number; scale?: number; accentHex?: string; frame: number; progress: number }> = ({ x, y, scale = 1, accentHex = "#10B981", frame, progress }) => (
  <g transform={`translate(${x} ${y}) scale(${scale})`}>
    <polygon points="140,-90 168,-108 168,72 140,90" fill="#0B1120" stroke="#475569" strokeWidth={3} />
    <polygon points="-140,-90 -112,-108 168,-108 140,-90" fill="#334155" stroke="#64748B" strokeWidth={3} />
    <rect x={-140} y={-90} width={280} height={180} rx={8} fill="#1E293B" stroke="#475569" strokeWidth={4} />
    <rect x={-110} y={-60} width={220 * Math.min(1, progress * 1.5)} height={120} rx={6} fill={accentHex} opacity={0.8 + 0.2 * Math.sin(frame * 0.15)} />
  </g>
);

export const SplitScreen3Panel: React.FC<{ progress: number; panel1: React.ReactNode; panel2: React.ReactNode; panel3: React.ReactNode }> = ({ progress, panel1, panel2, panel3 }) => (
  <g>
    <g>{panel1}</g>
    {progress >= 0.25 && <g>{panel2}</g>}
    {progress >= 0.52 && <g>{panel3}</g>}
    <line x1={640} y1={0} x2={640} y2={1080} stroke="#1E293B" strokeWidth={8} />
    <line x1={1280} y1={0} x2={1280} y2={1080} stroke="#1E293B" strokeWidth={8} />
  </g>
);
