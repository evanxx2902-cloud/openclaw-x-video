import { Composition } from "remotion";
import { TypeAVideo, typeADefaultProps } from "./compositions/TypeA";

// 计算默认时长（用于预览）
const calculateDefaultDuration = (props: typeof typeADefaultProps) => {
  const fps = 30;
  let frames = Math.round(1.5 * fps); // hook
  for (const slide of props.slides) {
    frames += Math.round(slide.duration * fps);
  }
  frames += Math.round(2.0 * fps); // CTA
  return frames;
};

export const VideoRoot = () => (
  <>
    <Composition
      id="TypeA"
      component={TypeAVideo}
      durationInFrames={calculateDefaultDuration(typeADefaultProps)}
      fps={30}
      width={1080}
      height={1920}
      defaultProps={typeADefaultProps}
    />
  </>
);
