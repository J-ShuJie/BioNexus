"""
工具更新服务模块 - 仅管理第三方生物信息工具更新
注意：此模块不涉及BioNexus本体更新，仅处理：
- FastQC、BLAST、HISAT2等工具的版本检查
- 第三方工具的下载和安装更新
- 与BioNexus软件本身更新无关
"""

import threading
import time
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from pathlib import Path
from PyQt5.QtCore import QObject, pyqtSignal, QTimer
from concurrent.futures import ThreadPoolExecutor

from utils.unified_logger import get_logger
from core.tool_registry import ToolRegistry


class ToolUpdateService(QObject):
    """
    第三方工具更新服务
    
    功能：
    1. 定时检查第三方工具更新（FastQC、BLAST等）
    2. 支持自动/手动更新模式
    3. 后台运行，不阻塞UI
    4. 提供更新通知和历史记录
    
    注意：不包括BioNexus软件本体更新
    """
    
    # 信号定义
    update_found = pyqtSignal(dict)          # 发现工具更新
    update_completed = pyqtSignal(str, bool)  # 更新完成（工具名，成功状态）
    update_progress = pyqtSignal(str, int, str)  # 更新进度（工具名，进度，状态文本）
    check_completed = pyqtSignal(dict)       # 检查完成
    
    def __init__(self, config_manager=None, tool_manager=None):
        super().__init__()
        
        self.logger = get_logger()
        self.config_manager = config_manager
        self.tool_manager = tool_manager
        
        # 工具注册表
        self.tool_registry = ToolRegistry()
        
        # 更新设置（从配置管理器读取）
        self.update_settings = self._load_update_settings()
        
        # 定时器用于定期检查
        self.check_timer = QTimer()
        self.check_timer.timeout.connect(self._scheduled_check)
        
        # 线程池用于后台操作
        self.thread_pool = ThreadPoolExecutor(max_workers=3, thread_name_prefix="ToolUpdate")
        
        # 运行状态
        self.is_checking = False
        self.pending_updates = {}  # 待处理的更新
        self.update_history = []   # 更新历史
        
        # 启动定时检查
        self._setup_scheduled_checks()
        
        self.logger.log_runtime("工具更新服务初始化完成")
    
    def _load_update_settings(self) -> Dict[str, Any]:
        """加载工具更新设置"""
        default_settings = {
            'update_mode': 'auto',           # auto/manual
            'check_frequency': 1,            # 检查频率（天）
            'show_notification': True,       # 显示通知（仅manual模式）
            'last_check': None,              # 上次检查时间
            'skipped_versions': {},          # 跳过的版本 {tool_name: version}
            'silent_versions': {},           # 静默的版本 {tool_name: version}
            'auto_update_time': '02:00'      # 自动更新时间（小时:分钟）
        }
        
        if self.config_manager:
            # 从配置管理器读取工具更新设置
            saved_settings = getattr(self.config_manager.settings, 'tool_update', {})
            default_settings.update(saved_settings)
        
        return default_settings
    
    def _setup_scheduled_checks(self):
        """设置定时检查"""
        frequency_hours = self.update_settings['check_frequency'] * 24
        self.check_timer.start(frequency_hours * 60 * 60 * 1000)  # 转换为毫秒
        
        self.logger.log_runtime(f"工具更新定时检查已设置：每{self.update_settings['check_frequency']}天")
    
    def _scheduled_check(self):
        """定时检查工具更新"""
        if not self.is_checking:
            self.logger.log_runtime("执行定时工具更新检查")
            self.check_tool_updates(is_scheduled=True)
    
    def check_tool_updates(self, is_manual: bool = False, is_scheduled: bool = False, is_manual_from_settings: bool = False) -> None:
        """
        检查所有工具更新（异步）
        
        Args:
            is_manual: 是否为手动触发
            is_scheduled: 是否为定时触发
            is_manual_from_settings: 是否为设置面板的手动检查（需要强制弹窗）
        """
        if self.is_checking:
            self.logger.log_runtime("工具更新检查已在进行中，跳过")
            return
        
        # 提交到线程池异步执行
        self.thread_pool.submit(self._check_tools_async, is_manual, is_scheduled, is_manual_from_settings)
    
    def _check_tools_async(self, is_manual: bool, is_scheduled: bool, is_manual_from_settings: bool = False):
        """异步检查工具更新"""
        try:
            self.is_checking = True
            check_start_time = datetime.now()
            
            # 获取所有已安装的工具
            installed_tools = self.tool_registry.get_installed_tools()
            
            if not installed_tools:
                self.logger.log_runtime("没有已安装的工具需要检查更新")
                self.check_completed.emit({
                    'available_updates': [], 
                    'total_checked': 0,
                    'is_manual_from_settings': is_manual_from_settings
                })
                return
            
            self.logger.log_runtime(f"开始检查{len(installed_tools)}个已安装工具的更新")
            
            available_updates = []
            
            for tool_name in installed_tools:
                try:
                    # 获取工具实例
                    tool_instance = self.tool_registry.get_tool(tool_name)
                    if not tool_instance:
                        continue
                    
                    # 检查单个工具更新
                    update_info = self._check_single_tool_update(tool_name, tool_instance)
                    
                    if update_info:
                        # 检查是否应该跳过此更新
                        if not self._should_skip_update(tool_name, update_info['latest_version']):
                            available_updates.append(update_info)
                    
                    # 避免频繁请求
                    time.sleep(0.5)
                    
                except Exception as e:
                    self.logger.log_error(f"检查工具 {tool_name} 更新失败: {e}")
            
            # 更新最后检查时间
            self.update_settings['last_check'] = datetime.now().isoformat()
            self._save_update_settings()
            
            # 发送检查完成信号
            check_result = {
                'available_updates': available_updates,
                'total_checked': len(installed_tools),
                'check_time': check_start_time.isoformat(),
                'is_manual': is_manual,
                'is_scheduled': is_scheduled,
                'is_manual_from_settings': is_manual_from_settings
            }
            
            self.check_completed.emit(check_result)
            
            # 如果发现更新，发送更新发现信号
            if available_updates:
                self.update_found.emit({
                    'updates': available_updates,
                    'is_manual': is_manual,
                    'is_scheduled': is_scheduled
                })
                
                self.logger.log_runtime(f"发现{len(available_updates)}个工具更新")
            else:
                self.logger.log_runtime("所有工具都是最新版本")
        
        except Exception as e:
            self.logger.log_error(f"工具更新检查异常: {e}")
            self.check_completed.emit({
                'error': str(e), 
                'is_manual_from_settings': is_manual_from_settings
            })
        
        finally:
            self.is_checking = False
    
    def _check_single_tool_update(self, tool_name: str, tool_instance) -> Optional[Dict[str, Any]]:
        """
        检查单个工具的更新
        
        Returns:
            更新信息字典，如果没有更新返回None
        """
        try:
            # 获取当前版本信息
            current_metadata = tool_instance.get_metadata()
            current_version = current_metadata.get('version', 'unknown')
            
            # 获取最新版本信息（这里调用工具的更新检查方法）
            if hasattr(tool_instance, 'check_for_updates'):
                latest_info = tool_instance.check_for_updates()
            else:
                # 如果工具没有实现更新检查，尝试重新获取元数据
                latest_info = tool_instance.get_metadata()
            
            latest_version = latest_info.get('version', current_version)
            
            # 比较版本
            if self._is_newer_version(latest_version, current_version):
                return {
                    'tool_name': tool_name,
                    'current_version': current_version,
                    'latest_version': latest_version,
                    'changelog': latest_info.get('release_notes', ''),
                    'download_url': latest_info.get('download_url', ''),
                    'size': latest_info.get('size', '未知'),
                    'priority': self._determine_update_priority(current_version, latest_version),
                    'check_time': datetime.now().isoformat()
                }
            
            return None
            
        except Exception as e:
            self.logger.log_error(f"检查工具 {tool_name} 更新时出错: {e}")
            return None
    
    def _is_newer_version(self, latest: str, current: str) -> bool:
        """比较版本号"""
        try:
            # 简单的版本比较（可以改进为更复杂的语义版本比较）
            def parse_version(v):
                # 移除非数字字符，分割版本号
                import re
                clean_v = re.sub(r'[^0-9.]', '', str(v))
                return tuple(map(int, clean_v.split('.')))
            
            return parse_version(latest) > parse_version(current)
        
        except:
            # 如果版本解析失败，使用字符串比较
            return str(latest) != str(current)
    
    def _determine_update_priority(self, current: str, latest: str) -> str:
        """确定更新优先级"""
        try:
            def parse_version(v):
                import re
                clean_v = re.sub(r'[^0-9.]', '', str(v))
                parts = clean_v.split('.')
                return [int(p) if p.isdigit() else 0 for p in parts[:3]]  # 主.次.修复
            
            current_parts = parse_version(current)
            latest_parts = parse_version(latest)
            
            # 主版本更新
            if len(current_parts) >= 1 and len(latest_parts) >= 1:
                if latest_parts[0] > current_parts[0]:
                    return 'recommended'
            
            # 次版本更新
            if len(current_parts) >= 2 and len(latest_parts) >= 2:
                if latest_parts[1] > current_parts[1]:
                    return 'recommended'
            
            # 修复版本更新
            return 'optional'
            
        except:
            return 'optional'
    
    def _should_skip_update(self, tool_name: str, version: str) -> bool:
        """检查是否应该跳过此更新"""
        # 检查永久跳过的版本
        skipped = self.update_settings.get('skipped_versions', {})
        if tool_name in skipped and skipped[tool_name] == version:
            return True
        
        # 检查临时静默的版本
        silent = self.update_settings.get('silent_versions', {})
        if tool_name in silent and silent[tool_name] == version:
            return True
        
        return False
    
    def skip_update(self, tool_name: str, version: str, permanent: bool = False):
        """跳过更新"""
        if permanent:
            self.update_settings.setdefault('skipped_versions', {})[tool_name] = version
        else:
            self.update_settings.setdefault('silent_versions', {})[tool_name] = version
        
        self._save_update_settings()
        self.logger.log_runtime(f"已跳过工具 {tool_name} v{version} 的更新")
    
    def _save_update_settings(self):
        """保存更新设置"""
        if self.config_manager:
            # 保存到配置管理器
            if not hasattr(self.config_manager.settings, 'tool_update'):
                setattr(self.config_manager.settings, 'tool_update', {})
            
            setattr(self.config_manager.settings, 'tool_update', self.update_settings)
            self.config_manager.save_settings()
    
    def get_update_settings(self) -> Dict[str, Any]:
        """获取当前更新设置"""
        return self.update_settings.copy()
    
    def update_settings_changed(self, new_settings: Dict[str, Any]):
        """更新设置变更回调"""
        old_frequency = self.update_settings.get('check_frequency', 1)
        self.update_settings.update(new_settings)
        self._save_update_settings()
        
        # 如果检查频率改变，重新设置定时器
        new_frequency = self.update_settings.get('check_frequency', 1)
        if old_frequency != new_frequency:
            self.check_timer.stop()
            self._setup_scheduled_checks()
        
        self.logger.log_runtime("工具更新设置已更新")
    
    def get_update_history(self) -> List[Dict[str, Any]]:
        """获取更新历史"""
        return self.update_history.copy()
    
    def add_to_history(self, record: Dict[str, Any]):
        """添加更新记录到历史"""
        record['timestamp'] = datetime.now().isoformat()
        self.update_history.insert(0, record)  # 最新的在前面
        
        # 限制历史记录数量
        if len(self.update_history) > 100:
            self.update_history = self.update_history[:100]
    
    def cleanup(self):
        """清理资源"""
        self.check_timer.stop()
        self.thread_pool.shutdown(wait=False)
        self.logger.log_runtime("工具更新服务已清理")