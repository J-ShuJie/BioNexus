"""
增强型日志系统 v1.1.10
支持结构化日志、详细的网络和系统信息记录
"""
import os
import json
import platform
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Union
from enum import Enum


class LogLevel(Enum):
    """日志级别枚举"""
    TRACE = 5    # 极详细的调试信息
    DEBUG = 10   # 调试信息
    INFO = 20    # 正常流程
    WARN = 30    # 警告但继续
    ERROR = 40   # 错误需处理
    FATAL = 50   # 致命错误


class StructuredLogger:
    """
    结构化日志记录器
    支持JSON格式的结构化日志，便于后续分析
    """
    
    def __init__(self, name: str, log_dir: Path):
        self.name = name
        self.log_dir = log_dir
        self.log_file = log_dir / f"{name}_structured.json"
        
        # 确保目录存在
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # 系统信息（启动时记录一次）
        self.system_info = self._get_system_info()
        
        # 写入系统信息作为第一条日志
        self._write_log({
            'timestamp': datetime.now().isoformat(),
            'level': 'INFO',
            'event': 'system_info',
            'data': self.system_info
        })
    
    def _get_system_info(self) -> Dict[str, Any]:
        """获取系统信息"""
        try:
            info = {
                'platform': platform.platform(),
                'python_version': platform.python_version(),
                'processor': platform.processor(),
                'architecture': platform.architecture(),
                'system': platform.system()
            }
            
            # 尝试获取更详细信息（如果psutil可用）
            try:
                import psutil
                info.update({
                    'cpu_count': psutil.cpu_count(),
                    'memory_total_gb': round(psutil.virtual_memory().total / (1024**3), 2),
                    'disk_usage': {
                        'total_gb': round(psutil.disk_usage('/').total / (1024**3), 2),
                        'free_gb': round(psutil.disk_usage('/').free / (1024**3), 2),
                        'percent': psutil.disk_usage('/').percent
                    }
                })
            except ImportError:
                info['note'] = 'psutil不可用，系统信息有限'
            
            return info
        except Exception as e:
            return {'error': f'无法获取系统信息: {str(e)}'}
    
    def _write_log(self, log_entry: Dict[str, Any]):
        """写入结构化日志"""
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
        except Exception as e:
            print(f"写入日志失败: {e}")
    
    def log(self, level: Union[str, LogLevel], event: str, data: Dict[str, Any] = None, 
            error: Exception = None):
        """
        记录结构化日志
        
        Args:
            level: 日志级别
            event: 事件名称
            data: 事件数据
            error: 异常对象
        """
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'level': level.value if isinstance(level, LogLevel) else level,
            'event': event,
            'logger': self.name
        }
        
        if data:
            log_entry['data'] = data
        
        if error:
            log_entry['error'] = {
                'type': type(error).__name__,
                'message': str(error),
                'traceback': None  # 可以添加traceback
            }
        
        self._write_log(log_entry)
    
    def log_download(self, tool_name: str, source_name: str, url: str, 
                     size_bytes: Optional[int] = None, speed_mbps: Optional[float] = None,
                     retry_count: int = 0, success: bool = True, error_msg: str = None):
        """记录下载详情"""
        self.log('INFO', 'download', {
            'tool': tool_name,
            'source': source_name,
            'url': url,
            'size_bytes': size_bytes,
            'size_mb': round(size_bytes / (1024*1024), 2) if size_bytes else None,
            'speed_mbps': speed_mbps,
            'retry_count': retry_count,
            'success': success,
            'error': error_msg
        })
    
    def log_installation(self, tool_name: str, phase: str, progress: int = -1,
                        message: str = None, details: Dict[str, Any] = None):
        """记录安装过程"""
        data = {
            'tool': tool_name,
            'phase': phase,
            'progress': progress,
            'message': message
        }
        if details:
            data.update(details)
        
        self.log('INFO', 'installation', data)
    
    def log_network_error(self, url: str, error_type: str, error_msg: str,
                         timeout: Optional[int] = None, retry_count: int = 0):
        """记录网络错误"""
        self.log('ERROR', 'network_error', {
            'url': url,
            'error_type': error_type,
            'error_message': error_msg,
            'timeout_seconds': timeout,
            'retry_count': retry_count
        })
    
    def log_file_operation(self, operation: str, path: str, size_bytes: Optional[int] = None,
                          success: bool = True, error_msg: str = None):
        """记录文件操作"""
        self.log('DEBUG', f'file_{operation}', {
            'path': path,
            'size_bytes': size_bytes,
            'size_mb': round(size_bytes / (1024*1024), 2) if size_bytes else None,
            'success': success,
            'error': error_msg
        })
    
    def log_dependency_check(self, tool_name: str, dependency: str, version: str = None,
                            found: bool = True, required_version: str = None):
        """记录依赖检查"""
        self.log('INFO', 'dependency_check', {
            'tool': tool_name,
            'dependency': dependency,
            'found': found,
            'version': version,
            'required_version': required_version,
            'satisfied': found and (not required_version or version >= required_version)
        })
    
    def log_user_action(self, action: str, target: str = None, params: Dict[str, Any] = None):
        """记录用户操作"""
        data = {'action': action}
        if target:
            data['target'] = target
        if params:
            data['params'] = params
        
        self.log('INFO', 'user_action', data)
    
    def log_performance(self, operation: str, duration_ms: float, 
                       details: Dict[str, Any] = None):
        """记录性能数据"""
        data = {
            'operation': operation,
            'duration_ms': duration_ms,
            'duration_seconds': duration_ms / 1000
        }
        if details:
            data.update(details)
        
        self.log('DEBUG', 'performance', data)


