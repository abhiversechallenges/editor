import React from "react";
import { loadFont as loadSpaceGrotesk } from "@remotion/google-fonts/SpaceGrotesk";
import { loadFont as loadJetBrainsMono } from "@remotion/google-fonts/JetBrainsMono";
import { spring, useVideoConfig } from "remotion";
import type { BackdropTheme, CameraMove2D } from "../types";

const { fontFamily: UI_FONT } = loadSpaceGrotesk("normal", { weights: ["600", "700"], subsets: ["latin"] });
const { fontFamily: MONO_FONT } = loadJetBrainsMono("normal", { weights: ["500", "700"], subsets: ["latin"] });

const INK = "#0A0F1D";
const BLUEPRINT_LINE = "#1E293B";

export const SceneBackdrop2D: React.FC<{
  theme: BackdropTheme;
  frame: number;
  accentHex?: string;
}> = ({ theme, frame, accentHex = "#00F0FF" }) => {
  if (theme === "black_title_card") {
    return <rect x={-100} y={-100} width={2200} height={2200} fill="#050811" />;
  }

  if (theme === "isometric_blueprint" || theme === "thermal_flow") {
    return (
      <g>
        <rect x={-100} y={-100} width={2200} height={2200} fill="#080C14" />
        {Array.from({ length: 30 }).map((_, i) => (
          <line key={`iso1_${i}`} x1={-200 + i * 120} y1={-100} x2={-200 + i * 120 + 1200} y2={2100} stroke={BLUEPRINT_LINE} strokeWidth={1.5} strokeDasharray="4 8" />
        ))}
        {Array.from({ length: 30 }).map((_, i) => (
          <line key={`iso2_${i}`} x1={2200 - i * 120} y1={-100} x2={2200 - i * 120 - 1200} y2={2100} stroke={BLUEPRINT_LINE} strokeWidth={1.5} strokeDasharray="4 8" />
        ))}
        <text x={80} y={80} fill="#334155" fontFamily={MONO_FONT} fontSize={16}>
          SYS_REF: GRID_30DEG // {theme.toUpperCase()}
        </text>
      </g>
    );
  }

  if (theme === "xray_cutaway" || theme === "split_3panel") {
    return (
      <g>
        <rect x={-100} y={-100} width={2200} height={2200} fill="#0A1120" />
        {Array.from({ length: 24 }).map((_, i) => (
          <line key={`xr_${i}`} x1={i * 90} y1={-50} x2={i * 90} y2={2050} stroke="#162238" strokeWidth={1.5} />
        ))}
        <rect x={60} y={60} width={1800} height={960} fill="none" stroke={accentHex} strokeWidth={2} strokeOpacity={0.25} strokeDasharray="10 8" />
      </g>
    );
  }

  if (theme === "substation_grid") {
    return (
      <g>
        <rect x={-100} y={-100} width={2200} height={2200} fill="#0A0E17" />
        <rect x={-50} y={780} width={2100} height={1300} fill="#111827" stroke={INK} strokeWidth={4} />
        {[-40, 20, 80].map((yOff, i) => (
          <line key={i} x1={-100} y1={280 + yOff} x2={2100} y2={280 + yOff} stroke="#F59E0B" strokeWidth={3} strokeDasharray="18 12" strokeDashoffset={-frame * 2} />
        ))}
      </g>
    );
  }

  if (theme === "cleanroom_fab") {
    return (
      <g>
        <rect x={-100} y={-100} width={2200} height={2200} fill="#0D1527" />
        {Array.from({ length: 24 }).map((_, i) => (
          <line key={`v_${i}`} x1={i * 90} y1={-50} x2={i * 90} y2={2050} stroke="#1E293B" strokeWidth={1.5} />
        ))}
        {Array.from({ length: 24 }).map((_, i) => (
          <line key={`h_${i}`} x1={-50} y1={i * 90} x2={2050} y2={i * 90} stroke="#1E293B" strokeWidth={1.5} />
        ))}
      </g>
    );
  }

  return (
    <g>
      <rect x={-100} y={-100} width={2200} height={2200} fill="#090D16" />
      {[240, 640, 1280, 1680].map((lx, i) => (
        <rect key={i} x={lx - 60} y={30} width={120} height={14} rx={4} fill={accentHex} opacity={0.8} />
      ))}
      <rect x={-50} y={820} width={2100} height={1200} fill="#1E293B" stroke={INK} strokeWidth={4} />
      <line x1={-50} y1={820} x2={2050} y2={820} stroke={accentHex} strokeWidth={4} />
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

  if (move === "push_in") scale = 1 + ease * 0.08;
  else if (move === "pull_out") scale = 1.08 - ease * 0.08;
  else if (move === "pan_right") { scale = 1.04; tx = 30 - ease * 60; }
  else if (move === "pan_left") { scale = 1.04; tx = -30 + ease * 60; }
  else if (move === "pan_up") { scale = 1.04; ty = 25 - ease * 50; }

  let shake = 0;
  for (const pt of peakTimes) {
    const dt = localTime - pt;
    if (dt >= 0 && dt < 0.25) {
      shake += Math.sin(frame * 2.8) * 6 * (1 - dt / 0.25);
    }
  }

  return (
    <g transform={`translate(${960 + tx + shake} ${540 + ty + shake}) scale(${scale}) translate(-960 -540)`}>
      {children}
    </g>
  );
};

export const TelemetryHUD2D: React.FC<{
  x: number;
  y: number;
  title: string;
  metrics: { label: string; value: string; unit?: string; alert?: boolean }[];
  progress: number;
}> = ({ x, y, title, metrics, progress }) => {
  const p = Math.min(1, progress * 1.5);
  return (
    <g transform={`translate(${x} ${y}) scale(${0.9 + 0.1 * p})`} opacity={p}>
      <rect x={0} y={0} width={380} height={60 + metrics.length * 48} rx={8} fill="#090E17" fillOpacity={0.92} stroke="#38BDF8" strokeWidth={2} />
      <rect x={0} y={0} width={380} height={36} rx={8} fill="#1E293B" />
      <circle cx={20} cy={18} r={5} fill="#00F0FF" />
      <text x={36} y={23} fill="#E2E8F0" fontFamily={UI_FONT} fontSize={16} fontWeight={700}>{title}</text>
      {metrics.map((m, idx) => (
        <g key={idx} transform={`translate(20 ${62 + idx * 48})`}>
          <text x={0} y={16} fill="#94A3B8" fontFamily={MONO_FONT} fontSize={14}>{m.label}</text>
          <text x={340} y={16} textAnchor="end" fill={m.alert ? "#EF4444" : "#00F0FF"} fontFamily={MONO_FONT} fontSize={18} fontWeight={700}>
            {m.value} {m.unit || ""}
          </text>
          <line x1={0} y1={28} x2={340} y2={28} stroke="#1E293B" strokeWidth={1} />
        </g>
      ))}
    </g>
  );
};

export const MicrochannelColdPlate2D: React.FC<{
  x: number;
  y: number;
  scale?: number;
  coolantTempC?: number;
  frame: number;
  progress: number;
}> = ({ x, y, scale = 1, coolantTempC = 62, frame, progress }) => {
  const lift = Math.min(1, progress * 1.4) * 60;
  const shift = (frame * 3) % 24;
  return (
    <g transform={`translate(${x} ${y}) scale(${scale})`}>
      <rect x={-180} y={60} width={360} height={60} rx={4} fill="#1E293B" stroke="#00F0FF" strokeWidth={3} />
      <text x={0} y={98} textAnchor="middle" fill="#00F0FF" fontFamily={MONO_FONT} fontSize={20} fontWeight={700}>
        SILICON DIE // {coolantTempC}C EXIT
      </text>
      <rect x={-210} y={0} width={420} height={48} rx={6} fill="#B45309" stroke="#F59E0B" strokeWidth={3} />
      {Array.from({ length: 32 }).map((_, i) => (
        <rect key={i} x={-190 + i * 12} y={-40} width={6} height={40} fill={i % 2 === 0 ? "#D97706" : "#38BDF8"} opacity={0.75 + 0.25 * Math.sin(shift + i)} />
      ))}
      <g transform={`translate(0 ${-lift})`}>
        <rect x={-220} y={-90} width={440} height={46} rx={8} fill="#334155" stroke="#94A3B8" strokeWidth={3} />
        <circle cx={-130} cy={-67} r={18} fill="#00F0FF" />
        <text x={-130} y={-62} textAnchor="middle" fill="#0A0F1D" fontFamily={MONO_FONT} fontSize={12} fontWeight={700}>IN</text>
        <circle cx={130} cy={-67} r={18} fill="#EF4444" />
        <text x={130} y={-62} textAnchor="middle" fill="#0A0F1D" fontFamily={MONO_FONT} fontSize={12} fontWeight={700}>OUT</text>
      </g>
    </g>
  );
};

export const ServerRack800kW2D: React.FC<{
  x: number;
  y: number;
  scale?: number;
  accentHex?: string;
  frame: number;
  progress: number;
}> = ({ x, y, scale = 1, accentHex = "#00F0FF", frame, progress }) => (
  <g transform={`translate(${x} ${y}) scale(${scale})`}>
    <rect x={-120} y={-260} width={240} height={520} rx={8} fill="#0D131F" stroke="#334155" strokeWidth={5} />
    <rect x={-12} y={-240} width={24} height={480 * Math.min(1, progress + 0.2)} fill="#B45309" stroke="#F59E0B" strokeWidth={2} />
    {[-210, -140, -70, 0, 70, 140, 210].map((ry, i) => {
      const active = Math.sin(frame * 0.2 - i) > -0.1;
      return (
        <g key={i}>
          <rect x={-98} y={ry - 24} width={196} height={48} rx={4} fill="#1E293B" stroke="#475569" strokeWidth={2} />
          <circle cx={-75} cy={ry} r={5} fill={active ? accentHex : "#334155"} />
          <line x1={-55} y1={ry} x2={55} y2={ry} stroke={active ? "#38BDF8" : "#334155"} strokeWidth={3} strokeDasharray="8 6" />
        </g>
      );
    })}
  </g>
);

export const TransformerSubstation2D: React.FC<{
  x: number;
  y: number;
  scale?: number;
  voltageKV?: number;
  frame: number;
}> = ({ x, y, scale = 1, voltageKV = 345, frame }) => (
  <g transform={`translate(${x} ${y}) scale(${scale})`}>
    <rect x={-160} y={-100} width={320} height={260} rx={10} fill="#1E293B" stroke="#475569" strokeWidth={6} />
    {[-140, -100, -60, 60, 100, 140].map((fx, i) => (
      <line key={i} x1={fx} y1={-80} x2={fx} y2={140} stroke="#334155" strokeWidth={8} />
    ))}
    {[-80, 0, 80].map((bx, i) => (
      <g key={i} transform={`translate(${bx} -100)`}>
        <polygon points="-16,0 16,0 8,-90 -8,-90" fill="#94A3B8" stroke="#334155" strokeWidth={3} />
        <circle cx={0} cy={-98} r={12} fill="#F59E0B" opacity={0.7 + 0.3 * Math.sin(frame * 0.3 + i)} />
        <line x1={0} y1={-100} x2={bx * 1.5} y2={-160} stroke="#F59E0B" strokeWidth={4} strokeDasharray="6 4" />
      </g>
    ))}
    <rect x={-80} y={40} width={160} height={40} rx={4} fill="#0F172A" stroke="#F59E0B" strokeWidth={2} />
    <text x={0} y={66} textAnchor="middle" fill="#F59E0B" fontFamily={MONO_FONT} fontSize={18} fontWeight={700}>
      {voltageKV} kV STEP-DOWN
    </text>
  </g>
);

export const NuclearSMRVessel2D: React.FC<{
  x: number;
  y: number;
  scale?: number;
  cherenkovGlow?: boolean;
  frame: number;
  progress: number;
}> = ({ x, y, scale = 1, cherenkovGlow = true, frame, progress }) => {
  const pulse = 0.75 + 0.25 * Math.sin(frame * 0.2);
  const rodDrop = Math.sin(frame * 0.1) * 18 * Math.min(1, progress * 1.5);
  return (
    <g transform={`translate(${x} ${y}) scale(${scale})`}>
      <path d="M -120 -80 Q -120 -220 0 -220 Q 120 -220 120 -80 L 120 180 L -120 180 Z" fill="#1E293B" stroke="#475569" strokeWidth={6} />
      <rect x={-75} y={-30} width={150} height={160} rx={12} fill="#0284C7" stroke="#38BDF8" strokeWidth={4} />
      {cherenkovGlow && <rect x={-65} y={-20} width={130} height={140} rx={8} fill="#00F0FF" opacity={pulse * 0.85} />}
      {[-32, 0, 32].map((rx, i) => (
        <rect key={i} x={rx - 8} y={-110 + rodDrop} width={16} height={110} rx={4} fill="#FACC15" stroke="#713F12" strokeWidth={2} />
      ))}
    </g>
  );
};

export const AnimatedFluidPipe2D: React.FC<{
  d: string;
  color?: string;
  fluidColor?: string;
  strokeWidth?: number;
  frame: number;
}> = ({ d, color = "#334155", fluidColor = "#00F0FF", strokeWidth = 26, frame }) => (
  <g>
    <path d={d} fill="none" stroke="#0A0F1D" strokeWidth={strokeWidth + 8} strokeLinecap="round" strokeLinejoin="round" />
    <path d={d} fill="none" stroke={color} strokeWidth={strokeWidth} strokeLinecap="round" strokeLinejoin="round" />
    <path d={d} fill="none" stroke={fluidColor} strokeWidth={strokeWidth * 0.4} strokeDasharray="20 16" strokeDashoffset={-frame * 6} strokeLinecap="round" />
  </g>
);

export const TechnicalCallout2D: React.FC<{
  x: number;
  y: number;
  text: string;
  subtext?: string;
  color?: string;
  localTime: number;
  delaySec?: number;
  arrowTo?: [number, number];
}> = ({ x, y, text, subtext, color = "#00F0FF", localTime, delaySec = 0, arrowTo }) => {
  const { fps } = useVideoConfig();
  const f = Math.max(0, Math.round((localTime - delaySec) * fps));
  const pop = spring({ frame: f, fps, config: { damping: 14, stiffness: 180 } });
  if (localTime < delaySec) return null;

  return (
    <g transform={`translate(${x} ${y}) scale(${pop})`}>
      {arrowTo && (
        <line x1={0} y1={0} x2={arrowTo[0] - x} y2={arrowTo[1] - y} stroke={color} strokeWidth={2} strokeDasharray="4 4" />
      )}
      <rect x={-14} y={-24} width={Math.max(180, text.length * 15)} height={subtext ? 58 : 38} rx={4} fill="#090E17" stroke={color} strokeWidth={2} />
      <text x={0} y={0} fill={color} fontFamily={MONO_FONT} fontSize={18} fontWeight={700}>{text}</text>
      {subtext && <text x={0} y={22} fill="#94A3B8" fontFamily={UI_FONT} fontSize={13}>{subtext}</text>}
    </g>
  );
};

export const TitleCard2D: React.FC<{
  text: string;
  progress: number;
  accentHex?: string;
}> = ({ text, progress, accentHex = "#00F0FF" }) => (
  <g transform="translate(960 540)">
    <text x={0} y={15} textAnchor="middle" fill="#FFFFFF" fontFamily={UI_FONT} fontSize={88} fontWeight={700}>{text}</text>
    <line x1={-300 * Math.min(1, progress * 1.5)} y1={60} x2={300 * Math.min(1, progress * 1.5)} y2={60} stroke={accentHex} strokeWidth={6} strokeLinecap="round" />
  </g>
);

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
  color?: string;
  progress: number;
}> = ({ x, y, w = 960, h = 420, label = "SURGE", startVal = 0, endVal = 100, prefix = "", suffix = "", color = "#EF4444", progress }) => {
  const drawProg = Math.min(1, progress * 1.4);
  const cur = Math.round(startVal + (endVal - startVal) * drawProg);
  const d = `M ${x} ${y + h} Q ${x + w * 0.4} ${y + h * 0.7} ${x + w} ${y + h * 0.15}`;
  return (
    <g>
      <rect x={x - 20} y={y - 20} width={w + 40} height={h + 70} rx={8} fill="#080C14" fillOpacity={0.9} stroke="#1E293B" strokeWidth={2} />
      <path d={d} fill="none" stroke={color} strokeWidth={8} strokeLinecap="round" strokeDasharray={w * 1.5} strokeDashoffset={w * 1.5 * (1 - drawProg)} />
      <text x={x + 20} y={y + 36} fill="#E2E8F0" fontFamily={UI_FONT} fontSize={24} fontWeight={700}>{label}</text>
      <text x={x + w - 20} y={y + 45} textAnchor="end" fill={color} fontFamily={MONO_FONT} fontSize={44} fontWeight={700}>{prefix}{cur.toLocaleString()}{suffix}</text>
    </g>
  );
};

