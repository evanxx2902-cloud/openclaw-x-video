import { Composition } from "remotion";
import { TypeAVideo, typeADefaultProps } from "./compositions/TypeA";

export const VideoRoot = () => (
  <>
    <Composition
      id="TypeA"
      component={TypeAVideo}
      durationInFrames={300}
      fps={30}
      width={1080}
      height={1920}
      defaultProps={typeADefaultProps}
    />
  </>
);
