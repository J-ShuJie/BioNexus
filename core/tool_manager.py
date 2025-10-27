"""
工具管理器 v1.1.10
负责工具的安装、启动、状态管理等核心功能
现已集成插件化架构和真实安装功能
对应JavaScript中的工具相关操作函数
"""
import subprocess
import threading
import time
import logging
from pathlib import Path
from typing import Callable, Optional, Dict, Any, List
from PyQt5.QtCore import QObject, pyqtSignal, QThread, pyqtSlot
from data.models import Tool, ToolStatus, DownloadTask, DownloadStatus
from data.config import ConfigManager
from .tool_registry import ToolRegistry
from utils.tool_localization import get_localized_tool_description


class InstallWorker(QThread):
    """
    安装工作线程 v1.1.10
    在后台执行工具安装，避免界面阻塞
    现已集成真实的工具安装功能
    """
    
    # 进度更新信号
    progress_updated = pyqtSignal(int)          # 进度百分比
    status_updated = pyqtSignal(str)            # 状态文本更新
    installation_completed = pyqtSignal(bool)   # 安装完成(成功/失败)
    error_occurred = pyqtSignal(str)            # 错误信息
    
    def __init__(self, tool_instance, tool_name: str):
        """
        初始化安装工作线程
        
        Args:
            tool_instance: 工具实例（实现了ToolInterface）
            tool_name: 工具名称
        """
        super().__init__()
        self.tool_instance = tool_instance
        self.tool_name = tool_name
        self.is_cancelled = False
    
    def run(self):
        """
        执行真实的安装过程
        调用工具实例的install方法
        """
        try:
            if self.is_cancelled:
                return
            
            # 定义进度回调函数
            def progress_callback(status_text: str, percentage: int):
                if self.is_cancelled:
                    return
                
                self.status_updated.emit(status_text)
                if percentage >= 0:
                    self.progress_updated.emit(percentage)
                else:
                    # 负数表示错误
                    self.error_occurred.emit(status_text)
            
            # 调用工具的真实安装方法
            success = self.tool_instance.install(progress_callback)
            
            if self.is_cancelled:
                return
            
            # 发送完成信号
            self.installation_completed.emit(success)
            
        except Exception as e:
            error_msg = f"安装过程异常: {str(e)}"
            self.error_occurred.emit(error_msg)
            self.installation_completed.emit(False)
    
    def cancel(self):
        """取消安装"""
        self.is_cancelled = True


