import { Config } from "@remotion/cli/config";

Config.setVideoImageFormat("jpeg");
Config.setJpegQuality(90);
Config.setOffthreadVideoCacheSizeInBytes(1024 * 1024 * 1024);
Config.setCodec("h264");
Config.setPixelFormat("yuv420p");
