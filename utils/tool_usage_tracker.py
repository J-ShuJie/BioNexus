#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工具使用时间跟踪器

功能：
- 记录工具启动时间
- 监控工具进程状态
- 计算并更新总使用时长
- 持久化到配置文件
"""
import os
import sys
import time
import psutil
import logging
import threading
from datetime import datetime
from typing import Dict, Optional, Callable
from pathlib import Path
from PyQt5.QtCore import QObject, pyqtSignal, QMetaObject, Qt, Q_ARG, pyqtSlot


class ToolUsageSession:
    """单次工具使用会话"""

    def __init__(self, tool_name: str, pid: Optional[int] = None):
        self.tool_name = tool_name
        self.pid = pid
        self.start_time = datetime.now()
        self.end_time: Optional[datetime] = None
        self.duration_seconds = 0
        self.is_active = True

    def mark_ended(self):
        """标记会话结束"""
        if self.is_active:
            self.end_time = datetime.now()
            self.duration_seconds = int((self.end_time - self.start_time).total_seconds())
            self.is_active = False

    def get_current_duration(self) -> int:
        """获取当前运行时长（秒）"""
        if self.is_active:
            return int((datetime.now() - self.start_time).total_seconds())
        return self.duration_seconds


class ToolUsageTracker(QObject):
    """
    工具使用时间跟踪器

    负责：
    1. 记录工具启动
    2. 监控工具进程
    3. 计算使用时长
    4. 更新配置文件

    🔥 继承QObject以支持线程安全的信号发射
    """

    # 🔥 定义线程安全的信号：当工具使用时间更新时发出
    # 参数：(tool_name: str, total_runtime: int)
    usage_updated = pyqtSignal(str, int)

    def __init__(self, config_manager, check_interval: int = 1):
        """
        初始化跟踪器

        Args:
            config_manager: 配置管理器实例
            check_interval: 进程检查间隔（秒），默认5秒
        """
        super().__init__()  # 🔥 初始化QObject
        self.config_manager = config_manager
        self.check_interval = check_interval
        self.logger = logging.getLogger(__name__)

        # 活动会话: {tool_name: ToolUsageSession}
        self.active_sessions: Dict[str, ToolUsageSession] = {}

        # 进程监控线程
        self.monitor_thread: Optional[threading.Thread] = None
        self.is_monitoring = False
        self._lock = threading.Lock()

        # 🔥 保留回调函数以兼容旧代码（但优先使用信号）
        self.on_usage_updated: Optional[Callable[[str, int], None]] = None

    @pyqtSlot(str, int)
    def _emit_usage_updated(self, tool_name: str, total_runtime: int):
        """
        在主线程中发射信号的槽函数

        通过QMetaObject.invokeMethod调用，确保在主线程的事件循环中执行

        Args:
            tool_name: 工具名称
            total_runtime: 总使用时间（秒）
        """
        self.logger.info(f"🎯 [Tracker-主线程发射] 在主线程中发射usage_updated信号: {tool_name}, {total_runtime}秒")
        self.usage_updated.emit(tool_name, total_runtime)

    def start_tracking(self, tool_name: str, pid: Optional[int] = None):
        """
        开始跟踪工具使用

        Args:
            tool_name: 工具名称
            pid: 工具进程ID（可选，用于更精确的监控）
        """
        with self._lock:
            # 如果该工具已有活动会话，先结束旧会话
            if tool_name in self.active_sessions:
                self.logger.warning(f"工具 {tool_name} 已有活动会话，结束旧会话")
                self._end_session(tool_name)

            # 创建新会话
            session = ToolUsageSession(tool_name, pid)
            self.active_sessions[tool_name] = session

            self.logger.info(f"开始跟踪工具: {tool_name}, PID: {pid or '未知'}")

            # 启动监控线程（如果还未启动）
            if not self.is_monitoring:
                self._start_monitor_thread()

        # 如果拿到了有效的 PID，则并行启动“等待线程”，实现退出即刻刷新
        if pid is not None:
            try:
                self._start_pid_wait_thread(tool_name, pid)
            except Exception as e:
                self.logger.warning(f"启动PID等待线程失败: {e}")

    def stop_tracking(self, tool_name: str):
        """
        停止跟踪工具使用（手动停止）

        Args:
            tool_name: 工具名称
        """
        with self._lock:
            if tool_name in self.active_sessions:
                self._end_session(tool_name)
                self.logger.info(f"手动停止跟踪工具: {tool_name}")

    def _start_monitor_thread(self):
        """启动后台监控线程"""
        if self.monitor_thread and self.monitor_thread.is_alive():
            return

        self.is_monitoring = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_processes,
            daemon=True,
            name="ToolUsageMonitor"
        )
        self.monitor_thread.start()
        self.logger.info("工具使用监控线程已启动")

    def _monitor_processes(self):
        """后台监控进程（在独立线程中运行）"""
        while self.is_monitoring:
            try:
                time.sleep(self.check_interval)

                with self._lock:
                    # 检查每个活动会话
                    ended_tools = []

                    for tool_name, session in list(self.active_sessions.items()):
                        if not session.is_active:
                            continue

                        # 检查进程是否还在运行
                        if session.pid:
                            # 如果有PID，检查该进程是否存在
                            if not self._is_process_running(session.pid):
                                self.logger.info(f"检测到工具进程结束: {tool_name} (PID: {session.pid})")
                                ended_tools.append(tool_name)
                        else:
                            # 如果没有PID，通过进程名检查（不太准确）
                            if not self._is_tool_process_running(tool_name):
                                self.logger.info(f"检测到工具进程结束: {tool_name}")
                                ended_tools.append(tool_name)

                    # 结束已停止的会话
                    for tool_name in ended_tools:
                        self._end_session(tool_name)

            except Exception as e:
                self.logger.error(f"监控进程时发生错误: {e}")

        self.logger.info("工具使用监控线程已停止")

    def _start_pid_wait_thread(self, tool_name: str, pid: int):
        """
        启动一个专用线程等待指定PID退出，一旦退出立即结束会话并更新UI。

        说明：
        - 这是事件驱动的即时通知，优先于轮询；
        - 当PID不可用或进程模型复杂时，仍由轮询兜底。
        """
        t = threading.Thread(
            target=self._wait_for_process_end,
            args=(tool_name, pid),
            daemon=True,
            name=f"PIDWait-{tool_name}-{pid}"
        )
        t.start()
        self.logger.info(f"PID等待线程已启动: {t.name}")

    def _wait_for_process_end(self, tool_name: str, pid: int):
        """阻塞等待指定PID退出，然后立即结束会话。"""
        try:
            p = psutil.Process(pid)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            # 取不到进程，交给轮询兜底
            self.logger.info(f"PID等待放弃（进程不存在或无权限）: {tool_name}, PID={pid}")
            return

        try:
            p.wait()  # 阻塞直到进程退出
        except Exception as e:
            self.logger.warning(f"等待进程退出时发生异常: {tool_name}, PID={pid}, 错误: {e}")
            # 交由轮询兜底
            return

        # 进程已退出，尝试立即结束会话（避免与轮询线程冲突，按现有流程幂等）
        try:
            self.logger.info(f"检测到进程退出（PID等待线程）: {tool_name}, PID={pid}")
            self._end_session(tool_name)
        except Exception as e:
            self.logger.error(f"PID等待线程结束会话失败: {tool_name}, 错误: {e}")

    def _is_process_running(self, pid: int) -> bool:
        """检查指定PID的进程是否还在运行"""
        try:
            process = psutil.Process(pid)
            return process.is_running()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False

    def _is_tool_process_running(self, tool_name: str) -> bool:
        """
        通过进程名检查工具是否还在运行（不太准确，仅作为后备）

        Args:
            tool_name: 工具名称

        Returns:
            bool: 是否有匹配的进程在运行
        """
        try:
            # 常见工具的进程名映射
            process_name_map = {
                'Cytoscape': ['cytoscape.exe', 'java.exe', 'javaw.exe'],  # Cytoscape 使用 Java
                'IGV': ['igv.exe', 'java.exe', 'javaw.exe'],
                'FastQC': ['fastqc.exe', 'java.exe', 'javaw.exe'],
                'BLAST': ['blastn.exe', 'blastp.exe', 'blastx.exe'],
                'BWA': ['bwa.exe'],
                'SAMtools': ['samtools.exe'],
            }

            possible_names = process_name_map.get(tool_name, [f"{tool_name.lower()}.exe"])

            for proc in psutil.process_iter(['name']):
                try:
                    proc_name = proc.info['name']
                    if proc_name and any(name.lower() in proc_name.lower() for name in possible_names):
                        return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            return False
        except Exception as e:
            self.logger.error(f"检查工具进程时发生错误: {e}")
            return False

    def _end_session(self, tool_name: str):
        """
        结束工具使用会话并更新统计

        Args:
            tool_name: 工具名称
        """
        if tool_name not in self.active_sessions:
            return

        session = self.active_sessions[tool_name]
        session.mark_ended()

        # 更新配置文件中的使用统计
        self._update_tool_usage_stats(tool_name, session)

        # 从活动会话中移除
        del self.active_sessions[tool_name]

        # 如果没有活动会话了，可以考虑停止监控（可选）
        # if not self.active_sessions:
        #     self.is_monitoring = False

    def _update_tool_usage_stats(self, tool_name: str, session: ToolUsageSession):
        """
        更新工具使用统计到配置文件

        Args:
            tool_name: 工具名称
            session: 使用会话
        """
        try:
            # 获取当前工具数据
            tools = self.config_manager.tools
            tool_data = None

            for tool in tools:
                if tool.get('name') == tool_name:
                    tool_data = tool
                    break

            if not tool_data:
                self.logger.warning(f"未找到工具数据: {tool_name}")
                return

            # 更新 last_used
            tool_data['last_used'] = session.end_time.isoformat() if session.end_time else datetime.now().isoformat()

            # 累加 total_runtime
            current_runtime = tool_data.get('total_runtime', 0)
            new_runtime = current_runtime + session.duration_seconds
            tool_data['total_runtime'] = new_runtime

            # 保存到配置文件
            self.config_manager.save_tools()

            self.logger.info(
                f"更新工具使用统计: {tool_name}, "
                f"本次: {session.duration_seconds}秒, "
                f"总计: {new_runtime}秒 ({new_runtime//3600}小时{(new_runtime%3600)//60}分钟)"
            )

            # 🔥 关键修复：从Python threading.Thread中发射信号需要使用QMetaObject.invokeMethod
            # 强制在主线程的事件循环中发射信号
            self.logger.info(f"🔔 [Tracker-信号发射] 使用QMetaObject.invokeMethod发射信号: {tool_name}, {new_runtime}秒")
            try:
                # 使用 Qt.QueuedConnection 确保在主线程中执行
                QMetaObject.invokeMethod(
                    self,
                    "_emit_usage_updated",
                    Qt.QueuedConnection,
                    Q_ARG(str, tool_name),
                    Q_ARG(int, new_runtime)
                )
                self.logger.info(f"✅ [Tracker-信号成功] 信号发射已排队到主线程")
            except Exception as signal_error:
                self.logger.error(f"❌ [Tracker-信号失败] 信号发射出错: {signal_error}")
                import traceback
                self.logger.error(traceback.format_exc())

            # 🔥 仍然调用回调函数以兼容旧代码（如果有）
            if self.on_usage_updated:
                self.logger.info(f"🔔 [Tracker-回调触发] 同时调用旧的回调函数（兼容）: {tool_name}")
                try:
                    self.on_usage_updated(tool_name, new_runtime)
                    self.logger.info(f"✅ [Tracker-回调成功] 回调函数执行完成")
                except Exception as callback_error:
                    self.logger.error(f"❌ [Tracker-回调失败] 回调函数执行出错: {callback_error}")
                    import traceback
                    self.logger.error(traceback.format_exc())

        except Exception as e:
            self.logger.error(f"更新工具使用统计失败: {tool_name}, 错误: {e}")

    def get_active_sessions(self) -> Dict[str, ToolUsageSession]:
        """获取所有活动会话"""
        with self._lock:
            return self.active_sessions.copy()

    def get_session_info(self, tool_name: str) -> Optional[Dict]:
        """
        获取指定工具的会话信息

        Args:
            tool_name: 工具名称

        Returns:
            会话信息字典，如果没有活动会话则返回 None
        """
        with self._lock:
            session = self.active_sessions.get(tool_name)
            if session:
                return {
                    'tool_name': session.tool_name,
                    'pid': session.pid,
                    'start_time': session.start_time.isoformat(),
                    'current_duration': session.get_current_duration(),
                    'is_active': session.is_active
                }
        return None

    def stop_all_tracking(self):
        """停止所有跟踪（应用关闭时调用）"""
        with self._lock:
            self.logger.info("停止所有工具使用跟踪")

            # 结束所有活动会话
            for tool_name in list(self.active_sessions.keys()):
                self._end_session(tool_name)

            # 停止监控线程
            self.is_monitoring = False

    def __del__(self):
        """析构函数：确保清理资源"""
        try:
            self.stop_all_tracking()
        except Exception:
            pass


# 全局单例
_tracker_instance: Optional[ToolUsageTracker] = None


def get_tool_usage_tracker(config_manager=None) -> Optional[ToolUsageTracker]:
    """
    获取工具使用跟踪器单例

    Args:
        config_manager: 配置管理器（首次调用时必须提供）

    Returns:
        ToolUsageTracker 实例
    """
    global _tracker_instance

    if _tracker_instance is None:
        if config_manager is None:
            logging.warning("首次获取 ToolUsageTracker 需要提供 config_manager")
            return None
        _tracker_instance = ToolUsageTracker(config_manager)

    return _tracker_instance
