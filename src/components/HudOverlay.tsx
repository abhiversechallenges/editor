import React from "react";
import { loadFont as loadSpaceGrotesk } from "@remotion/google-fonts/SpaceGrotesk";
import { loadFont as loadJetBrainsMono } from "@remotion/google-fonts/JetBrainsMono";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import type { DocumentaryPlan, HudCallout, StatCounter, SubtitleChunk } from "../types";

const { fontFamily: DISPLAY_FONT } = loadSpaceGrotesk("normal", {
  weights: ["700"],
  subsets: ["latin"],
});

const { fontFamily: MONO_FONT } = loadJetBrainsMono("normal", {
  weights: ["600", "700"],
  subsets: ["latin"],
});

function formatCounterValue(val: number, decimals = 0, prefix = "", suffix = ""): string {
  const fixed = decimals > 0 ? Number(val.toFixed(decimals)) : Math.round(val);
  const formatted = fixed.toLocaleString("en-US", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
  return `${prefix}${formatted}${suffix}`;
}

const CalloutLayer: React.FC<{
  callouts: HudCallout[];
  accentHex: string;
  localBeatFrame: number;
  beatDurFrames: number;
  isFirstBeat: boolean;
  fps: number;
  width: number;
  height: number;
}> = ({ callouts, accentHex, localBeatFrame, beatDurFrames, isFirstBeat, fps, width, height }) => {
  const enter = spring({
    frame: localBeatFrame + (isFirstBeat ? 10 : 0),
    fps,
    config: { damping: 18, stiffness: 170, mass: 0.8 },
  });
  const exitOpacity = interpolate(
    localBeatFrame,
    [Math.max(0, beatDurFrames - 10), beatDurFrames],
    [1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  return (
    <AbsoluteFill style={{ pointerEvents: "none", opacity: exitOpacity }}>
      <svg width={width} height={height} style={{ position: "absolute", inset: 0 }}>
        {callouts.map((c, idx) => {
          const ax = (c.anchorPct[0] / 100) * width;
          const ay = (c.anchorPct[1] / 100) * height;
          const bx = (c.boxPct[0] / 100) * width;
          const by = (c.boxPct[1] / 100) * height;
          const ex = bx + (ax - bx) * 0.45;
          const ey = by;
          const pathLen = Math.hypot(ex - bx, ey - by) + Math.hypot(ax - ex, ay - ey);
          const dashOffset = pathLen * (1 - enter);

          return (
            <g key={idx}>
              <path
                d={`M ${bx} ${by} L ${ex} ${ey} L ${ax} ${ay}`}
                fill="none"
                stroke={accentHex}
                strokeWidth={2.5}
                strokeDasharray={pathLen}
                strokeDashoffset={dashOffset}
                strokeLinecap="round"
              />
              <circle cx={ax} cy={ay} r={6 * enter} fill={accentHex} />
              <circle cx={ax} cy={ay} r={14 * enter} fill="none" stroke={accentHex} strokeWidth={1.5} opacity={0.55} />
            </g>
          );
        })}
      </svg>

      {callouts.map((c, idx) => {
        const bx = (c.boxPct[0] / 100) * width;
        const by = (c.boxPct[1] / 100) * height;
        const alignRight = c.boxPct[0] > 55;
        return (
          <div
            key={idx}
            style={{
              position: "absolute",
              left: alignRight ? undefined : bx,
              right: alignRight ? width - bx : undefined,
              top: by - 22,
              transform: `scale(${0.9 + 0.1 * enter})`,
              opacity: enter,
              padding: "9px 18px",
              borderRadius: 8,
              backgroundColor: "rgba(15, 23, 42, 0.90)",
              border: `1.5px solid ${accentHex}`,
              boxShadow: "0 10px 26px rgba(0, 0, 0, 0.5)",
              fontFamily: MONO_FONT,
              fontSize: width < height ? 21 : 22,
              fontWeight: 700,
              letterSpacing: "0.06em",
              color: "#F8FAFC",
              whiteSpace: "nowrap",
            }}
          >
            {c.label}
          </div>
        );
      })}
    </AbsoluteFill>
  );
};

const StatCounterCard: React.FC<{
  stat: StatCounter;
  accentHex: string;
  frame: number;
  triggerFrame: number;
  beatEndFrame: number;
  isFirstBeat: boolean;
  fps: number;
  isVertical: boolean;
}> = ({ stat, accentHex, frame, triggerFrame, beatEndFrame, isFirstBeat, fps, isVertical }) => {
  const animFrame = Math.max(0, frame - triggerFrame + (isFirstBeat ? 4 : 0));
  const progress = spring({
    frame: animFrame,
    fps,
    config: { damping: 20, stiffness: 120, mass: 0.9 },
  });
  const fadeOut = interpolate(frame, [Math.max(0, beatEndFrame - 10), beatEndFrame], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const opacity = (isFirstBeat ? 1 : Math.min(1, animFrame / 4)) * fadeOut;

  const currentVal = stat.fromVal + (stat.toVal - stat.fromVal) * progress;
  const formatted = formatCounterValue(currentVal, stat.decimals ?? 0, stat.prefix ?? "", stat.suffix ?? "");

  return (
    <div
      style={{
        position: "absolute",
        left: isVertical ? 48 : 64,
        top: isVertical ? 96 : 52,
        opacity,
        transform: `translateY(${isFirstBeat ? 0 : (1 - progress) * 18}px)`,
        padding: "16px 28px",
        borderRadius: 14,
        backgroundColor: "rgba(15, 23, 42, 0.90)",
        border: `1.5px solid ${accentHex}`,
        boxShadow: "0 18px 42px rgba(0, 0, 0, 0.6)",
      }}
    >
      <div
        style={{
          fontFamily: MONO_FONT,
          fontSize: isVertical ? 18 : 17,
          fontWeight: 700,
          letterSpacing: "0.1em",
          color: "#CBD5E1",
          marginBottom: 6,
        }}
      >
        {stat.label}
      </div>
      <div
        style={{
          fontFamily: MONO_FONT,
          fontSize: isVertical ? 54 : 60,
          fontWeight: 700,
          fontVariantNumeric: "tabular-nums",
          lineHeight: 1.0,
          color: accentHex,
        }}
      >
        {formatted}
      </div>
    </div>
  );
};

const SubtitleBanner: React.FC<{
  chunk: SubtitleChunk;
  accentHex: string;
  isVertical: boolean;
}> = ({ chunk, accentHex, isVertical }) => (
  <div
    style={{
      position: "absolute",
      left: "50%",
      bottom: isVertical ? 200 : 78,
      transform: "translateX(-50%)",
      maxWidth: isVertical ? "88%" : "76%",
      padding: "12px 28px",
      borderRadius: 14,
      backgroundColor: "rgba(10, 16, 30, 0.84)",
      border: `1.5px solid ${accentHex}55`,
      boxShadow: "0 12px 30px rgba(0, 0, 0, 0.55)",
      textAlign: "center",
      lineHeight: 1.24,
    }}
  >
    <span
      style={{
        fontFamily: DISPLAY_FONT,
        fontSize: isVertical ? 44 : 48,
        fontWeight: 700,
        letterSpacing: "-0.015em",
      }}
    >
      {chunk.words.map((w, wi) => (
        <span
          key={wi}
          style={{
            color: w.highlight ? accentHex : "#F8FAFC",
            marginRight: wi === chunk.words.length - 1 ? 0 : 12,
            textShadow: "0 3px 14px rgba(0,0,0,0.9)",
          }}
        >
          {w.text}
        </span>
      ))}
    </span>
  </div>
);

export const HudOverlay: React.FC<{ plan: DocumentaryPlan }> = ({ plan }) => {
  const frame = useCurrentFrame();
  const { width, height, fps } = useVideoConfig();
  const tSec = frame / fps;
  const isVertical = height > width;

  const activeSceneIdx = plan.scenes.findIndex((s) => tSec >= s.startSec && tSec <= s.endSec);
  const resolvedSceneIdx = activeSceneIdx === -1 ? plan.scenes.length - 1 : activeSceneIdx;
  const activeScene = plan.scenes[resolvedSceneIdx];

  const activeBeatIdx = activeScene?.beats.findIndex((b) => tSec >= b.startSec && tSec <= b.endSec) ?? -1;
  const resolvedBeatIdx = activeBeatIdx === -1 ? Math.max(0, (activeScene?.beats.length ?? 1) - 1) : activeBeatIdx;
  const activeBeat = activeScene?.beats[resolvedBeatIdx];

  const activeSubtitle = plan.subtitleChunks.find((c) => tSec >= c.startSec && tSec <= c.endSec);

  if (!activeScene || !activeBeat) return null;

  const isFirstBeat = resolvedSceneIdx === 0 && resolvedBeatIdx === 0;
  const beatStartFrame = Math.round(activeBeat.startSec * fps);
  const beatEndFrame = Math.round(activeBeat.endSec * fps);
  const localBeatFrame = Math.max(0, frame - beatStartFrame);
  const beatDurFrames = Math.max(15, beatEndFrame - beatStartFrame);

  const rawTrigFrame = Math.round(activeBeat.triggerSec * fps);
  const triggerFrame = isFirstBeat
    ? 0
    : Math.min(rawTrigFrame, beatStartFrame + Math.round(beatDurFrames * 0.35));

  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      {activeBeat.callouts?.length > 0 && (
        <CalloutLayer
          callouts={activeBeat.callouts}
          accentHex={activeScene.accentHex}
          localBeatFrame={localBeatFrame}
          beatDurFrames={beatDurFrames}
          isFirstBeat={isFirstBeat}
          fps={fps}
          width={width}
          height={height}
        />
      )}

      {activeBeat.statCounter && (
        <StatCounterCard
          stat={activeBeat.statCounter}
          accentHex={activeScene.accentHex}
          frame={frame}
          triggerFrame={triggerFrame}
          beatEndFrame={beatEndFrame}
          isFirstBeat={isFirstBeat}
          fps={fps}
          isVertical={isVertical}
        />
      )}

      {activeSubtitle && (
        <SubtitleBanner chunk={activeSubtitle} accentHex={activeScene.accentHex} isVertical={isVertical} />
      )}
    </AbsoluteFill>
  );
};
