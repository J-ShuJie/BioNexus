"""
全面的日志记录系统 v1.2.9
确保捕获所有错误和重要信息，包括PyQt5信号、槽错误等
"""

import sys
import os
import logging
import traceback
import threading
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
import json

# 确保PyQt5可用时捕获Qt相关错误
try:
    from PyQt5.QtCore import qInstallMessageHandler, QtMsgType
    HAS_QT = True
except ImportError:
    HAS_QT = False


class ComprehensiveLogger:
    """全面的日志记录系统"""
    
    def __init__(self, app_version: str = "1.2.9"):
        self.app_version = app_version
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 创建日志目录
        self.log_dir = Path(__file__).parent.parent / "logs" / datetime.now().strftime("%Y-%m-%d") / f"session_{self.session_id}"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # 线程锁
        self.lock = threading.Lock()
        
        # 各种日志文件
        self.log_files = {
            'startup': self.log_dir / 'startup.log',
            'runtime': self.log_dir / 'runtime.log', 
            'errors': self.log_dir / 'errors.log',
            'qt_errors': self.log_dir / 'qt_errors.log',
            'ui_operations': self.log_dir / 'ui_operations.log',
            'system_info': self.log_dir / 'system_info.log',
            'performance': self.log_dir / 'performance.log',
            'debug': self.log_dir / 'debug.log'
        }
        
        # 初始化所有日志记录器
        self._setup_python_logging()
        self._setup_global_exception_handler()
        if HAS_QT:
            self._setup_qt_logging()
        
        # 记录会话开始信息
        self._log_session_start()
    
    def _setup_python_logging(self):
        """设置Python标准日志系统"""
        # 设置根日志级别
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.log_files['runtime'], encoding='utf-8'),
                logging.StreamHandler()  # 同时输出到控制台
            ]
        )
        
        # 为不同模块设置专门的处理器
        self.loggers = {}
        for log_type in ['startup', 'errors', 'ui_operations', 'performance', 'debug']:
            logger = logging.getLogger(f'BioNexus.{log_type}')
            handler = logging.FileHandler(self.log_files[log_type], encoding='utf-8')
            handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            logger.addHandler(handler)
            logger.setLevel(logging.DEBUG)
            self.loggers[log_type] = logger
    
    def _setup_global_exception_handler(self):
        """设置全局异常处理器"""
        original_excepthook = sys.excepthook
        
        def enhanced_excepthook(exc_type, exc_value, exc_traceback):
            if issubclass(exc_type, KeyboardInterrupt):
                sys.__excepthook__(exc_type, exc_value, exc_traceback)
                return
            
            # 记录详细错误信息
            self.log_critical_error(exc_type, exc_value, exc_traceback)
            
            # 调用原始处理器
            original_excepthook(exc_type, exc_value, exc_traceback)
        
        sys.excepthook = enhanced_excepthook
    
    def _setup_qt_logging(self):
        """设置Qt消息处理器"""
        def qt_message_handler(msg_type, context, message):
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # 确定消息级别
            if msg_type == QtMsgType.QtDebugMsg:
                level = "DEBUG"
            elif msg_type == QtMsgType.QtInfoMsg:
                level = "INFO"
            elif msg_type == QtMsgType.QtWarningMsg:
                level = "WARNING"
            elif msg_type == QtMsgType.QtCriticalMsg:
                level = "CRITICAL"
            elif msg_type == QtMsgType.QtFatalMsg:
                level = "FATAL"
            else:
                level = "UNKNOWN"
            
            # 记录Qt消息
            qt_log_entry = f"[{timestamp}] {level}: {message}"
            if context and hasattr(context, 'file') and context.file:
                qt_log_entry += f" (文件: {context.file}:{context.line})"
            
            self._write_to_file('qt_errors', qt_log_entry)
            
            # 严重错误也记录到主错误日志
            if msg_type in [QtMsgType.QtCriticalMsg, QtMsgType.QtFatalMsg]:
                self.log_error("Qt严重错误", message, {
                    'type': level,
                    'context': str(context) if context else None
                })
        
        qInstallMessageHandler(qt_message_handler)
    
    def _log_session_start(self):
        """记录会话开始信息"""
        start_info = {
            'session_id': self.session_id,
            'app_version': self.app_version,
            'python_version': sys.version,
            'platform': sys.platform,
            'log_directory': str(self.log_dir),
            'start_time': datetime.now().isoformat()
        }
        
        self._write_to_file('system_info', f"=== BioNexus {self.app_version} 会话开始 ===")
        for key, value in start_info.items():
            self._write_to_file('system_info', f"{key}: {value}")
        
        self.loggers['startup'].info(f"BioNexus {self.app_version} 启动 - 会话ID: {self.session_id}")
    
    def _write_to_file(self, log_type: str, message: str):
        """线程安全地写入日志文件"""
        with self.lock:
            try:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                log_entry = f"[{timestamp}] {message}\n"
                
                with open(self.log_files.get(log_type, self.log_files['runtime']), 'a', encoding='utf-8') as f:
                    f.write(log_entry)
                    f.flush()
            except Exception as e:
                print(f"日志写入失败 ({log_type}): {e}")
    
    def log_startup_phase(self, phase: str, details: str = "", success: bool = True):
        """记录启动阶段"""
        status = "成功" if success else "失败"
        message = f"启动阶段 - {phase}: {status}"
        if details:
            message += f" - {details}"
        
        self._write_to_file('startup', message)
        self.loggers['startup'].info(message)
    
    def log_error(self, error_type: str, message: str, context: Dict = None):
        """记录错误"""
        error_info = {
            'timestamp': datetime.now().isoformat(),
            'type': error_type,
            'message': message,
            'context': context or {}
        }
        
        error_text = f"错误 - {error_type}: {message}"
        if context:
            error_text += f" | 上下文: {json.dumps(context, ensure_ascii=False)}"
        
        self._write_to_file('errors', error_text)
        self.loggers['errors'].error(error_text)
    
    def log_critical_error(self, exc_type, exc_value, exc_traceback):
        """记录严重错误"""
        error_details = {
            'timestamp': datetime.now().isoformat(),
            'exception_type': exc_type.__name__,
            'exception_message': str(exc_value),
            'traceback': ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback)),
            'session_id': self.session_id
        }
        
        # 写入详细错误日志
        self._write_to_file('errors', f"=== 严重错误 ===")
        self._write_to_file('errors', f"类型: {error_details['exception_type']}")
        self._write_to_file('errors', f"消息: {error_details['exception_message']}")
        self._write_to_file('errors', f"堆栈追踪:\n{error_details['traceback']}")
        self._write_to_file('errors', "=" * 60)
        
        # 创建崩溃报告
        crash_file = self.log_dir / f"crash_report_{self.session_id}.json"
        try:
            with open(crash_file, 'w', encoding='utf-8') as f:
                json.dump(error_details, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"无法创建崩溃报告: {e}")
    
    def log_ui_operation(self, operation: str, component: str, details: Dict = None):
        """记录UI操作"""
        ui_message = f"UI操作 - {component}: {operation}"
        if details:
            ui_message += f" | 详情: {json.dumps(details, ensure_ascii=False)}"
        
        self._write_to_file('ui_operations', ui_message)
        self.loggers['ui_operations'].info(ui_message)
    
    def log_performance(self, operation: str, duration_ms: float, details: Dict = None):
        """记录性能信息"""
        perf_message = f"性能 - {operation}: {duration_ms:.2f}ms"
        if details:
            perf_message += f" | 详情: {json.dumps(details, ensure_ascii=False)}"
        
        self._write_to_file('performance', perf_message)
        self.loggers['performance'].info(perf_message)
    
    def log_debug(self, component: str, message: str, data: Any = None):
        """记录调试信息"""
        debug_message = f"调试 - {component}: {message}"
        if data is not None:
            debug_message += f" | 数据: {json.dumps(data, ensure_ascii=False, default=str)}"
        
        self._write_to_file('debug', debug_message)
        self.loggers['debug'].debug(debug_message)
    
    def log_module_import(self, module_name: str, success: bool, error_msg: str = ""):
        """记录模块导入"""
        status = "成功" if success else "失败"
        message = f"模块导入 - {module_name}: {status}"
        if error_msg:
            message += f" - {error_msg}"
        
        self._write_to_file('startup', message)
        if success:
            self.loggers['startup'].info(message)
        else:
            self.loggers['startup'].error(message)
    
    def create_summary_report(self):
        """创建会话总结报告"""
        summary_file = self.log_dir / "session_summary.txt"
        
        try:
            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write(f"BioNexus {self.app_version} 会话总结\n")
                f.write(f"会话ID: {self.session_id}\n")
                f.write(f"开始时间: {datetime.now().isoformat()}\n")
                f.write("=" * 50 + "\n\n")
                
                # 统计各类日志数量
                for log_type, log_file in self.log_files.items():
                    if log_file.exists():
                        try:
                            with open(log_file, 'r', encoding='utf-8') as lf:
                                lines = len(lf.readlines())
                            f.write(f"{log_type}日志: {lines} 条记录\n")
                        except:
                            f.write(f"{log_type}日志: 无法读取\n")
                
                f.write(f"\n日志目录: {self.log_dir}\n")
            
            return str(summary_file)
        except Exception as e:
            print(f"无法创建总结报告: {e}")
            return None
    
    def close_session(self):
        """关闭会话"""
        self._write_to_file('system_info', f"=== 会话结束: {datetime.now().isoformat()} ===")
        self.create_summary_report()


