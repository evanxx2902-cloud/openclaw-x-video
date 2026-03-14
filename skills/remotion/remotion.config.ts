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