class EnhancedMonitor:
    """
    增强型监控系统
    整合所有日志功能，提供统一接口
    """
    
    def __init__(self, app_version: str = "1.1.10"):
        self.app_version = app_version
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 创建日志目录
        self.logs_dir = Path.cwd() / "logs"
        today = datetime.now().strftime("%Y-%m-%d")
        self.session_dir = self.logs_dir / today / f"session_{self.session_id}"
        self.session_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化各种日志记录器
        self.structured_logger = StructuredLogger('main', self.session_dir)
        self.download_logger = StructuredLogger('download', self.session_dir)
        self.install_logger = StructuredLogger('install', self.session_dir)
        self.network_logger = StructuredLogger('network', self.session_dir)
        
        # 记录会话开始
        self.structured_logger.log('INFO', 'session_start', {
            'version': app_version,
            'session_id': self.session_id,
            'timestamp': datetime.now().isoformat()
        })
    
    def get_logger(self, name: str) -> StructuredLogger:
        """获取指定名称的日志记录器"""
        if name == 'download':
            return self.download_logger
        elif name == 'install':
            return self.install_logger
        elif name == 'network':
            return self.network_logger
        else:
            return self.structured_logger
    
    def log_session_end(self):
        """记录会话结束"""
        self.structured_logger.log('INFO', 'session_end', {
            'session_id': self.session_id,
            'timestamp': datetime.now().isoformat()
        })
    
    def generate_session_report(self) -> Dict[str, Any]:
        """生成会话报告"""
        # 读取所有日志并生成统计报告
        report = {
            'session_id': self.session_id,
            'version': self.app_version,
            'summary': {
                'downloads': 0,
                'installations': 0,
                'errors': 0,
                'user_actions': 0
            }
        }
        
        # 遍历日志文件统计事件
        for log_file in self.session_dir.glob('*_structured.json'):
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        entry = json.loads(line)
                        event = entry.get('event', '')
                        
                        if event == 'download':
                            report['summary']['downloads'] += 1
                        elif event == 'installation':
                            report['summary']['installations'] += 1
                        elif entry.get('level') == 'ERROR':
                            report['summary']['errors'] += 1
                        elif event == 'user_action':
                            report['summary']['user_actions'] += 1
            except:
                pass
        
        return report


# 全局监控实例
_monitor_instance = None


def get_enhanced_monitor() -> EnhancedMonitor:
    """获取全局监控实例"""
    global _monitor_instance
    if _monitor_instance is None:
        _monitor_instance = EnhancedMonitor()
    return _monitor_instance