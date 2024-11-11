<div align="center">
  <img src="./images/logo.png"alt="VideoCaptioner Logo" width="100">
  <h1>VideoCaptioner</h1>
  English / [简体中文](./docs/README_CN.md)
  
  <p>An intelligent video subtitle processing assistant based on Large Language Models (LLM), supporting subtitle generation, optimization, translation and more</p>
</div>

## 📖 Introduction

VideoCaptioner is a powerful video subtitle processing software. Easy to use and requiring no high-end configuration, it utilizes large language models for intelligent subtitle segmentation, correction, optimization, and translation, creating stunning subtitles for videos with just one click.

- 🎯 Powerful speech recognition engine usable without GPU, generating accurate subtitles
- ✂️ LLM-based intelligent segmentation and punctuation for more natural subtitle reading
- 🔄 Multi-threaded AI subtitle optimization and translation, improving format and expression
- 🎬 Support for batch video subtitle synthesis to enhance processing efficiency
- 📝 Intuitive subtitle editing interface with real-time preview and quick editing
- 🤖 Low model token consumption with built-in basic LLM model for out-of-box usage

## 📸 Interface Preview

<div align="center">
  <img src="./images/main.png" alt="Software Interface Preview" width="90%" style="border-radius: 5px;">
</div>

![Page Preview](./images/preview1.png)
![Page Preview](./images/preview2.png)

## ✨ Main Features

The software leverages the contextual understanding advantages of large language models (LLM) to further process speech recognition-generated subtitles. It effectively corrects typos, standardizes technical terms, and makes subtitle content more accurate and coherent, providing users with an excellent viewing experience!

### 1. Multi-Platform Video Download and Processing
- Supports major domestic and international video platforms (Bilibili, Youtube, etc.)
- Automatically extracts and processes existing video subtitles

### 2. Professional Speech Recognition Engine
- Provides multiple online recognition interfaces comparable to professional tools (Free & Fast)
- Supports local Whisper model (Privacy protection, Offline capability)

### 3. Intelligent Subtitle Optimization
- LLM-based intelligent error correction improves subtitle accuracy
- Automatic optimization of technical terms, code snippets, and mathematical formula formats
- Context-aware sentence segmentation optimization for better reading experience

### 4. High-Quality Subtitle Translation
- Context-aware intelligent translation ensures accurate and natural translations
- Uses prompts to guide LLM reflection on translations, improving quality
- Employs sequence fuzzy matching algorithm to maintain perfect timeline consistency

### 5. Subtitle Style Adjustment
- Rich subtitle style templates (Educational, News, Anime styles, etc.)
- Supports export to various subtitle video formats (SRT, ASS, VTT, TXT)

## 🚀 Quick Start

### Windows Users

The software is lightweight, with a package size under 60MB, and includes all necessary environments for immediate use after download.

1. Download the latest executable from the [Release](https://github.com/WEIFENG2333/VideoCaptioner/releases) page

2. Extract and run `VideoCaptioner.exe` directly

3. (Optional) Configure LLM API, choose whether to enable subtitle optimization or translation

4. Drag and drop video files into the software window for automatic processing


<details>
<summary>MacOS Users</summary>

Due to lack of Mac hardware for testing and packaging, no MacOS executable is currently available.

Mac users please download source code and install Python dependencies to run:
1. Install ffmpeg
```bash
brew install ffmpeg
```

2. Clone project
```bash
git clone https://github.com/WEIFENG2333/VideoCaptioner.git
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Run program
```bash
python main.py
```
</details>

### Basic Configuration

1. LLM API Configuration (Optional)

- Software includes basic language model (`gpt-4o-mini`), usable without configuration. For better results, personal API configuration is recommended.
- Supports standard OpenAI API format (Compatible with Tongyi Qianwen, DeepSeek, etc.)
- For higher quality, consider using `Claude-3.5-sonnet` or `gpt-4o`

2. Local Whisper Speech Recognition Configuration (In-app download required)

- Available models: `Tiny`, `Base`, `Small`, `Medium`, `Large-v1`, `Large-v2`
- Recommend `Medium` or above for Chinese recognition quality

3. Subtitle Style Customization

- Main/Secondary subtitle settings: font, size, color, border style, line spacing, position, etc.
- Layout options: Original text above, Translation above, Original only, Translation only

## 💡 Software Process Introduction

Complete processing flow:
```
Speech Recognition -> Subtitle Generation -> Subtitle Optimization/Translation(Optional) -> Subtitle Video Synthesis
```

## 📝 Notes

1. Subtitle segmentation quality directly affects viewing experience. I developed the [SubtitleSpliter](https://github.com/WEIFENG2333/SubtitleSpliter) project using semantic understanding technology to intelligently identify sentence boundaries and perform reasonable segmentation. For example, character-by-character subtitles are reorganized into natural language paragraphs while maintaining perfect synchronization with video.

2. To improve performance, subtitle data sent to LLM only includes text content without timeline information, significantly reducing model processing overhead. Results are fuzzy-matched with original content to ensure timeline consistency.

3. Translation process uses Andrew Ng's "translate-reflect-translate" method, ensuring good translation results and language expression habits.

## 🤝 Contribution Guidelines

As a third-year university student, both my personal abilities and the project have room for improvement. The project is continuously being refined. If you encounter bugs during use, please submit Issues and Pull Requests to help improve the project.