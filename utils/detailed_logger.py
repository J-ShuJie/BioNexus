"""
详细日志记录系统
提供全面的错误追踪、网络请求记录、文件操作监控等功能
用于问题溯源和调试分析
"""

import os
import json
import time
import traceback
import logging
import threading
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError


class DetailedLogger:
    """详细日志记录器，记录所有操作的完整信息"""
    
    def __init__(self, log_dir: Path = None):
        """
        初始化详细日志记录器
        
        Args:
            log_dir: 日志目录，默认为logs/当前日期/session_时间戳
        """
        if log_dir is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_dir = Path("logs") / datetime.now().strftime("%Y-%m-%d") / f"session_{timestamp}"
        
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建不同类型的日志文件
        self.files = {
            'network': self.log_dir / 'network_detailed.log',
            'download': self.log_dir / 'download_detailed.log', 
            'install': self.log_dir / 'install_detailed.log',
            'error': self.log_dir / 'error_detailed.log',
            'system': self.log_dir / 'system_detailed.log',
            'trace': self.log_dir / 'trace_detailed.log'
        }
        
        # 线程锁，确保并发安全
        self.lock = threading.Lock()
        
        # 初始化日志文件
        self._init_log_files()
        
        print(f"📝 详细日志系统已启用: {self.log_dir}")
    
    def _init_log_files(self):
        """初始化所有日志文件"""
        timestamp = datetime.now().isoformat()
        
        headers = {
            'network': f"# BioNexus 网络请求详细日志 - {timestamp}\n# 记录所有HTTP请求、响应、重试等信息\n\n",
            'download': f"# BioNexus 下载详细日志 - {timestamp}\n# 记录文件下载过程、进度、错误等\n\n",
            'install': f"# BioNexus 安装详细日志 - {timestamp}\n# 记录工具安装的每个步骤\n\n",
            'error': f"# BioNexus 错误详细日志 - {timestamp}\n# 记录所有错误的完整堆栈和上下文\n\n",
            'system': f"# BioNexus 系统详细日志 - {timestamp}\n# 记录系统信息、环境变量等\n\n",
            'trace': f"# BioNexus 调用追踪日志 - {timestamp}\n# 记录关键函数调用链\n\n"
        }
        
        for log_type, file_path in self.files.items():
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(headers.get(log_type, f"# BioNexus {log_type} 日志 - {timestamp}\n\n"))
    
    def _write_log(self, log_type: str, message: str):
        """线程安全地写入日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        
        with self.lock:
            try:
                with open(self.files[log_type], 'a', encoding='utf-8') as f:
                    f.write(f"[{timestamp}] {message}\n")
                    f.flush()
            except Exception as e:
                print(f"❌ 日志写入失败 ({log_type}): {e}")
    
    def log_network_request(self, url: str, method: str = "GET", headers: Dict = None, 
                          timeout: int = None, context: str = ""):
        """记录网络请求详情"""
        request_info = {
            'url': url,
            'method': method,
            'headers': headers or {},
            'timeout': timeout,
            'context': context,
            'timestamp': time.time()
        }
        
        message = f"🌐 网络请求开始\n"
        message += f"   URL: {url}\n"
        message += f"   方法: {method}\n"
        message += f"   超时: {timeout}s\n"
        message += f"   上下文: {context}\n"
        message += f"   请求头: {json.dumps(headers or {}, ensure_ascii=False, indent=4)}\n"
        
        self._write_log('network', message)
        return request_info
    
    def log_network_response(self, request_info: Dict, response_code: int = None, 
                           response_headers: Dict = None, error: Exception = None,
                           content_length: int = None):
        """记录网络响应详情"""
        duration = time.time() - request_info['timestamp']
        
        message = f"🌐 网络请求完成 (用时: {duration:.2f}s)\n"
        message += f"   URL: {request_info['url']}\n"
        
        if error:
            message += f"   ❌ 错误: {type(error).__name__}: {str(error)}\n"
            if hasattr(error, 'code'):
                message += f"   HTTP状态码: {error.code}\n"
            if hasattr(error, 'reason'):
                message += f"   错误原因: {error.reason}\n"
        else:
            message += f"   ✅ 状态码: {response_code}\n"
            message += f"   内容大小: {content_length or '未知'} bytes\n"
            if response_headers:
                message += f"   响应头: {json.dumps(dict(response_headers), ensure_ascii=False, indent=4)}\n"
        
        self._write_log('network', message)
    
    def log_download_start(self, url: str, file_path: Path, context: str = ""):
        """记录下载开始"""
        download_info = {
            'url': url,
            'file_path': str(file_path),
            'context': context,
            'start_time': time.time()
        }
        
        message = f"📥 下载开始\n"
        message += f"   URL: {url}\n"
        message += f"   保存路径: {file_path}\n"
        message += f"   上下文: {context}\n"
        message += f"   父目录: {file_path.parent}\n"
        message += f"   父目录存在: {file_path.parent.exists()}\n"
        
        self._write_log('download', message)
        return download_info
    
    def log_download_progress(self, download_info: Dict, downloaded: int, total: int = None):
        """记录下载进度"""
        elapsed = time.time() - download_info['start_time']
        speed = downloaded / elapsed if elapsed > 0 else 0
        
        if total:
            percent = (downloaded / total) * 100
            message = f"📈 下载进度: {percent:.1f}% ({downloaded}/{total} bytes)\n"
        else:
            message = f"📈 下载进度: {downloaded} bytes\n"
        
        message += f"   速度: {speed/1024:.1f} KB/s\n"
        message += f"   用时: {elapsed:.1f}s\n"
        message += f"   文件: {download_info['file_path']}\n"
        
        self._write_log('download', message)
    
    def log_download_complete(self, download_info: Dict, success: bool, error: Exception = None, 
                            final_size: int = None):
        """记录下载完成"""
        duration = time.time() - download_info['start_time']
        
        message = f"📥 下载{'完成' if success else '失败'} (用时: {duration:.2f}s)\n"
        message += f"   URL: {download_info['url']}\n"
        message += f"   文件: {download_info['file_path']}\n"
        
        if success:
            message += f"   ✅ 最终大小: {final_size or '未知'} bytes\n"
            # 验证文件是否真的存在
            file_path = Path(download_info['file_path'])
            if file_path.exists():
                actual_size = file_path.stat().st_size
                message += f"   📁 实际文件大小: {actual_size} bytes\n"
                if final_size and actual_size != final_size:
                    message += f"   ⚠️  大小不匹配！期望: {final_size}, 实际: {actual_size}\n"
            else:
                message += f"   ❌ 文件不存在！\n"
        else:
            message += f"   ❌ 错误: {type(error).__name__}: {str(error) if error else '未知错误'}\n"
            if error:
                message += f"   堆栈: {traceback.format_exc()}\n"
        
        self._write_log('download', message)
    
    def log_install_step(self, tool_name: str, step: str, status: str, details: Dict = None):
        """记录安装步骤"""
        message = f"🔧 安装步骤: {tool_name} - {step}\n"
        message += f"   状态: {status}\n"
        
        if details:
            message += f"   详细信息: {json.dumps(details, ensure_ascii=False, indent=4)}\n"
        
        self._write_log('install', message)
    
    def log_error(self, error: Exception, context: str = "", additional_info: Dict = None):
        """记录错误详情"""
        message = f"❌ 错误发生\n"
        message += f"   类型: {type(error).__name__}\n"
        message += f"   消息: {str(error)}\n"
        message += f"   上下文: {context}\n"
        
        if additional_info:
            message += f"   附加信息: {json.dumps(additional_info, ensure_ascii=False, indent=4)}\n"
        
        # 获取完整堆栈
        stack_trace = traceback.format_exc()
        message += f"   完整堆栈:\n{stack_trace}\n"
        
        self._write_log('error', message)
    
    def log_system_info(self, info_type: str, info_data: Dict):
        """记录系统信息"""
        message = f"💻 系统信息: {info_type}\n"
        message += f"   数据: {json.dumps(info_data, ensure_ascii=False, indent=4)}\n"
        
        self._write_log('system', message)
    
    def log_function_call(self, func_name: str, args: tuple = None, kwargs: Dict = None, 
                         result: Any = None, duration: float = None):
        """记录函数调用"""
        message = f"🔍 函数调用: {func_name}\n"
        
        if args:
            message += f"   位置参数: {str(args)}\n"
        
        if kwargs:
            message += f"   关键字参数: {json.dumps(kwargs, ensure_ascii=False, default=str)}\n"
        
        if duration is not None:
            message += f"   执行时间: {duration:.4f}s\n"
        
        if result is not None:
            result_str = str(result)
            if len(result_str) > 500:
                result_str = result_str[:500] + "..."
            message += f"   返回值: {result_str}\n"
        
        self._write_log('trace', message)
    
    def create_debug_summary(self) -> str:
        """创建调试摘要，返回关键信息"""
        summary_file = self.log_dir / 'debug_summary.txt'
        
        summary = f"BioNexus 调试摘要 - {datetime.now().isoformat()}\n"
        summary += "=" * 60 + "\n\n"
        
        # 统计各类日志数量
        for log_type, file_path in self.files.items():
            if file_path.exists():
                line_count = sum(1 for _ in open(file_path, 'r', encoding='utf-8'))
                summary += f"{log_type.upper()} 日志: {line_count} 行\n"
        
        summary += f"\n详细日志目录: {self.log_dir}\n"
        summary += "=" * 60 + "\n"
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(summary)
        
        return str(summary_file)


# 全局日志实例
_global_logger = None

def get_detailed_logger() -> DetailedLogger:
    """获取全局详细日志实例"""
    global _global_logger
    if _global_logger is None:
        _global_logger = DetailedLogger()
    return _global_logger

def init_detailed_logging(log_dir: Path = None) -> DetailedLogger:
    """初始化详细日志系统"""
    global _global_logger
    _global_logger = DetailedLogger(log_dir)
    return _global_logger