import React from "react";
import {
  AbsoluteFill,
  Sequence,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
} from "remotion";

export interface Slide {
  text: string;
  duration: number; // 秒
}

export interface TypeAProps {
  hook: string;
  slides: Slide[];
  cta: string;
  colorScheme: "dark" | "light" | "gradient";
  fontStyle: "bold" | "elegant" | "handwrite";
}

export const typeADefaultProps: TypeAProps = {
  hook: "震惊！",
  slides: [
    { text: "这是第一屏内容", duration: 2.5 },
    { text: "这是第二屏内容", duration: 2.5 },
  ],
  cta: "关注获取更多",
  colorScheme: "dark",
  fontStyle: "bold",
};

const THEMES = {
  dark: { bg: "#0a0a0a", text: "#ffffff", accent: "#ff4757" },
  light: { bg: "#fafafa", text: "#1a1a1a", accent: "#2ed573" },
  gradient: {
    bg: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
    text: "#ffffff",
    accent: "#ffd700",
  },
};

const FONTS = {
  bold: { family: "'PingFang SC', 'Noto Sans SC', sans-serif", weight: 900 },
  elegant: { family: "'STSong', 'Noto Serif SC', serif", weight: 400 },
  handwrite: { family: "'ZCOOL KuaiLe', cursive", weight: 400 },
};

export const TypeAVideo: React.FC<TypeAProps> = ({
  hook,
  slides,
  cta,
  colorScheme,
  fontStyle,
}) => {
  const { fps } = useVideoConfig();
  const theme = THEMES[colorScheme];
  const font = FONTS[fontStyle];

  const hookFrames = Math.round(1.5 * fps);
  let cursor = hookFrames;
  const slideFrames = slides.map((s) => {
    const start = cursor;
    const dur = Math.round(s.duration * fps);
    cursor += dur;
    return { start, dur, text: s.text };
  });
  const ctaStart = cursor;

  return (
    <AbsoluteFill
      style={{
        background: theme.bg,
        fontFamily: font.family,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      <Sequence from={0} durationInFrames={hookFrames}>
        <HookSlide text={hook} theme={theme} font={font} fps={fps} />
      </Sequence>

      {slideFrames.map((s, i) => (
        <Sequence key={i} from={s.start} durationInFrames={s.dur}>
          <ContentSlide
            text={s.text}
            theme={theme}
            font={font}
            fps={fps}
            index={i}
          />
        </Sequence>
      ))}

      <Sequence from={ctaStart}>
        <CtaSlide text={cta} theme={theme} font={font} fps={fps} />
      </Sequence>
    </AbsoluteFill>
  );
};

const HookSlide: React.FC<{
  text: string;
  theme: (typeof THEMES)["dark"];
  font: (typeof FONTS)["bold"];
  fps: number;
}> = ({ text, theme, font, fps }) => {
  const frame = useCurrentFrame();
  const scale = spring({ frame, fps, config: { damping: 12, stiffness: 200 } });
  return (
    <AbsoluteFill
      style={{ alignItems: "center", justifyContent: "center", display: "flex" }}
    >
      <div
        style={{
          fontSize: 88,
          fontWeight: font.weight,
          color: theme.accent,
          transform: `scale(${scale})`,
          textAlign: "center",
          lineHeight: 1.2,
          padding: "0 60px",
        }}
      >
        {text}
      </div>
    </AbsoluteFill>
  );
};

const ContentSlide: React.FC<{
  text: string;
  theme: (typeof THEMES)["dark"];
  font: (typeof FONTS)["bold"];
  fps: number;
  index: number;
}> = ({ text, theme, font }) => {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [0, 8], [0, 1], {
    extrapolateRight: "clamp",
  });
  const y = interpolate(frame, [0, 8], [30, 0], {
    extrapolateRight: "clamp",
  });
  return (
    <AbsoluteFill
      style={{
        alignItems: "center",
        justifyContent: "center",
        display: "flex",
        padding: "0 60px",
      }}
    >
      <div
        style={{
          fontSize: 56,
          fontWeight: font.weight,
          color: theme.text,
          opacity,
          transform: `translateY(${y}px)`,
          textAlign: "center",
          lineHeight: 1.6,
        }}
      >
        {text}
      </div>
    </AbsoluteFill>
  );
};

const CtaSlide: React.FC<{
  text: string;
  theme: (typeof THEMES)["dark"];
  font: (typeof FONTS)["bold"];
  fps: number;
}> = ({ text, theme }) => {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [0, 10], [0, 1], {
    extrapolateRight: "clamp",
  });
  return (
    <AbsoluteFill
      style={{
        alignItems: "flex-end",
        justifyContent: "center",
        display: "flex",
        paddingBottom: 120,
      }}
    >
      <div
        style={{
          fontSize: 44,
          fontWeight: 700,
          color: theme.accent,
          opacity,
          textAlign: "center",
          border: `3px solid ${theme.accent}`,
          padding: "16px 40px",
          borderRadius: 50,
        }}
      >
        {text}
      </div>
    </AbsoluteFill>
  );
};
