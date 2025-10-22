"""
工具更新控制器 - 管理UI与更新服务的交互
注意：此模块仅处理第三方工具更新，不涉及BioNexus本体更新

负责：
1. 协调更新服务和UI界面
2. 处理更新通知显示
3. 管理更新对话框和用户交互
4. 控制自动/手动更新流程
"""

from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QMessageBox, QDialog, QApplication
from typing import Dict, List, Any, Optional
from datetime import datetime

from utils.unified_logger import get_logger
from .tool_update_service import ToolUpdateService
from .tool_update_notifier import ToolUpdateNotifier


class ToolUpdateController(QObject):
    """
    工具更新控制器
    
    协调更新服务、UI界面和用户交互
    仅管理第三方生物信息工具更新，不包括BioNexus软件本体
    """
    
    # 信号定义
    update_status_changed = pyqtSignal(str, str)    # 更新状态变化（工具名，状态）
    history_updated = pyqtSignal(list)              # 更新历史变化
    settings_changed = pyqtSignal(dict)             # 设置变更
    
    def __init__(self, parent=None, config_manager=None, tool_manager=None):
        super().__init__(parent)
        
        self.logger = get_logger()
        self.parent_window = parent
        self.config_manager = config_manager
        self.tool_manager = tool_manager
        
        # 初始化更新服务
        self.update_service = ToolUpdateService(config_manager, tool_manager)
        self.update_notifier = ToolUpdateNotifier(parent)
        
        # 连接信号
        self._setup_connections()
        
        # 当前更新状态
        self.current_updates = {}
        self.is_updating = False
        
        self.logger.log_runtime("工具更新控制器初始化完成")
    
    def _setup_connections(self):
        """设置信号连接"""
        # 更新服务信号
        self.update_service.update_found.connect(self._handle_updates_found)
        self.update_service.update_completed.connect(self._handle_update_completed)
        self.update_service.update_progress.connect(self._handle_update_progress)
        self.update_service.check_completed.connect(self._handle_check_completed)
        
        # 通知器信号
        self.update_notifier.update_accepted.connect(self._handle_update_accepted)
        self.update_notifier.update_skipped.connect(self._handle_update_skipped)
        self.update_notifier.update_silenced.connect(self._handle_update_silenced)
    
    def check_for_updates(self, is_manual: bool = True):
        """
        检查工具更新
        
        Args:
            is_manual: 是否为手动触发（影响通知方式）
        """
        self.logger.log_runtime(f"开始检查工具更新 (手动: {is_manual})")
        self.update_service.check_tool_updates(is_manual=is_manual)
    
    def check_for_updates_from_settings(self):
        """
        从设置面板触发的手动检查（无论结果如何都要弹窗）
        """
        self.logger.log_runtime("开始检查工具更新 (来自设置面板)")
        # 使用特殊标记来区分这种手动检查
        self.update_service.check_tool_updates(is_manual=True, is_manual_from_settings=True)
    
    def _handle_updates_found(self, update_data: Dict[str, Any]):
        """处理发现更新"""
        updates = update_data.get('updates', [])
        is_manual = update_data.get('is_manual', False)
        is_scheduled = update_data.get('is_scheduled', False)
        
        if not updates:
            return
        
        self.current_updates = {update['tool_name']: update for update in updates}
        
        # 记录更新发现
        for update in updates:
            self.update_service.add_to_history({
                'type': 'update_found',
                'tool_name': update['tool_name'],
                'from_version': update['current_version'],
                'to_version': update['latest_version'],
                'priority': update.get('priority', 'optional')
            })
        
        # 根据更新模式决定处理方式
        update_mode = self.update_service.update_settings.get('update_mode', 'auto')
        
        if update_mode == 'auto':
            self._handle_auto_updates(updates, is_scheduled)
        else:
            self._handle_manual_updates(updates, is_manual)
        
        # 发送历史更新信号
        self.history_updated.emit(self.update_service.get_update_history())
    
    def _handle_auto_updates(self, updates: List[Dict[str, Any]], is_scheduled: bool):
        """处理自动更新模式"""
        self.logger.log_runtime(f"自动更新模式：发现{len(updates)}个更新")
        
        if QApplication.instance():
            # 检查应用是否正在运行
            if self._is_app_active():
                # 应用正在使用，标记待更新，等待应用关闭
                self._schedule_updates_on_close(updates)
            else:
                # 应用空闲，立即执行更新
                self._execute_auto_updates(updates)
    
    def _handle_manual_updates(self, updates: List[Dict[str, Any]], is_manual: bool):
        """处理手动更新模式"""
        show_notification = self.update_service.update_settings.get('show_notification', True)
        
        if is_manual or show_notification:
            # 显示更新通知对话框
            self.update_notifier.show_updates_dialog(updates, is_manual)
        else:
            # 静默记录，不显示通知
            self.logger.log_runtime(f"手动模式静默：发现{len(updates)}个更新，但通知已禁用")
    
    def _is_app_active(self) -> bool:
        """检查应用是否活跃（用户正在使用）"""
        # 简单的活跃检查：如果主窗口可见且有焦点
        if self.parent_window:
            return self.parent_window.isVisible() and self.parent_window.isActiveWindow()
        return True
    
    def _schedule_updates_on_close(self, updates: List[Dict[str, Any]]):
        """安排应用关闭时更新"""
        self.logger.log_runtime(f"安排{len(updates)}个工具在应用关闭时更新")
        
        # 可以在状态区域显示小提示（使用现代化下载卡片）
        if hasattr(self.parent_window, 'modern_download_card') and self.parent_window.modern_download_card:
            title = self.parent_window.tr("工具更新")
            msg = self.parent_window.tr("发现{0}个工具更新，将在应用关闭时自动更新").format(len(updates))
            self.parent_window.modern_download_card.add_or_update_download(title, 0, msg)
    
    def _execute_auto_updates(self, updates: List[Dict[str, Any]]):
        """执行自动更新"""
        self.logger.log_runtime(f"执行自动更新：{len(updates)}个工具")
        
        for update in updates:
            tool_name = update['tool_name']
            self._start_tool_update(tool_name, update)
    
    def _start_tool_update(self, tool_name: str, update_info: Dict[str, Any]):
        """开始工具更新"""
        try:
            self.is_updating = True
            
            # 更新状态
            self.update_status_changed.emit(tool_name, "更新中")
            
            # 获取工具实例
            tool_instance = self.update_service.tool_registry.get_tool(tool_name)
            if not tool_instance:
                raise Exception(f"无法找到工具实例: {tool_name}")
            
            # 如果工具有自定义更新方法，使用它
            if hasattr(tool_instance, 'update'):
                # 在后台线程执行更新
                self.update_service.thread_pool.submit(
                    self._execute_tool_update, 
                    tool_instance, 
                    update_info
                )
            else:
                # 使用通用更新方法（重新安装）
                self._reinstall_tool(tool_name, update_info)
                
        except Exception as e:
            self.logger.log_error(f"启动工具 {tool_name} 更新失败: {e}")
            self.update_status_changed.emit(tool_name, "更新失败")
            self._handle_update_completed(tool_name, False)
    
    def _execute_tool_update(self, tool_instance, update_info: Dict[str, Any]):
        """执行工具更新（在后台线程中）"""
        tool_name = update_info['tool_name']
        
        try:
            # 定义进度回调
            def progress_callback(message: str, progress: int):
                self.update_service.update_progress.emit(tool_name, progress, message)
            
            # 执行更新
            result = tool_instance.update(
                target_version=update_info['latest_version'],
                progress_callback=progress_callback
            )
            
            # 发送完成信号
            self.update_service.update_completed.emit(tool_name, result)
            
        except Exception as e:
            self.logger.log_error(f"执行工具 {tool_name} 更新时出错: {e}")
            self.update_service.update_completed.emit(tool_name, False)
    
    def _reinstall_tool(self, tool_name: str, update_info: Dict[str, Any]):
        """重新安装工具（通用更新方法）"""
        try:
            if self.tool_manager:
                # 使用工具管理器重新安装
                def progress_callback(progress: int, message: str):
                    self.update_service.update_progress.emit(tool_name, progress, message)
                
                # 异步重新安装
                self.update_service.thread_pool.submit(
                    self._async_reinstall,
                    tool_name,
                    progress_callback
                )
        except Exception as e:
            self.logger.log_error(f"重新安装工具 {tool_name} 失败: {e}")
            self.update_service.update_completed.emit(tool_name, False)
    
    def _async_reinstall(self, tool_name: str, progress_callback):
        """异步重新安装工具"""
        try:
            result = self.tool_manager.install_tool(tool_name, progress_callback)
            self.update_service.update_completed.emit(tool_name, result)
        except Exception as e:
            self.logger.log_error(f"异步重新安装工具 {tool_name} 失败: {e}")
            self.update_service.update_completed.emit(tool_name, False)
    
    def _handle_update_completed(self, tool_name: str, success: bool):
        """处理更新完成"""
        status = "更新成功" if success else "更新失败"
        self.update_status_changed.emit(tool_name, status)
        
        # 添加到历史记录
        if tool_name in self.current_updates:
            update_info = self.current_updates[tool_name]
            self.update_service.add_to_history({
                'type': 'update_completed',
                'tool_name': tool_name,
                'from_version': update_info['current_version'],
                'to_version': update_info['latest_version'],
                'success': success,
                'error': None if success else "更新过程中发生错误"
            })
        
        # 从当前更新中移除
        if tool_name in self.current_updates:
            del self.current_updates[tool_name]
        
        # 如果所有更新都完成，重置状态
        if not self.current_updates:
            self.is_updating = False
        
        # 发送历史更新信号
        self.history_updated.emit(self.update_service.get_update_history())
        
        self.logger.log_runtime(f"工具 {tool_name} 更新完成: {status}")
    
    def _handle_update_progress(self, tool_name: str, progress: int, message: str):
        """处理更新进度"""
        # 可以转发给下载状态面板
        if hasattr(self.parent_window, 'download_status_panel'):
            self.parent_window.download_status_panel.add_or_update_download(
                f"{tool_name} 更新",
                progress,
                message
            )
    
    def _handle_check_completed(self, result: Dict[str, Any]):
        """处理检查完成"""
        if 'error' in result:
            self.logger.log_error(f"工具更新检查失败: {result['error']}")
            # 如果是来自设置面板的手动检查，即使出错也要弹窗告知
            if result.get('is_manual_from_settings', False):
                self._show_manual_check_error(result['error'])
            return
        
        updates = result.get('available_updates', [])
        is_manual = result.get('is_manual', False)
        is_manual_from_settings = result.get('is_manual_from_settings', False)
        
        # 如果是设置面板的手动检查，无论结果如何都要弹窗
        if is_manual_from_settings:
            if updates:
                # 有更新：显示具体更新内容
                self.update_notifier.show_updates_dialog(updates, is_manual=True)
            else:
                # 没有更新：显示"都是最新版本"
                self._show_no_updates_message()
        
        self.logger.log_runtime(f"工具更新检查完成: 发现{len(updates)}个更新")
    
    def _show_no_updates_message(self):
        """显示没有更新的消息"""
        if self.parent_window:
            QMessageBox.information(
                self.parent_window,
                "检查工具更新",
                "所有已安装的工具都是最新版本！"
            )
    
    def _show_manual_check_error(self, error_message: str):
        """显示手动检查错误消息"""
        if self.parent_window:
            QMessageBox.critical(
                self.parent_window,
                "检查更新失败",
                f"检查工具更新时发生错误:\n{error_message}"
            )
    
    def _handle_update_accepted(self, tool_names: List[str]):
        """处理用户接受更新"""
        for tool_name in tool_names:
            if tool_name in self.current_updates:
                self._start_tool_update(tool_name, self.current_updates[tool_name])
    
    def _handle_update_skipped(self, tool_name: str, version: str, permanent: bool):
        """处理用户跳过更新"""
        self.update_service.skip_update(tool_name, version, permanent)
        
        # 从当前更新中移除
        if tool_name in self.current_updates:
            del self.current_updates[tool_name]
    
    def _handle_update_silenced(self, tool_name: str, version: str):
        """处理用户选择静默"""
        self.update_service.skip_update(tool_name, version, permanent=False)
        
        # 从当前更新中移除
        if tool_name in self.current_updates:
            del self.current_updates[tool_name]
    
    def get_update_settings(self) -> Dict[str, Any]:
        """获取当前更新设置"""
        return self.update_service.get_update_settings()
    
    def update_settings(self, new_settings: Dict[str, Any]):
        """更新设置"""
        self.update_service.update_settings_changed(new_settings)
        self.settings_changed.emit(new_settings)
    
    def get_update_history(self) -> List[Dict[str, Any]]:
        """获取更新历史"""
        return self.update_service.get_update_history()
    
    def cleanup(self):
        """清理资源"""
        if self.update_service:
            self.update_service.cleanup()
        self.logger.log_runtime("工具更新控制器已清理")