# 全局实例
_comprehensive_logger = None


def get_comprehensive_logger() -> ComprehensiveLogger:
    """获取全局日志实例"""
    global _comprehensive_logger
    if _comprehensive_logger is None:
        _comprehensive_logger = ComprehensiveLogger()
    return _comprehensive_logger


def init_comprehensive_logging(app_version: str = "1.2.9") -> ComprehensiveLogger:
    """初始化全面日志系统"""
    global _comprehensive_logger
    _comprehensive_logger = ComprehensiveLogger(app_version)
    return _comprehensive_logger


def log_module_import_attempt(module_name: str):
    """装饰器：记录模块导入尝试"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger = get_comprehensive_logger()
            try:
                result = func(*args, **kwargs)
                logger.log_module_import(module_name, True)
                return result
            except Exception as e:
                logger.log_module_import(module_name, False, str(e))
                raise
        return wrapper
    return decorator


# 上下文管理器用于性能监控
class PerformanceTimer:
    def __init__(self, operation_name: str, logger: ComprehensiveLogger = None):
        self.operation_name = operation_name
        self.logger = logger or get_comprehensive_logger()
        self.start_time = None
    
    def __enter__(self):
        import time
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        import time
        duration = (time.time() - self.start_time) * 1000
        self.logger.log_performance(self.operation_name, duration)