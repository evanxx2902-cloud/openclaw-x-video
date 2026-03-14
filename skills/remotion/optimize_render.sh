#!/bin/bash
# 优化Remotion渲染配置

set -e

cd "$(dirname "$0")"

echo "=== 优化Remotion渲染配置 ===\n"

# 备份原始配置
if [ -f "remotion.config.ts" ]; then
    cp remotion.config.ts remotion.config.ts.backup
    echo "✅ 备份原始配置: remotion.config.ts.backup"
fi

# 创建优化后的配置
cat > remotion.config.ts << 'EOF'
import {Config} from '@remotion/cli/config';

Config.setVideoImageFormat('jpeg');
Config.setOverwriteOutput(true);

// 2C4G服务器优化配置
Config.setConcurrency(1);  // 单线程渲染，避免OOM
Config.setMaxTimelineTracks(5);  // 限制时间轴轨道数

// 编码优化
Config.setCodec('h264');
Config.setCrf(23);  // 质量平衡点
Config.setMuted(true);  // Type A视频不需要音频

// 性能优化
Config.setBrowserExecutable(process.env.CHROMIUM_PATH);
Config.setEntryPoint('./src/index.ts');

// 日志级别
Config.setLogLevel('info');

console.log('[Remotion] 配置已优化为2C4G服务器环境');
console.log(`[Remotion] 并发数: ${Config.getConcurrency()}`);
console.log(`[Remotion] 编码器: ${Config.getCodec()}`);
EOF

echo "✅ 创建优化配置: remotion.config.ts"

# 创建渲染质量配置文件
cat > render_profiles.json << 'EOF'
{
  "profiles": {
    "fast": {
      "concurrency": 1,
      "quality": 50,
      "crf": 28,
      "description": "快速渲染，文件较小"
    },
    "balanced": {
      "concurrency": 1,
      "quality": 80,
      "crf": 23,
      "description": "平衡模式，推荐使用"
    },
    "high_quality": {
      "concurrency": 1,
      "quality": 95,
      "crf": 18,
      "description": "高质量，文件较大"
    }
  },
  "default": "balanced",
  "server_spec": {
    "cpu_cores": 2,
    "memory_gb": 4,
    "recommended_profile": "balanced"
  }
}
EOF

echo "✅ 创建渲染质量配置: render_profiles.json"

# 更新render.sh脚本以支持质量配置
if [ -f "render.sh" ]; then
    cp render.sh render.sh.backup
    echo "✅ 备份原始渲染脚本: render.sh.backup"
    
    # 创建增强版渲染脚本
    cat > render_enhanced.sh << 'EOF'
#!/bin/bash
# 增强版渲染脚本，支持质量配置
set -e

TASK_JSON="$1"
OUTPUT="$2"
PROFILE="${3:-balanced}"  # 默认使用balanced配置
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

if [ -z "$TASK_JSON" ] || [ -z "$OUTPUT" ]; then
  echo "用法: $0 <task_json> <output_mp4> [profile]"
  echo "可选profile: fast, balanced, high_quality"
  exit 1
fi

# 加载质量配置
if [ -f "render_profiles.json" ]; then
  PROFILE_CONFIG=$(python3 -c "
import json
with open('render_profiles.json') as f:
    config = json.load(f)
profile = config['profiles'].get('$PROFILE', config['profiles'][config['default']])
print(f'--concurrency={profile[\"concurrency\"]}')
print(f'--crf={profile[\"crf\"]}')
  ")
  
  CONCURRENCY=$(echo "$PROFILE_CONFIG" | head -1 | cut -d'=' -f2)
  CRF=$(echo "$PROFILE_CONFIG" | tail -1 | cut -d'=' -f2)
else
  CONCURRENCY=1
  CRF=23
fi

echo "[remotion] 使用配置: $PROFILE (并发: $CONCURRENCY, CRF: $CRF)"

# 计算总帧数
TOTAL_FRAMES=$(python3 -c "
import json
t = json.load(open('$TASK_JSON'))
fps = 30
frames = int(1.5 * fps)  # 开场
for s in t.get('slides', []):
    frames += int(s['duration'] * fps)
frames += int(2.0 * fps)  # 结尾
print(frames)
")

# 构建props JSON
PROPS=$(python3 -c "
import json
t = json.load(open('$TASK_JSON'))
props = {
    'hook': t.get('hook', ''),
    'slides': t.get('slides', []),
    'cta': t.get('cta', ''),
    'colorScheme': t.get('color_scheme', 'dark'),
    'fontStyle': t.get('font_style', 'bold'),
}
print(json.dumps(props))
")

cd "$SCRIPT_DIR"

# 确保依赖已安装
if [ ! -d "node_modules" ]; then
  echo "[remotion] 安装依赖..."
  npm install --silent
fi

# 渲染视频
echo "[remotion] 开始渲染..."
npx remotion render \
  src/index.ts \
  TypeA \
  --props="$PROPS" \
  --duration-in-frames="$TOTAL_FRAMES" \
  --concurrency="$CONCURRENCY" \
  --crf="$CRF" \
  --codec="h264" \
  --muted \
  --overwrite \
  --output="$OUTPUT"

# 检查输出文件
if [ -f "$OUTPUT" ]; then
  FILESIZE=$(stat -c%s "$OUTPUT")
  FILESIZE_MB=$(echo "scale=2; $FILESIZE / 1048576" | bc)
  echo "[remotion] 渲染完成: $OUTPUT (${FILESIZE_MB} MB)"
else
  echo "[remotion] 错误: 输出文件未生成"
  exit 1
fi
EOF

    chmod +x render_enhanced.sh
    echo "✅ 创建增强版渲染脚本: render_enhanced.sh"
fi

# 创建Type B视频模板（混剪视频）
mkdir -p src/compositions
cat > src/compositions/TypeB.tsx << 'EOF'
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
EOF

echo "✅ 创建Type B视频模板: src/compositions/TypeB.tsx"

# 更新index.ts注册Type B
if [ -f "src/index.ts" ]; then
    cat > src/index.ts << 'EOF'
import {registerRoot} from 'remotion';
import {TypeA} from './compositions/TypeA';
import TypeB from './compositions/TypeB';

registerRoot(() => {
  return (
    <>
      <TypeA {...TypeA.typeADefaultProps} />
      <TypeB {...TypeB.typeBDefaultProps} />
    </>
  );
});
EOF
    echo "✅ 更新入口文件注册Type B组件"
fi

echo -e "\n🎬 渲染优化完成！"
echo -e "\n新增功能:"
echo "1. 多质量配置 (fast/balanced/high_quality)"
echo "2. Type B视频模板 (故事混剪)"
echo "3. 服务器优化配置 (2C4G环境)"
echo "4. 增强监控和日志"

echo -e "\n使用示例:"
echo "  # 平衡模式渲染"
echo "  ./render_enhanced.sh ../../data/tasks/xxx_task.json ../../output/video.mp4 balanced"
echo ""
echo "  # 快速模式渲染"
echo "  ./render_enhanced.sh ../../data/tasks/xxx_task.json ../../output/video.mp4 fast"