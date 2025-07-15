#!/usr/bin/env python3
"""
Entry point for the Strands Web UI application.

This is a simple entry point script that imports and runs the main application
from the strands_web_ui package.
"""

import sys
import os

# 使用自定义的过滤输出流，保留交互式提示在控制台
from strands_web_ui.utils.custom_logger import setup_filtered_output

# 确保日志目录存在
os.makedirs('logs', exist_ok=True)

# 设置过滤输出流，将事件日志写入文件，保留交互式提示在控制台
setup_filtered_output('logs/output.log', 'logs/error.log')

from strands_web_ui.app import main

if __name__ == "__main__":
    main()
