"""
错误处理和异常日志记录模块
提供全局异常捕获和详细的错误日志记录
"""

import sys
import traceback
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Any


class ErrorHandler:
    """
    全局错误处理器
    捕获并记录所有未处理的异常
    """
    
    def __init__(self, log_dir: Optional[Path] = None):
        """
        初始化错误处理器
        
        Args:
            log_dir: 日志目录路径
        """
        if log_dir is None:
            project_root = Path(__file__).parent.parent
            log_dir = project_root / "logs"
        
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # 错误日志文件
        error_log_name = datetime.now().strftime("errors_%Y%m%d.log")
        self.error_log = self.log_dir / error_log_name
        
        # 崩溃日志文件
        self.crash_log = self.log_dir / "crash.log"
        
        self.logger = logging.getLogger("BioNexus.ErrorHandler")
        
    def setup_global_handler(self):
        """设置全局异常处理器"""
        sys.excepthook = self._handle_uncaught_exception
        
    def _handle_uncaught_exception(self, exc_type, exc_value, exc_traceback):
        """
        处理未捕获的异常
        
        Args:
            exc_type: 异常类型
            exc_value: 异常值
            exc_traceback: 异常堆栈
        """
        if issubclass(exc_type, KeyboardInterrupt):
            # 忽略键盘中断
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        # 格式化异常信息
        error_msg = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 记录到错误日志
        self._write_error_log(exc_type.__name__, str(exc_value), error_msg)
        
        # 记录到崩溃日志
        self._write_crash_log(error_msg)
        
        # 输出到控制台
        print(f"\n{'='*60}")
        print(f"时间: {timestamp}")
        print(f"错误类型: {exc_type.__name__}")
        print(f"错误消息: {exc_value}")
        print(f"堆栈追踪:")
        print(error_msg)
        print('='*60)
        
        # 调用系统默认异常处理器
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
    
    def _write_error_log(self, error_type: str, error_msg: str, traceback_str: str):
        """写入错误日志"""
        try:
            with open(self.error_log, 'a', encoding='utf-8') as f:
                f.write(f"\n{'='*60}\n")
                f.write(f"时间: {datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')}\n")
                f.write(f"错误类型: {error_type}\n")
                f.write(f"错误消息: {error_msg}\n")
                f.write(f"堆栈追踪:\n{traceback_str}")
                f.write(f"{'='*60}\n\n")
                f.flush()
        except Exception as e:
            print(f"无法写入错误日志: {e}")
    
    def _write_crash_log(self, error_msg: str):
        """写入崩溃日志"""
        try:
            with open(self.crash_log, 'a', encoding='utf-8') as f:
                f.write(f"\n崩溃时间: {datetime.now().isoformat()}\n")
                f.write(f"错误信息:\n{error_msg}\n")
                f.write("-" * 80 + "\n")
                f.flush()
        except Exception as e:
            print(f"无法写入崩溃日志: {e}")
    
    def log_error(self, error_type: str, error_msg: str, context: dict = None):
        """手动记录错误"""
        traceback_info = traceback.format_stack()
        traceback_str = ''.join(traceback_info)
        self._write_error_log(error_type, error_msg, f"手动记录的错误, 上下文: {context}\n堆栈:\n{traceback_str}")
        self.logger.error(f"{error_type}: {error_msg}", extra={'context': context})
    
    def log_exception(self, exception: Exception, context: str = ""):
        """
        记录异常信息
        
        Args:
            exception: 异常对象
            context: 上下文描述
        """
        error_info = {
            'timestamp': datetime.now().isoformat(),
            'type': type(exception).__name__,
            'message': str(exception),
            'context': context,
            'traceback': traceback.format_exc()
        }
        
        self.log_error(error_info)
        self.logger.error(f"{context}: {type(exception).__name__}: {exception}")
    
    def create_error_report(self) -> str:
        """
        创建错误报告
        
        Returns:
            错误报告的文件路径
        """
        report_file = self.log_dir / f"error_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write("BioNexus 错误报告\n")
                f.write(f"生成时间: {datetime.now().isoformat()}\n")
                f.write("="*60 + "\n\n")
                
                # 包含最近的错误日志
                if self.error_log.exists():
                    f.write("最近的错误:\n")
                    f.write("-"*40 + "\n")
                    with open(self.error_log, 'r', encoding='utf-8') as error_f:
                        # 只取最后5000字符
                        content = error_f.read()
                        if len(content) > 5000:
                            content = "..." + content[-5000:]
                        f.write(content)
                
                f.write("\n" + "="*60 + "\n")
                f.write("报告结束\n")
            
            return str(report_file)
            
        except Exception as e:
            self.logger.error(f"创建错误报告失败: {e}")
            return ""


# 全局错误处理器实例
_error_handler = None


def initialize_error_handler(log_dir: Optional[Path] = None):
    """
    初始化全局错误处理器
    
    Args:
        log_dir: 日志目录路径
    """
    global _error_handler
    _error_handler = ErrorHandler(log_dir)
    _error_handler.setup_global_handler()
    return _error_handler


def get_error_handler() -> ErrorHandler:
    """
    获取全局错误处理器实例
    
    Returns:
        ErrorHandler实例
    """
    global _error_handler
    if _error_handler is None:
        _error_handler = ErrorHandler()
    return _error_handler


def log_exception(exception: Exception, context: str = ""):
    """
    快捷函数：记录异常
    
    Args:
        exception: 异常对象
        context: 上下文描述
    """
    handler = get_error_handler()
    handler.log_exception(exception, context)