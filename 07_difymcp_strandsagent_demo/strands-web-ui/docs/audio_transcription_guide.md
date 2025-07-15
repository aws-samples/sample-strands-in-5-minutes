# 音频转录功能使用指南

## 功能概述

Strands Web UI 现在支持 MP3 音频文件的自动转录功能，集成了 AWS Transcribe 服务，支持多语言自动检测（重点支持印尼语和英语）。

## 主要特性

- 🎤 **MP3 文件上传**: 支持上传 MP3 格式的音频文件
- 🌍 **多语言检测**: 自动检测印尼语 (id-ID) 和英语 (en-US)，也支持其他语言
- 🤖 **智能体集成**: 转录结果可直接发送给 Strands Agent 进行处理
- 📝 **自定义提示**: 可以添加额外的提示词与转录内容结合
- ⚡ **实时处理**: 流式转录，实时显示结果

## 使用步骤

### 1. 准备工作

确保已安装必要的依赖：

```bash
pip install boto3 pydub amazon-transcribe
```

### 2. AWS 配置

确保你的 AWS 凭证已正确配置，可以访问 Transcribe 服务：

```bash
aws configure
```

或设置环境变量：

```bash
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_DEFAULT_REGION=ap-southeast-1
```

### 3. 使用界面

1. **启动应用**:
   ```bash
   streamlit run app.py
   ```

2. **上传音频文件**:
   - 在主界面找到 "🎤 Audio Upload & Transcription" 展开区域
   - 点击 "Choose an MP3 file" 上传你的 MP3 文件
   - 选择语言检测选项（默认：英语和印尼语）
   - 选择 AWS 区域（默认：ap-southeast-1）

3. **添加自定义提示**（可选）:
   - 在 "Additional Prompt" 文本框中输入额外的指令
   - 这些指令会与转录结果结合发送给智能体

4. **开始转录**:
   - 点击 "🎯 Transcribe Audio" 按钮
   - 等待转录完成（通常需要几秒到几分钟，取决于音频长度）

5. **查看结果**:
   - 转录完成后会显示检测到的语言和置信度
   - 转录文本会显示在文本框中

6. **发送给智能体**:
   - 点击 "📤 Send to Agent" 将转录结果发送给智能体
   - 智能体会根据系统提示词处理转录内容并给出响应

## 支持的语言

- **en-US**: 英语（美国）
- **id-ID**: 印尼语（印度尼西亚）
- **zh-CN**: 中文（简体）
- **ja-JP**: 日语
- **ko-KR**: 韩语
- **th-TH**: 泰语
- **vi-VN**: 越南语

## 配置选项

在 `config/config_with_thinking.json` 中可以配置：

```json
{
  "audio": {
    "default_region": "ap-southeast-1",
    "supported_languages": ["en-US", "id-ID"],
    "max_file_size_mb": 100
  }
}
```

## 使用场景示例

### 场景 1: 会议记录转录和总结

1. 上传会议录音 MP3 文件
2. 在自定义提示中输入："请总结这次会议的要点，并列出行动项目"
3. 点击转录并发送给智能体
4. 智能体会分析转录内容并提供会议总结

### 场景 2: 多语言客服对话分析

1. 上传客服对话录音
2. 选择印尼语和英语检测
3. 在自定义提示中输入："请分析这次客服对话，识别客户问题并提供解决方案建议"
4. 智能体会根据检测到的语言进行相应分析

### 场景 3: 语音备忘录处理

1. 上传语音备忘录
2. 在自定义提示中输入："请将这个语音备忘录整理成结构化的待办事项列表"
3. 智能体会将语音内容转换为有组织的任务列表

## 故障排除

### 常见问题

1. **转录失败**:
   - 检查 AWS 凭证配置
   - 确认 Transcribe 服务在所选区域可用
   - 检查音频文件格式是否为 MP3

2. **语言检测不准确**:
   - 尝试调整语言选项
   - 确保音频质量良好，语音清晰

3. **依赖安装问题**:
   ```bash
   pip install --upgrade boto3 pydub amazon-transcribe
   ```

4. **音频格式问题**:
   - 确保文件是有效的 MP3 格式
   - 音频质量建议：16kHz 采样率，单声道

### 日志查看

转录过程的详细日志会记录在 `logs/output.log` 文件中，可以查看具体的错误信息。

## API 参考

### 工具函数

- `transcribe_audio_file_sync(file_path, language_options, region)`: 同步转录音频文件
- `get_supported_languages()`: 获取支持的语言列表

### 配置参数

- `language_options`: 语言检测选项列表
- `region`: AWS 区域
- `additional_prompt`: 额外的提示词

## 最佳实践

1. **音频质量**: 使用清晰的录音，避免背景噪音
2. **文件大小**: 建议单个文件不超过 100MB
3. **语言选择**: 根据实际需要选择语言选项，减少不必要的语言可以提高准确性
4. **提示词设计**: 设计清晰的提示词帮助智能体更好地理解和处理转录内容

## 成本考虑

AWS Transcribe 是按使用量计费的服务，建议：

1. 监控使用量和成本
2. 在测试阶段使用较短的音频文件
3. 考虑使用 AWS 免费套餐（如果适用）

## 更新日志

- **v1.0**: 初始版本，支持 MP3 转录和多语言检测
- **v1.1**: 添加自定义提示词功能
- **v1.2**: 优化用户界面和错误处理
