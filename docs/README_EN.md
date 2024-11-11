<div align="center">
  <img src="./docs/images/logo.png"alt="VideoCaptioner Logo" width="100">
  <h1>VideoCaptioner</h1>
  English / [简体中文](./docs/README_CN.md)
  
  <p>An intelligent video subtitle processing assistant based on Large Language Models (LLM), supporting subtitle generation, optimization, translation and more</p>
</div>

## 📖 Project Introduction

VideoCaptioner is a powerful video subtitle configuration software. Simple to operate and requiring no high-end hardware, it utilizes large language models for intelligent subtitle segmentation, correction, optimization, and translation, adding stunning subtitles to videos with just one click.

- 🎯 Use powerful speech recognition engine without GPU, automatically generating accurate subtitles
- ✂️ LLM-based intelligent segmentation and sentence breaking for more natural and fluid subtitle reading
- 🔄 AI subtitle optimization and translation, adjusting subtitle format for more authentic and professional expression
- 🎬 Support batch video subtitle synthesis, greatly improving processing efficiency
- 📝 Intuitive subtitle editing and viewing interface for effortless subtitle adjustment

## 📸 Interface Preview

![Software Interface Preview](./docs/images/main.png)

![Page Preview](./docs/images/preview1.png)
![Page Preview](./docs/images/preview2.png)

## ✨ Main Features

The software fully leverages the contextual understanding advantages of large language models (LLM) to intelligently correct and translate speech recognition-generated subtitles. It effectively corrects typos in speech recognition, optimizes the coherence of context and consistency of noun names, making subtitles more natural and fluid with outstanding results!

Additionally, subtitle segmentation significantly impacts viewing experience, and the software's built-in LLM segmentation optimization can effectively improve sentence fluency.

### 1. Speech Recognition and Subtitle Generation
- Support online models (fast, free)
- Local Whisper model (ensures sensitive data security, offline capable)
- Integrated ffmpeg environment

### 2. Subtitle Optimization
- Intelligent typo correction
- Optimize formatting for capitalization, code, formulas, etc.
- LLM-based intelligent sentence segmentation optimization

### 3. Subtitle Translation
- Support multiple language translation
- Context-aware translation optimization
- Configurable custom LLM API

### 4. Subtitle Synthesis
- Support multiple subtitle styles
- Flexible subtitle timeline adjustment
- High-quality video export

## 🚀 Quick Start

### Windows Users

The software is lightweight, with package size less than 100M, and includes necessary environments for immediate use after download.

1. Download the latest executable from the [Release](https://github.com/WEIFENG2333/VideoCaptioner/releases) page
2. Extract and run `VideoCaptioner.exe` directly

### MacOS/Linux Users

Due to lack of Mac hardware for testing and packaging, MacOS executable is currently unavailable.

Mac users please download source code and install Python dependencies to run.

1. Install ffmpeg