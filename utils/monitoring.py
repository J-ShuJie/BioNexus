"""
运行监控和日志系统
提供完整的应用运行状态监控、用户操作追踪、错误记录和性能分析
"""
import os
import logging
import time
import threading
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional
from functools import wraps


class EnhancedLogger:
    """
    增强日志记录器
    支持多种类型的日志记录和自动归档
    """
    
    def __init__(self, app_version: str = "1.1.3"):
        self.app_version = app_version
        self.start_time = time.time()
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 创建日志目录结构 - 按日期和会话组织
        self.base_dir = Path.cwd()  # BioNexus_1.1.3 目录
        self.logs_dir = self.base_dir / "logs"
        
        # 按日期创建子文件夹
        today = datetime.now().strftime("%Y-%m-%d")
        self.daily_logs_dir = self.logs_dir / today
        self.session_dir = self.daily_logs_dir / f"session_{self.session_id}"
        
        # 在会话目录下创建不同类型的日志目录
        self.archives_dir = self.logs_dir / "archives"
        self.crash_dir = self.logs_dir / "crash_reports"
        
        # 确保目录存在
        for dir_path in [self.logs_dir, self.daily_logs_dir, self.session_dir, self.archives_dir, self.crash_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # 设置不同类型的日志记录器
        self.setup_loggers()
        
        # 启动监控
        self.session_stats = {
            'start_time': datetime.now().isoformat(),
            'operations_count': 0,
            'errors_count': 0,
            'view_switches': 0,
            'tool_operations': 0
        }
        
        self.runtime_logger.info(f"=== BioNexus {app_version} 启动 ===")
        self.runtime_logger.info(f"会话ID: {self.session_id}")
        self.runtime_logger.info(f"会话目录: {self.session_dir}")
        self.runtime_logger.info(f"日志根目录: {self.logs_dir}")
    
    def setup_loggers(self):
        """设置不同类型的日志记录器"""
        
        # 通用日志格式
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # 1. 运行时日志 - 应用生命周期和系统状态
        self.runtime_logger = self._create_logger(
            'runtime', 
            self.session_dir / "runtime.log",
            formatter
        )
        
        # 2. 操作日志 - 用户操作记录
        self.operations_logger = self._create_logger(
            'operations',
            self.session_dir / "operations.log", 
            formatter
        )
        
        # 3. 错误日志 - 专门记录错误和异常
        self.error_logger = self._create_logger(
            'errors',
            self.session_dir / "errors.log",
            formatter
        )
        
        # 4. 性能日志 - 性能监控和统计
        self.performance_logger = self._create_logger(
            'performance',
            self.session_dir / "performance.log",
            formatter
        )
    
    def _create_logger(self, name: str, file_path: Path, formatter) -> logging.Logger:
        """创建指定名称和文件的日志记录器"""
        logger = logging.getLogger(f"BioNexus.{name}")
        logger.setLevel(logging.DEBUG)
        
        # 避免重复添加handler
        if not logger.handlers:
            # 文件handler
            file_handler = logging.FileHandler(file_path, encoding='utf-8')
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
            
            # 控制台handler（只对runtime日志）
            if name == 'runtime':
                console_handler = logging.StreamHandler()
                console_handler.setFormatter(formatter)
                console_handler.setLevel(logging.INFO)
                logger.addHandler(console_handler)
        
        return logger
    
    def log_startup(self, startup_info: Dict[str, Any]):
        """记录应用启动信息"""
        self.runtime_logger.info("应用启动完成")
        for key, value in startup_info.items():
            self.runtime_logger.info(f"{key}: {value}")
    
    def log_user_operation(self, operation: str, details: Dict[str, Any] = None):
        """记录用户操作"""
        self.session_stats['operations_count'] += 1
        
        msg = f"用户操作: {operation}"
        if details:
            msg += f" - {json.dumps(details, ensure_ascii=False)}"
        
        self.operations_logger.info(msg)
    
    def log_view_switch(self, from_view: str, to_view: str, success: bool = True):
        """记录视图切换"""
        self.session_stats['view_switches'] += 1
        
        if success:
            self.operations_logger.info(f"视图切换: {from_view} -> {to_view}")
        else:
            self.error_logger.error(f"视图切换失败: {from_view} -> {to_view}")
            self.session_stats['errors_count'] += 1
    
    def log_tool_operation(self, tool_name: str, operation: str, success: bool = True, details: str = ""):
        """记录工具操作"""
        self.session_stats['tool_operations'] += 1
        
        msg = f"工具操作: {tool_name} - {operation}"
        if details:
            msg += f" ({details})"
        
        if success:
            self.operations_logger.info(msg)
        else:
            self.error_logger.error(f"{msg} - 失败")
            self.session_stats['errors_count'] += 1
    
    def log_error(self, error_type: str, error_msg: str, context: Dict[str, Any] = None):
        """记录错误信息"""
        self.session_stats['errors_count'] += 1
        
        msg = f"{error_type}: {error_msg}"
        if context:
            msg += f" - 上下文: {json.dumps(context, ensure_ascii=False)}"
        
        self.error_logger.error(msg)
    
    def log_performance(self, operation: str, duration: float, details: Dict[str, Any] = None):
        """记录性能信息"""
        msg = f"性能: {operation} 耗时 {duration:.3f}s"
        if details:
            msg += f" - {json.dumps(details, ensure_ascii=False)}"
        
        self.performance_logger.info(msg)
    
    def log_system_state(self, state_info: Dict[str, Any]):
        """记录系统状态"""
        self.runtime_logger.info(f"系统状态: {json.dumps(state_info, ensure_ascii=False)}")
    
    def log_shutdown(self):
        """记录应用关闭并保存所有日志"""
        runtime = time.time() - self.start_time
        
        # 记录会话统计
        self.session_stats['end_time'] = datetime.now().isoformat()
        self.session_stats['runtime_seconds'] = round(runtime, 2)
        
        self.runtime_logger.info("=== 应用关闭 ===")
        self.runtime_logger.info(f"运行时长: {runtime:.2f}s")
        self.runtime_logger.info(f"会话统计: {json.dumps(self.session_stats, ensure_ascii=False)}")
        
        # 强制刷新所有日志缓冲区，确保内容被写入磁盘
        for logger in [self.runtime_logger, self.operations_logger, self.error_logger, self.performance_logger]:
            for handler in logger.handlers:
                handler.flush()
        
        # 保存会话统计到会话目录
        stats_file = self.session_dir / "session_summary.json"
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(self.session_stats, f, ensure_ascii=False, indent=2)
        
        # 创建会话总结文件
        summary_file = self.session_dir / "README.md"
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(f"# BioNexus 会话日志 - {self.session_id}\n\n")
            f.write(f"## 会话信息\n")
            f.write(f"- **启动时间**: {self.session_stats['start_time']}\n")
            f.write(f"- **结束时间**: {self.session_stats['end_time']}\n")
            f.write(f"- **运行时长**: {runtime:.2f} 秒\n")
            f.write(f"- **版本**: BioNexus {self.app_version}\n\n")
            f.write(f"## 操作统计\n")
            f.write(f"- **用户操作次数**: {self.session_stats['operations_count']}\n")
            f.write(f"- **视图切换次数**: {self.session_stats['view_switches']}\n")
            f.write(f"- **工具操作次数**: {self.session_stats['tool_operations']}\n")
            f.write(f"- **错误次数**: {self.session_stats['errors_count']}\n\n")
            f.write(f"## 日志文件\n")
            f.write(f"- **运行时日志**: `runtime.log`\n")
            f.write(f"- **用户操作日志**: `operations.log`\n")
            f.write(f"- **错误日志**: `errors.log`\n")
            f.write(f"- **性能日志**: `performance.log`\n")
            f.write(f"- **会话统计**: `session_summary.json`\n")
        
        self.runtime_logger.info(f"会话日志已保存到: {self.session_dir}")
        
        # 归档到archives目录（可选，用于长期存储）
        archive_file = self.archives_dir / f"session_{self.session_id}_stats.json"
        with open(archive_file, 'w', encoding='utf-8') as f:
            json.dump(self.session_stats, f, ensure_ascii=False, indent=2)
    
    def create_crash_report(self, exception_info: str):
        """创建崩溃报告"""
        crash_file = self.crash_dir / f"crash_{self.session_id}.txt"
        
        with open(crash_file, 'w', encoding='utf-8') as f:
            f.write(f"BioNexus {self.app_version} 崩溃报告\n")
            f.write(f"时间: {datetime.now().isoformat()}\n")
            f.write(f"会话ID: {self.session_id}\n")
            f.write(f"运行时长: {time.time() - self.start_time:.2f}s\n\n")
            f.write("异常信息:\n")
            f.write(exception_info)
            f.write("\n\n会话统计:\n")
            f.write(json.dumps(self.session_stats, ensure_ascii=False, indent=2))
        
        self.error_logger.critical(f"应用崩溃，崩溃报告已保存到: {crash_file}")


def performance_monitor(operation_name: str):
    """
    性能监控装饰器
    自动记录函数执行时间
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                # 如果对象有monitor属性，记录性能
                if hasattr(args[0], 'monitor') and args[0].monitor:
                    args[0].monitor.log_performance(
                        f"{func.__name__}({operation_name})", 
                        duration,
                        {'args_count': len(args), 'kwargs_count': len(kwargs)}
                    )
                
                return result
            except Exception as e:
                duration = time.time() - start_time
                
                # 记录错误
                if hasattr(args[0], 'monitor') and args[0].monitor:
                    args[0].monitor.log_error(
                        f"函数异常: {func.__name__}",
                        str(e),
                        {'operation': operation_name, 'duration': duration}
                    )
                raise
        return wrapper
    return decorator


def operation_logger(operation_name: str, details: Dict[str, Any] = None):
    """
    操作日志装饰器
    自动记录用户操作
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 记录操作开始
            if hasattr(args[0], 'monitor') and args[0].monitor:
                args[0].monitor.log_user_operation(operation_name, details)
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


# 全局监控实例
_global_monitor: Optional[EnhancedLogger] = None


def initialize_monitoring(app_version: str = "1.1.2") -> EnhancedLogger:
    """初始化全局监控系统"""
    global _global_monitor
    _global_monitor = EnhancedLogger(app_version)
    return _global_monitor


def get_monitor() -> Optional[EnhancedLogger]:
    """获取全局监控实例"""
    return _global_monitor


def cleanup_old_logs(days_to_keep: int = 7):
    """清理旧的日志文件"""
    if not _global_monitor:
        return
    
    cutoff_date = datetime.now() - timedelta(days=days_to_keep)
    
    # 清理按日期组织的旧日志目录
    for daily_dir in _global_monitor.logs_dir.glob("????-??-??"):
        if daily_dir.is_dir():
            try:
                # 检查目录的修改时间
                dir_time = datetime.fromtimestamp(daily_dir.stat().st_mtime)
                if dir_time < cutoff_date:
                    # 将整个日期目录移动到归档
                    archive_path = _global_monitor.archives_dir / daily_dir.name
                    daily_dir.rename(archive_path)
                    _global_monitor.runtime_logger.info(f"日志目录已归档: {daily_dir.name}")
            except Exception as e:
                _global_monitor.runtime_logger.warning(f"归档日志目录失败: {daily_dir.name} - {e}")
    
    # 清理旧的松散日志文件（兼容旧版本）
    for log_file in _global_monitor.logs_dir.glob("*.log"):
        if log_file.stat().st_mtime < cutoff_date.timestamp():
            try:
                # 移动到归档目录而不是删除
                archive_path = _global_monitor.archives_dir / log_file.name
                log_file.rename(archive_path)
                _global_monitor.runtime_logger.info(f"日志文件已归档: {log_file.name}")
            except Exception as e:
                _global_monitor.runtime_logger.warning(f"归档日志文件失败: {e}")