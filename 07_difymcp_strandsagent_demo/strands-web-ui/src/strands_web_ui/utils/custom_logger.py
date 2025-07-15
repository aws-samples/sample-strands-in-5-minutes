"""
Custom logger for Strands Web UI.

This module provides a custom output stream class that can filter and redirect
output based on content, allowing event logs to go to files while keeping
interactive prompts visible in the console.
"""

import sys
import re
import os
import time
from typing import TextIO, Optional, Dict, Set

class FilteredOutputStream:
    """
    A custom output stream that filters content and redirects it to different destinations.
    
    This class allows:
    - Event logs and debug information to be written to log files
    - Interactive prompts and user-facing messages to remain visible in the console
    """
    
    def __init__(self, log_file: TextIO, original_stream: TextIO, is_stderr: bool = False):
        """
        Initialize the filtered output stream.
        
        Args:
            log_file: The file object to write logs to
            original_stream: The original stream (sys.stdout or sys.stderr)
            is_stderr: Whether this is for stderr (True) or stdout (False)
        """
        self.log_file = log_file
        self.original_stream = original_stream
        self.is_stderr = is_stderr
        
        # Patterns that indicate event logs (should go to file only)
        self.event_patterns = [
            r'\[ReAct -',
            r'\[COMPLETE MESSAGE\]',
            r'\[COMPLETE DELTA CONTENT\]',
            r'===== TOOL EXECUTION LOGS =====',
            r'===== END TOOL EXECUTION LOGS =====',
            r'Available tools on agent:',
            r'Processing user input:',
            r'Agent response type:',
            r'Agent response:',
            r'ERROR in agent execution:',
            r'Error type:',
            r'Calling agent with user input...',  # 添加这个模式以防止重复
        ]
        
        # Patterns that indicate interactive prompts (should go to console)
        self.interactive_patterns = [
            r'Do you want to execute',
            r'Are you sure you want to',
            r'This command may be dangerous',
            r'Please confirm',
            r'Proceed with',
            r'\[y/n\]',
            r'Press Enter to continue',
            r'Type "yes" to confirm',
        ]
        
        # 防止重复日志的缓存
        self.recent_logs: Dict[str, float] = {}
        self.log_expiry_time = 1.0  # 1秒内相同的日志被视为重复
        
    def write(self, text: str) -> None:
        """
        Write text to the appropriate output stream(s).
        
        Args:
            text: The text to write
        """
        # 检查是否是重复日志
        if text.strip() and not self.is_stderr:
            current_time = time.time()
            # 清理过期的日志记录
            expired_logs = [log for log, timestamp in self.recent_logs.items() 
                           if current_time - timestamp > self.log_expiry_time]
            for log in expired_logs:
                del self.recent_logs[log]
                
            # 检查是否是最近看到的相同日志
            if text in self.recent_logs:
                # 这是一个重复日志，更新时间戳但不写入文件
                self.recent_logs[text] = current_time
                return
            
            # 记录这个新日志
            self.recent_logs[text] = current_time
        
        # 写入日志文件
        self.log_file.write(text)
        self.log_file.flush()
        
        # 检查是否是事件日志
        is_event_log = any(re.search(pattern, text) for pattern in self.event_patterns)
        
        # 检查是否是交互式提示
        is_interactive = any(re.search(pattern, text) for pattern in self.interactive_patterns)
        
        # 写入控制台条件:
        # 1. 是交互式提示，或
        # 2. 是stderr（确保错误可见），或
        # 3. 不是事件日志
        if is_interactive or self.is_stderr or not is_event_log:
            self.original_stream.write(text)
            self.original_stream.flush()
    
    def flush(self) -> None:
        """Flush both output streams."""
        self.log_file.flush()
        self.original_stream.flush()
    
    def isatty(self) -> bool:
        """Return whether the original stream is connected to a terminal."""
        return self.original_stream.isatty()
    
    def fileno(self) -> int:
        """Return the file descriptor of the original stream."""
        return self.original_stream.fileno()


def setup_filtered_output(stdout_path: str = 'logs/output.log', 
                         stderr_path: str = 'logs/error.log') -> None:
    """
    Set up filtered output streams for stdout and stderr.
    
    Args:
        stdout_path: Path to the stdout log file
        stderr_path: Path to the stderr log file
    """
    # 确保日志目录存在
    os.makedirs(os.path.dirname(stdout_path), exist_ok=True)
    
    # 保存原始流
    original_stdout = sys.stdout
    original_stderr = sys.stderr
    
    # 打开日志文件，使用 'w' 模式清空旧内容
    stdout_file = open(stdout_path, 'w')
    stderr_file = open(stderr_path, 'w')
    
    # 写入会话开始标记
    session_start = f"\n{'='*50}\nSession started at {time.strftime('%Y-%m-%d %H:%M:%S')}\n{'='*50}\n\n"
    stdout_file.write(session_start)
    stderr_file.write(session_start)
    
    # 创建并设置过滤输出流
    sys.stdout = FilteredOutputStream(stdout_file, original_stdout, is_stderr=False)
    sys.stderr = FilteredOutputStream(stderr_file, original_stderr, is_stderr=True)
