import React from "react";
import {
  AbsoluteFill,
  Sequence,
  useCurrentFrame,
  useVideoConfig,
  Audio,
  Img,
} from "remotion";

export interface Subtitle {
  start: number;
  end: number;
  text: string;
}

export interface TypeBProps {
  title: string;
  narrationScript: string;
  subtitles: Subtitle[];
  bgmStyle: "upbeat" | "dramatic" | "calm";
  bgVideoUrl?: string;
}

export const typeBDefaultProps: TypeBProps = {
  title: "故事标题",
  narrationScript: "这是一个示例旁白文案...",
  subtitles: [
    { start: 0, end: 3, text: "第一段字幕" },
    { start: 3, end: 6, text: "第二段字幕" },
  ],
  bgmStyle: "upbeat",
};

const TypeB: React.FC<TypeBProps> = ({
  title,
  narrationScript,
  subtitles,
  bgmStyle,
  bgVideoUrl,
}) => {
  const { fps, durationInFrames } = useVideoConfig();
  const frame = useCurrentFrame();

  // 当前显示的字幕
  const currentSubtitle = subtitles.find(
    (s) => frame >= s.start * fps && frame < s.end * fps
  );

  return (
    <AbsoluteFill style={{ backgroundColor: "#0a0a0a" }}>
      {/* 背景视频或图片 */}
      {bgVideoUrl ? (
        <Img src={bgVideoUrl} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
      ) : (
        <div style={{ 
          width: "100%", 
          height: "100%", 
          background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
          opacity: 0.3 
        }} />
      )}

      {/* 标题 */}
      <Sequence from={0} durationInFrames={3 * fps}>
        <div style={{
          position: "absolute",
          top: "10%",
          left: "10%",
          right: "10%",
          textAlign: "center",
          color: "white",
          fontFamily: "'PingFang SC', sans-serif",
          fontSize: 48,
          fontWeight: "bold",
          textShadow: "2px 2px 4px rgba(0,0,0,0.5)",
        }}>
          {title}
        </div>
      </Sequence>

      {/* 字幕区域 */}
      {currentSubtitle && (
        <div style={{
          position: "absolute",
          bottom: "20%",
          left: "10%",
          right: "10%",
          backgroundColor: "rgba(0, 0, 0, 0.7)",
          padding: "20px",
          borderRadius: "10px",
          textAlign: "center",
        }}>
          <div style={{
            color: "white",
            fontFamily: "'PingFang SC', sans-serif",
            fontSize: 32,
            lineHeight: 1.5,
          }}>
            {currentSubtitle.text}
          </div>
        </div>
      )}

      {/* 进度条 */}
      <div style={{
        position: "absolute",
        bottom: "10%",
        left: "10%",
        right: "10%",
        height: "4px",
        backgroundColor: "rgba(255, 255, 255, 0.2)",
        borderRadius: "2px",
      }}>
        <div style={{
          width: `${(frame / durationInFrames) * 100}%`,
          height: "100%",
          backgroundColor: "#ff4757",
          borderRadius: "2px",
          transition: "width 0.1s linear",
        }} />
      </div>
    </AbsoluteFill>
  );
};

export default TypeB;