export const BarChart2D: React.FC<{
  x: number;
  y: number;
  w?: number;
  h?: number;
  bars: { label: string; value: number; color?: string }[];
  progress: number;
}> = ({ x, y, w = 840, h = 420, bars, progress }) => {
  const max = Math.max(1, ...bars.map((b) => b.value));
  const bw = (w / Math.max(1, bars.length)) * 0.6;
  return (
    <g>
      <line x1={x} y1={y + h} x2={x + w} y2={y + h} stroke="#334155" strokeWidth={4} />
      {bars.map((b, i) => {
        const bh = (b.value / max) * (h - 60) * Math.min(1, progress * 1.5);
        const bx = x + i * (w / Math.max(1, bars.length)) + 40;
        return (
          <g key={i}>
            <rect x={bx} y={y + h - bh} width={bw} height={bh} rx={4} fill={b.color || "#00F0FF"} />
            <text x={bx + bw / 2} y={y + h + 36} textAnchor="middle" fill="#94A3B8" fontFamily={MONO_FONT} fontSize={16}>{b.label}</text>
          </g>
        );
      })}
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
}> = ({ x, y, leftLabel, rightLabel, tiltDeg = 15, leftColor = "#10B981", rightColor = "#EF4444", progress }) => {
  const tilt = tiltDeg * Math.min(1, progress * 1.5);
  return (
    <g transform={`translate(${x} ${y})`}>
      <line x1={-240} y1={tilt} x2={240} y2={-tilt} stroke="#94A3B8" strokeWidth={12} strokeLinecap="round" />
      <polygon points="0,-10 -30,160 30,160" fill="#334155" />
      <rect x={-260} y={tilt + 10} width={160} height={60} rx={6} fill={leftColor} />
      <text x={-180} y={tilt + 46} textAnchor="middle" fill="#FFFFFF" fontFamily={UI_FONT} fontSize={18} fontWeight={700}>{leftLabel}</text>
      <rect x={100} y={-tilt + 10} width={160} height={60} rx={6} fill={rightColor} />
      <text x={180} y={-tilt + 46} textAnchor="middle" fill="#FFFFFF" fontFamily={UI_FONT} fontSize={18} fontWeight={700}>{rightLabel}</text>
    </g>
  );
};

export const Microchip2D: React.FC<{
  x: number;
  y: number;
  scale?: number;
  color?: string;
  cracked?: boolean;
  overheating?: boolean;
  frame: number;
  progress: number;
}> = ({ x, y, scale = 1, color = "#00F0FF", overheating = false, frame }) => (
  <g transform={`translate(${x} ${y}) scale(${scale})`}>
    <rect x={-120} y={-120} width={240} height={240} rx={12} fill="#090E17" stroke={overheating ? "#EF4444" : color} strokeWidth={6} />
    <rect x={-80} y={-80} width={160} height={160} rx={8} fill={overheating ? "#EF4444" : color} opacity={0.75 + 0.25 * Math.sin(frame * 0.25)} />
    <text x={0} y={8} textAnchor="middle" fill="#0A0F1D" fontFamily={MONO_FONT} fontSize={22} fontWeight={700}>BLACKWELL</text>
  </g>
);

export const PowerPylon2D: React.FC<{
  x: number;
  y: number;
  scale?: number;
  accentHex?: string;
  frame: number;
}> = ({ x, y, scale = 1, accentHex = "#F59E0B", frame }) => (
  <g transform={`translate(${x} ${y}) scale(${scale})`}>
    <polygon points="-80,180 -20,-180 20,-180 80,180" fill="none" stroke="#94A3B8" strokeWidth={6} />
    <line x1={-120} y1={-80} x2={120} y2={-80} stroke="#94A3B8" strokeWidth={8} />
    <circle cx={-120} cy={-70} r={12} fill={accentHex} opacity={0.7 + 0.3 * Math.sin(frame * 0.3)} />
    <circle cx={120} cy={-70} r={12} fill={accentHex} opacity={0.7 + 0.3 * Math.sin(frame * 0.3)} />
  </g>
);

export const BatteryBank2D: React.FC<{
  x: number;
  y: number;
  scale?: number;
  accentHex?: string;
  frame: number;
  progress: number;
}> = ({ x, y, scale = 1, accentHex = "#10B981", frame, progress }) => (
  <g transform={`translate(${x} ${y}) scale(${scale})`}>
    <rect x={-140} y={-90} width={280} height={180} rx={12} fill="#1E293B" stroke="#475569" strokeWidth={5} />
    <rect x={-110} y={-60} width={220 * Math.min(1, progress * 1.5)} height={120} rx={6} fill={accentHex} opacity={0.8 + 0.2 * Math.sin(frame * 0.15)} />
  </g>
);

export const SplitScreen3Panel: React.FC<{
  progress: number;
  panel1: React.ReactNode;
  panel2: React.ReactNode;
  panel3: React.ReactNode;
}> = ({ progress, panel1, panel2, panel3 }) => (
  <g>
    <g>{panel1}</g>
    {progress >= 0.25 && <g>{panel2}</g>}
    {progress >= 0.52 && <g>{panel3}</g>}
    <line x1={640} y1={0} x2={640} y2={1080} stroke="#1E293B" strokeWidth={8} />
    <line x1={1280} y1={0} x2={1280} y2={1080} stroke="#1E293B" strokeWidth={8} />
  </g>
);
