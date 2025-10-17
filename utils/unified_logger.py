"""
统一日志系统 v1.1.12
合并所有重复的日志系统，提供简洁高效的日志功能
替代: enhanced_logger, detailed_logger, monitoring 等重复实现
"""

import os
import json
import time
import logging
import threading
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from contextlib import contextmanager


class UnifiedLogger:
    """
    统一的日志管理器
    合并所有日志功能：运行时、错误、性能、安装、网络等
    """
    
    def __init__(self, session_id: str = None, log_dir: Path = None):
        """初始化统一日志系统"""
        self.session_id = session_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 使用项目本地的logs目录，而不是相对路径
        if log_dir is None:
            # 获取项目根目录
            project_root = Path(__file__).parent.parent
            log_dir = project_root / "logs" / datetime.now().strftime("%Y-%m-%d") / f"session_{self.session_id}"
        
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # 线程安全锁
        self.lock = threading.Lock()
        
        # 会话统计
        self.session_stats = {
            'start_time': datetime.now().isoformat(),
            'operations_count': 0,
            'errors_count': 0,
            'installations': 0,
            'network_requests': 0
        }
        
        # 日志文件映射
        self.log_files = {
            'runtime': self.log_dir / 'runtime.log',
            'errors': self.log_dir / 'errors.log', 
            'operations': self.log_dir / 'operations.log',
            'install': self.log_dir / 'install.log',
            'network': self.log_dir / 'network.log'
        }
        
        # 初始化Python日志
        self._setup_python_logging()
        
        # 记录会话开始
        self.log_runtime("=== BioNexus 1.1.12 启动 ===")
        self.log_runtime(f"会话ID: {self.session_id}")
        self.log_runtime(f"日志目录: {self.log_dir}")
        
    def _setup_python_logging(self):
        """设置标准Python日志"""
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)
        
        # 创建格式器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # 文件处理器
        file_handler = logging.FileHandler(self.log_files['runtime'], encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
    def _write_log(self, log_type: str, message: str):
        """线程安全写入日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f")[:-3]
        log_entry = f"{timestamp} - BioNexus.{log_type} - {message}\n"
        
        with self.lock:
            try:
                with open(self.log_files.get(log_type, self.log_files['runtime']), 'a', encoding='utf-8') as f:
                    f.write(log_entry)
                    f.flush()
            except Exception as e:
                print(f"日志写入失败 ({log_type}): {e}")
    
    def log_runtime(self, message: str, level: str = "INFO"):
        """记录运行时信息"""
        self._write_log('runtime', f"{level} - {message}")
        
    def log_error(self, error_type: str, message: str, context: Dict = None):
        """记录错误信息"""
        error_msg = f"ERROR - {error_type}: {message}"
        if context:
            error_msg += f" - 上下文: {json.dumps(context, ensure_ascii=False)}"
        
        self._write_log('errors', error_msg)
        self.session_stats['errors_count'] += 1
        
    def log_operation(self, operation: str, details: Dict = None):
        """记录用户操作"""
        op_msg = f"INFO - 用户操作: {operation}"
        if details:
            op_msg += f" - {json.dumps(details, ensure_ascii=False)}"
        
        self._write_log('operations', op_msg)
        self.session_stats['operations_count'] += 1
        
    def log_installation(self, tool_name: str, step: str, status: str, details: Dict = None):
        """记录安装过程"""
        install_msg = f"INFO - 安装: {tool_name} - {step} - {status}"
        if details:
            install_msg += f" - {json.dumps(details, ensure_ascii=False)}"
        
        self._write_log('install', install_msg)
        if status == '完成':
            self.session_stats['installations'] += 1
            
    def log_network(self, url: str, method: str, status_code: int = None, duration: float = None):
        """记录网络请求"""
        net_msg = f"INFO - 网络请求: {method} {url}"
        if status_code:
            net_msg += f" - 状态码: {status_code}"
        if duration:
            net_msg += f" - 用时: {duration:.2f}s"
        
        self._write_log('network', net_msg)
        self.session_stats['network_requests'] += 1
    
    def log_view_switch(self, from_view: str, to_view: str, success: bool = True):
        """记录视图切换"""
        status = "成功" if success else "失败"
        view_msg = f"INFO - 视图切换: {from_view} → {to_view} - {status}"
        
        self._write_log('operations', view_msg)
        self.session_stats['operations_count'] += 1
    
    def log_user_operation(self, operation: str, details: dict = None):
        """记录用户操作（与log_operation相同，为了兼容性）"""
        self.log_operation(operation, details)
    
    def log_tool_operation(self, tool_name: str, operation: str, success: bool = True, details: str = ""):
        """记录工具操作"""
        status = "成功" if success else "失败"
        tool_msg = f"INFO - 工具操作: {tool_name} - {operation} - {status}"
        if details:
            tool_msg += f" ({details})"
        
        self._write_log('operations', tool_msg)
        self.session_stats['operations_count'] += 1
        if not success:
            self.session_stats['errors_count'] += 1
    
    def log_performance(self, operation: str, duration: float):
        """记录性能信息"""
        perf_msg = f"INFO - 性能: {operation} 用时 {duration:.3f}s"
        self._write_log('runtime', perf_msg)
    
    def create_crash_report(self, error_info: str):
        """创建崩溃报告"""
        crash_msg = f"CRITICAL - 应用崩溃: {error_info}"
        self._write_log('errors', crash_msg)
        
        # 创建独立的崩溃报告文件
        crash_file = self.log_dir / f"crash_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        try:
            with open(crash_file, 'w', encoding='utf-8') as f:
                f.write(f"BioNexus 崩溃报告\n")
                f.write(f"时间: {datetime.now().isoformat()}\n")
                f.write(f"会话ID: {self.session_id}\n")
                f.write(f"错误信息: {error_info}\n")
                f.write(f"会话统计: {json.dumps(self.session_stats, ensure_ascii=False, indent=2)}\n")
        except Exception as e:
            self.log_error("崩溃报告创建失败", str(e))
    
    def log_shutdown(self):
        """记录应用关闭"""
        self.session_stats['end_time'] = datetime.now().isoformat()
        shutdown_msg = f"INFO - 应用关闭"
        self._write_log('runtime', shutdown_msg)
        
        # 保存会话统计
        stats_file = self.log_dir / 'session_stats.json'
        try:
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(self.session_stats, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.log_error("会话统计保存失败", str(e))
    
    @contextmanager
    def performance_timer(self, operation: str):
        """性能计时上下文管理器"""
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            self.log_runtime(f"性能: {operation} 用时 {duration:.3f}s")
    
    def log_startup(self, info: Dict):
        """记录启动信息"""
        for key, value in info.items():
            self.log_runtime(f"{key}: {value}")
        self.log_runtime("应用启动完成")
    
    def log_user_operation(self, operation: str, details: Dict = None):
        """记录用户操作（兼容接口）"""
        self.log_operation(operation, details)
    
    def log_tool_operation(self, tool_name: str, operation: str, status: str, details=None):
        """记录工具操作（兼容接口）"""
        if isinstance(details, dict):
            op_details = details.copy()
        elif isinstance(details, str):
            op_details = {'message': details}
        else:
            op_details = {}
        
        op_details.update({
            'tool': tool_name,
            'status': status
        })
        self.log_operation(f"工具操作: {tool_name} - {operation}", op_details)
    
    def log_shutdown(self):
        """记录关闭信息"""
        end_time = datetime.now()
        start_time = datetime.fromisoformat(self.session_stats['start_time'])
        duration = (end_time - start_time).total_seconds()
        
        self.log_runtime("=== 应用关闭 ===")
        self.log_runtime(f"运行时长: {duration:.2f}s")
        
        # 更新会话统计
        self.session_stats.update({
            'end_time': end_time.isoformat(),
            'runtime_seconds': duration
        })
        
        self.log_runtime(f"会话统计: {json.dumps(self.session_stats, ensure_ascii=False)}")
        self.log_runtime(f"会话日志已保存到: {self.log_dir}")
    
    def create_crash_report(self, error_msg: str):
        """创建崩溃报告（兼容接口）"""
        crash_file = self.log_dir / 'crash_report.txt'
        try:
            with open(crash_file, 'w', encoding='utf-8') as f:
                f.write(f"BioNexus 1.1.12 崩溃报告\n")
                f.write(f"时间: {datetime.now().isoformat()}\n")
                f.write(f"会话ID: {self.session_id}\n")
                f.write("-" * 50 + "\n")
                f.write(error_msg)
            self.log_error('崩溃报告', f'已生成: {crash_file}')
        except Exception as e:
            self.log_error('崩溃报告', f'生成失败: {e}')


# 全局单例
_global_logger: Optional[UnifiedLogger] = None

def get_logger() -> UnifiedLogger:
    """获取全局日志实例"""
    global _global_logger
    if _global_logger is None:
        _global_logger = UnifiedLogger()
    return _global_logger

def init_logger(session_id: str = None, log_dir: Path = None) -> UnifiedLogger:
    """初始化全局日志实例"""
    global _global_logger
    _global_logger = UnifiedLogger(session_id, log_dir)
    return _global_logger

# 向后兼容的函数
def initialize_monitoring(version: str) -> UnifiedLogger:
    """兼容旧的监控初始化接口"""
    logger = get_logger()
    logger.log_runtime(f"BioNexus版本: {version}")
    return logger

def get_monitor() -> UnifiedLogger:
    """兼容旧的监控获取接口"""
    return get_logger()

def get_enhanced_monitor() -> UnifiedLogger:
    """兼容enhanced_logger接口"""
    return get_logger()

class CompatibilityWrapper:
    """兼容性包装器，提供旧接口的兼容"""
    
    def __init__(self, logger: UnifiedLogger):
        self.logger = logger
    
    def get_logger(self, log_type: str):
        """兼容enhanced_logger的get_logger"""
        return self.logger
    
    def log(self, level: str, event: str, data: Dict):
        """兼容enhanced_logger的log方法"""
        if level == 'ERROR':
            self.logger.log_error(event, str(data))
        elif event == 'download_start':
            self.logger.log_installation(data.get('source', 'Unknown'), '下载开始', '进行中', data)
        else:
            self.logger.log_runtime(f"{event}: {json.dumps(data, ensure_ascii=False)}")
    
    def log_startup(self, info: Dict):
        """兼容监控系统启动日志"""
        self.logger.log_startup(info)
    
    def log_shutdown(self):
        """兼容监控系统关闭日志"""
        self.logger.log_shutdown()
    
    def log_user_operation(self, operation: str, details: Dict):
        """兼容用户操作日志"""
        self.logger.log_operation(operation, details)
    
    def log_error(self, error_type: str, message: str, context: Dict = None):
        """兼容错误日志"""
        self.logger.log_error(error_type, message, context)

# 为兼容性提供包装实例
def get_enhanced_monitor():
    """返回兼容的监控实例"""
    return CompatibilityWrapper(get_logger())

# 兼容性装饰器
def performance_monitor(operation_name: str):
    """性能监控装饰器（兼容版本）"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger = get_logger()
            with logger.performance_timer(operation_name):
                return func(*args, **kwargs)
        return wrapper
    return decorator

def operation_logger(operation_name: str):
    """操作日志装饰器（兼容版本）"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger = get_logger()
            logger.log_operation(operation_name, {"function": func.__name__})
            return func(*args, **kwargs)
        return wrapper
    return decorator