class ToolManager(QObject):
    """
    工具管理器主类 v1.1.10
    负责工具的生命周期管理：安装、启动、状态更新等
    现已集成插件化架构，支持真实的工具安装
    """
    
    # 信号定义
    tool_installed = pyqtSignal(str)            # 工具安装完成
    tool_launched = pyqtSignal(str)             # 工具启动
    tool_uninstalled = pyqtSignal(str)          # 工具卸载完成
    tool_status_changed = pyqtSignal(str, str)  # 工具状态变化 (工具名, 新状态)
    installation_progress = pyqtSignal(str, int, str)  # 安装进度 (工具名, 进度%, 状态文本)
    error_occurred = pyqtSignal(str, str)       # 错误发生 (工具名, 错误信息)
    usage_time_updated = pyqtSignal(str, int)   # 工具使用时间更新 (工具名, 总使用时间秒数)
    
    def __init__(self, config_manager: ConfigManager):
        super().__init__()
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)

        # 初始化工具注册中心
        self.registry = ToolRegistry()

        self.install_workers: Dict[str, InstallWorker] = {}  # 正在安装的工具
        self.running_processes: Dict[str, subprocess.Popen] = {}  # 正在运行的工具进程

        # 初始化工具使用时间跟踪器
        self.usage_tracker = None
        try:
            from utils.tool_usage_tracker import get_tool_usage_tracker
            self.usage_tracker = get_tool_usage_tracker(config_manager)

            # 🔥 关键修复：使用线程安全的信号连接，而不是回调函数！
            # Qt会自动将信号从后台线程排队到主线程
            self.usage_tracker.usage_updated.connect(self._on_usage_time_updated)
            self.logger.info("✅ [ToolManager-初始化] 工具使用时间跟踪器已初始化")
            self.logger.info("✅ [ToolManager-初始化] 已连接线程安全的usage_updated信号到槽函数")

            # 🔥 保留旧的回调设置以兼容（但信号是主要方式）
            self.usage_tracker.on_usage_updated = self._on_usage_time_updated_callback
            self.logger.info(f"✅ [ToolManager-初始化] 回调函数已设置（兼容模式）")
        except Exception as e:
            self.logger.warning(f"❌ [ToolManager-初始化] 工具使用时间跟踪器初始化失败: {e}")
            import traceback
            self.logger.warning(traceback.format_exc())

    @pyqtSlot(str, int)
    def _on_usage_time_updated(self, tool_name: str, total_runtime: int):
        """
        工具使用时间更新槽函数（线程安全）
        通过Qt信号/槽机制从ToolUsageTracker接收更新，Qt自动处理线程切换

        🔥 使用 @pyqtSlot 装饰器确保跨线程信号正确传递

        Args:
            tool_name: 工具名称
            total_runtime: 总使用时间（秒）
        """
        self.logger.info(f"📡 [ToolManager-槽函数] 在主线程中收到usage_updated信号: {tool_name}, 总计: {total_runtime}秒")
        # 发出信号通知UI更新（现在已经在主线程中了）
        try:
            self.logger.info(f"📡 [ToolManager-信号发射] 准备发射 usage_time_updated 信号...")
            self.usage_time_updated.emit(tool_name, total_runtime)
            self.logger.info(f"✅ [ToolManager-信号发射] 信号发射成功: {tool_name}, {total_runtime}秒")
        except Exception as e:
            self.logger.error(f"❌ [ToolManager-信号发射] 信号发射失败: {e}")
            import traceback
            self.logger.error(traceback.format_exc())

    def _on_usage_time_updated_callback(self, tool_name: str, total_runtime: int):
        """
        工具使用时间更新回调（兼容模式，不应再使用）
        这是旧的回调函数接口，保留以兼容旧代码，但实际上信号机制已经处理了

        Args:
            tool_name: 工具名称
            total_runtime: 总使用时间（秒）
        """
        self.logger.info(f"⚠️ [ToolManager-旧回调] 收到回调调用（兼容模式）: {tool_name}, 但信号已经处理了")
    
    def install_tool(self, tool_name: str) -> bool:
        """
        安装工具 - 使用新的插件化架构
        
        Args:
            tool_name: 要安装的工具名称
            
        Returns:
            bool: 是否成功启动安装过程
        """
        # 检查是否已在安装中
        if tool_name in self.install_workers:
            self.logger.warning(f"工具 {tool_name} 正在安装中")
            return False
        
        # 从注册中心获取工具实例
        tool_instance = self.registry.get_tool(tool_name)
        if not tool_instance:
            error_msg = f"未找到工具: {tool_name}"
            self.error_occurred.emit(tool_name, error_msg)
            self.logger.error(error_msg)
            return False
        
        # 检查工具是否已安装
        if tool_instance.verify_installation():
            error_msg = f"工具 {tool_name} 已安装"
            self.error_occurred.emit(tool_name, error_msg)
            self.logger.warning(error_msg)
            return False
        
        # 创建安装工作线程
        worker = InstallWorker(tool_instance, tool_name)
        
        # 连接信号
        worker.progress_updated.connect(
            lambda progress: self.installation_progress.emit(tool_name, progress, "")
        )
        worker.status_updated.connect(
            lambda status: self.installation_progress.emit(tool_name, -1, status)
        )
        worker.installation_completed.connect(
            lambda success: self._on_installation_completed(tool_name, success)
        )
        worker.error_occurred.connect(
            lambda error: self.error_occurred.emit(tool_name, error)
        )
        
        # 保存工作线程引用并启动
        self.install_workers[tool_name] = worker
        worker.start()
        
        self.logger.info(f"开始安装工具: {tool_name}")
        return True
    
    def _on_installation_completed(self, tool_name: str, success: bool):
        """
        安装完成回调 - 更新状态
        """
        # 移除工作线程
        if tool_name in self.install_workers:
            del self.install_workers[tool_name]
        
        if success:
            self.logger.info(f"工具 {tool_name} 安装成功")
            # 发出安装完成信号
            print(f"[ToolManager] *** 发送 tool_installed 信号 ***: {tool_name}")
            self.tool_installed.emit(tool_name)
            print(f"[ToolManager] *** 发送 tool_status_changed 信号 ***: {tool_name} -> installed")
            self.tool_status_changed.emit(tool_name, "installed")
        else:
            self.logger.error(f"工具 {tool_name} 安装失败")
    
    def uninstall_tool(self, tool_name: str) -> bool:
        """
        卸载工具 - 新增功能
        
        Args:
            tool_name: 要卸载的工具名称
            
        Returns:
            bool: 卸载是否成功
        """
        try:
            # 从注册中心获取工具实例
            tool_instance = self.registry.get_tool(tool_name)
            if not tool_instance:
                error_msg = f"未找到工具: {tool_name}"
                self.error_occurred.emit(tool_name, error_msg)
                return False
            
            # 检查工具是否已安装
            if not tool_instance.verify_installation():
                error_msg = f"工具 {tool_name} 未安装"
                self.error_occurred.emit(tool_name, error_msg)
                return False
            
            # 执行卸载（添加进度反馈）
            self.installation_progress.emit(tool_name, 25, "正在停止工具进程...")
            
            self.installation_progress.emit(tool_name, 50, "正在删除工具文件...")
            success = tool_instance.uninstall()
            
            if success:
                self.installation_progress.emit(tool_name, 75, "正在清理配置文件...")
                self.installation_progress.emit(tool_name, 100, "卸载完成")
                
                self.logger.info(f"工具 {tool_name} 卸载成功")
                print(f"[ToolManager] *** 发送 tool_uninstalled 信号 ***: {tool_name}")
                self.tool_uninstalled.emit(tool_name)
                print(f"[ToolManager] *** 发送 tool_status_changed 信号 ***: {tool_name} -> available")
                self.tool_status_changed.emit(tool_name, "available")
                return True
            else:
                error_msg = f"工具 {tool_name} 卸载失败"
                self.error_occurred.emit(tool_name, error_msg)
                return False
                
        except Exception as e:
            error_msg = f"卸载工具 {tool_name} 时发生异常: {str(e)}"
            self.logger.error(error_msg)
            self.error_occurred.emit(tool_name, error_msg)
            return False
    
    def launch_tool(self, tool_name: str) -> bool:
        """
        启动工具 - 使用新的插件化架构
        
        Args:
            tool_name: 要启动的工具名称
            
        Returns:
            bool: 是否成功启动
        """
        try:
            # 从注册中心获取工具实例
            tool_instance = self.registry.get_tool(tool_name)
            if not tool_instance:
                error_msg = f"未找到工具: {tool_name}"
                self.error_occurred.emit(tool_name, error_msg)
                return False
            
            # 检查工具是否已安装
            if not tool_instance.verify_installation():
                error_msg = f"工具 {tool_name} 未安装"
                self.error_occurred.emit(tool_name, error_msg)
                return False
            
            # 启动工具
            success = tool_instance.launch()

            if success:
                self.logger.info(f"工具 {tool_name} 启动成功")
                self.tool_launched.emit(tool_name)

                # 开始跟踪工具使用时间
                if self.usage_tracker:
                    try:
                        # 尝试获取工具进程PID（如果可能）
                        pid = self._get_tool_process_pid(tool_name)
                        self.usage_tracker.start_tracking(tool_name, pid)
                        self.logger.info(f"开始跟踪工具使用时间: {tool_name}, PID: {pid or '未知'}")
                    except Exception as e:
                        self.logger.warning(f"启动工具使用跟踪失败: {e}")

                return True
            else:
                error_msg = f"工具 {tool_name} 启动失败"
                self.error_occurred.emit(tool_name, error_msg)
                return False
                
        except Exception as e:
            error_msg = f"启动工具 {tool_name} 时发生异常: {str(e)}"
            self.logger.error(error_msg)
            self.error_occurred.emit(tool_name, error_msg)
            return False
    
    def _with_localized_description(self, tool_data: Dict[str, Any]) -> Dict[str, Any]:
        """返回带本地化简介的工具数据副本，不修改原始数据文件。

        - 优先使用内置本地化（YAML/内嵌 i18n 字段）
        - 将结果写入 `display_description` 字段，同时覆盖 `description` 供旧代码使用
        - 原始用户数据不被修改
        """
        td = dict(tool_data or {})
        try:
            desc = get_localized_tool_description(td)
        except Exception:
            desc = ''
        td['display_description'] = desc
        td['description'] = desc
        return td

    def get_all_tools_data(self) -> List[Dict[str, Any]]:
        """
        获取所有工具数据，供UI层使用
        替代原有的从config_manager获取数据的方式
        
        Returns:
            工具数据列表
        """
        return [self._with_localized_description(t) for t in self.registry.get_all_tools()]
    
    def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """
        获取指定工具的详细信息
        
        Args:
            tool_name: 工具名称
            
        Returns:
            工具信息字典，如果不存在返回None
        """
        tool_instance = self.registry.get_tool(tool_name)
        if tool_instance:
            return self._with_localized_description(tool_instance.to_dict())
        return None
    
    def check_tool_dependencies(self, tool_name: str) -> Dict[str, bool]:
        """
        检查工具依赖项
        
        Args:
            tool_name: 工具名称
            
        Returns:
            依赖项检查结果
        """
        tool_instance = self.registry.get_tool(tool_name)
        if tool_instance:
            return tool_instance.check_dependencies()
        return {}
    
    def cancel_installation(self, tool_name: str) -> bool:
        """
        取消正在进行的安装
        
        Args:
            tool_name: 工具名称
            
        Returns:
            是否成功取消
        """
        if tool_name in self.install_workers:
            worker = self.install_workers[tool_name]
            worker.cancel()
            self.logger.info(f"已取消 {tool_name} 的安装")
            return True
        return False
    
    def is_tool_installed(self, tool_name: str) -> bool:
        """检查工具是否已安装"""
        tool_instance = self.registry.get_tool(tool_name)
        if tool_instance:
            return tool_instance.verify_installation()
        return False
    
    def is_tool_installing(self, tool_name: str) -> bool:
        """检查工具是否正在安装"""
        return tool_name in self.install_workers
    
    def _get_tool_process_pid(self, tool_name: str) -> Optional[int]:
        """
        尝试获取工具进程的PID

        Args:
            tool_name: 工具名称

        Returns:
            进程PID，如果找不到则返回None
        """
        try:
            import psutil
            import time

            # 等待一小段时间让进程完全启动
            time.sleep(0.5)

            # 常见工具的进程名映射
            process_name_map = {
                'Cytoscape': ['cytoscape.exe', 'Cytoscape.exe', 'java.exe', 'javaw.exe'],
                'IGV': ['igv.exe', 'IGV.exe', 'java.exe', 'javaw.exe'],
                'FastQC': ['fastqc.exe', 'FastQC.exe', 'java.exe', 'javaw.exe'],
                'BLAST': ['blastn.exe', 'blastp.exe', 'blastx.exe'],
                'BWA': ['bwa.exe'],
                'SAMtools': ['samtools.exe'],
            }

            possible_names = process_name_map.get(tool_name, [f"{tool_name.lower()}.exe"])

            # 查找最近启动的匹配进程
            candidates = []
            current_time = time.time()

            for proc in psutil.process_iter(['pid', 'name', 'create_time']):
                try:
                    proc_name = proc.info['name']
                    if proc_name and any(name.lower() in proc_name.lower() for name in possible_names):
                        # 只考虑最近10秒内启动的进程
                        if current_time - proc.info['create_time'] < 10:
                            candidates.append((proc.info['pid'], proc.info['create_time']))
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            # 返回最新启动的进程
            if candidates:
                candidates.sort(key=lambda x: x[1], reverse=True)
                pid = candidates[0][0]
                self.logger.info(f"找到工具进程: {tool_name}, PID: {pid}")
                return pid

        except Exception as e:
            self.logger.warning(f"获取工具进程PID失败: {tool_name}, 错误: {e}")

        return None

    def cleanup(self):
        """清理资源，应用退出时调用"""
        # 停止所有工具使用跟踪
        if self.usage_tracker:
            try:
                self.usage_tracker.stop_all_tracking()
                self.logger.info("已停止所有工具使用跟踪")
            except Exception as e:
                self.logger.error(f"停止工具使用跟踪失败: {e}")

        # 取消所有正在进行的安装
        for tool_name in list(self.install_workers.keys()):
            self.cancel_installation(tool_name)

        self.logger.info("ToolManager cleanup completed")
