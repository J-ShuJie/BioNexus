"""
命令行工具基类
用于需要在终端窗口中运行的生物信息学工具（如SAMtools、BWA等）
通过跟踪终端窗口进程来记录使用时长
"""
import os
import subprocess
import logging
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any

from .base import ToolInterface
from utils.unified_logger import get_logger


class CLIToolBase(ToolInterface):
    """
    命令行工具基类

    特性：
    1. 打开新的终端窗口（Windows: cmd.exe / PowerShell）
    2. 自动配置工具环境变量（PATH等）
    3. 跟踪终端窗口进程，记录使用时长
    4. 用户可以在窗口中自由执行命令

    工作流程：
    - 启动 → 打开终端窗口（进程PID可跟踪）
    - 用户在窗口中使用工具
    - 关闭窗口 → 自动计算使用时长

    子类需要实现：
    - get_metadata()
    - get_download_sources()
    - install()
    - verify_installation()
    - uninstall()
    - _get_tool_path(): 返回工具可执行文件路径
    """

    def __init__(self):
        """初始化命令行工具基类"""
        self.logger = logging.getLogger(__name__)
        self.unified_logger = get_logger()

    def launch(self, args: Optional[List[str]] = None) -> bool:
        """
        启动命令行工具
        打开新的终端窗口，配置好工具环境

        Args:
            args: 可选参数（通常命令行工具不需要）

        Returns:
            bool: 是否成功启动终端窗口
        """
        if not self.verify_installation():
            self.unified_logger.log_error(
                f'{self.get_metadata()["name"]}启动',
                '工具未安装'
            )
            return False

        try:
            tool_name = self.get_metadata()['name']
            tool_path = self._get_tool_path()

            if not tool_path or not tool_path.exists():
                self.unified_logger.log_error(
                    f'{tool_name}启动',
                    f'工具路径不存在: {tool_path}'
                )
                return False

            # 获取工具目录
            tool_dir = tool_path.parent

            # 构建环境变量
            env = os.environ.copy()

            # 将工具目录添加到PATH最前面
            if os.name == 'nt':
                tool_dir_str = str(tool_dir).replace('/', '\\')
                current_path = env.get('PATH', '')
                env['PATH'] = f"{tool_dir_str};{current_path}"
            else:
                current_path = env.get('PATH', '')
                env['PATH'] = f"{tool_dir}:{current_path}"

            self.unified_logger.log_runtime(f"配置环境变量: PATH={env['PATH'][:200]}...")

            # 构建欢迎信息
            welcome_msg = self._generate_welcome_message()

            # 启动终端窗口
            if os.name == 'nt':
                # Windows: 使用cmd.exe
                # /K: 执行命令后保持窗口打开
                cmd = f'cmd.exe /K "echo {welcome_msg} && echo. && echo 工具已配置好，您可以直接使用 {tool_name.lower()} 命令 && echo 示例: {tool_name.lower()} --help && echo. && echo 关闭此窗口将自动记录使用时长 && echo =================================="'

                self.unified_logger.log_runtime(f"Windows启动命令: {cmd[:100]}...")

                process = subprocess.Popen(
                    cmd,
                    shell=True,
                    env=env,
                    creationflags=subprocess.CREATE_NEW_CONSOLE  # 新控制台窗口
                )
            else:
                # Linux/macOS: 使用终端
                # TODO: 需要根据系统检测合适的终端模拟器
                cmd = ['xterm', '-e', f'echo "{welcome_msg}"; bash']

                process = subprocess.Popen(
                    cmd,
                    env=env
                )

            pid = process.pid
            self.unified_logger.log_runtime(f"启动{tool_name}终端窗口: PID {pid}")

            self.unified_logger.log_operation(f'启动{tool_name}', {
                'type': 'cli_tool',
                'tool_path': str(tool_path),
                'working_dir': str(tool_dir),
                'pid': pid
            })

            return True

        except Exception as e:
            tool_name = self.get_metadata()['name']
            self.unified_logger.log_error(
                f'{tool_name}启动',
                f"启动失败: {e}"
            )
            return False

    def _get_tool_path(self) -> Optional[Path]:
        """
        获取工具可执行文件路径
        子类必须实现此方法

        Returns:
            Path: 工具可执行文件的完整路径
        """
        raise NotImplementedError("子类必须实现 _get_tool_path() 方法")

    def _generate_welcome_message(self) -> str:
        """
        生成欢迎信息

        Returns:
            str: 终端窗口显示的欢迎信息
        """
        metadata = self.get_metadata()
        tool_name = metadata.get('name', 'Tool')
        version = metadata.get('version', 'Unknown')

        welcome = f"==================================\n"
        welcome += f"  {tool_name} v{version} - BioNexus\n"
        welcome += f"=================================="

        return welcome

    def get_installation_info(self) -> Optional[Dict[str, Any]]:
        """
        获取安装信息
        子类可以覆盖此方法提供更详细的信息
        """
        if not self.verify_installation():
            return None

        tool_path = self._get_tool_path()
        if not tool_path:
            return None

        # 计算安装目录大小
        try:
            install_dir = tool_path.parent
            total_size = 0
            for file_path in install_dir.rglob('*'):
                if file_path.is_file():
                    total_size += file_path.stat().st_size

            size_mb = total_size / (1024 * 1024)

            return {
                'install_path': str(install_dir),
                'executable_path': str(tool_path),
                'size_mb': round(size_mb, 1),
                'size_text': f"{size_mb:.1f} MB",
                'type': 'cli_tool'
            }
        except Exception as e:
            self.unified_logger.log_error('获取安装信息', f"失败: {e}")
            return {
                'install_path': str(tool_path.parent) if tool_path else 'Unknown',
                'executable_path': str(tool_path) if tool_path else 'Unknown',
                'type': 'cli_tool'
            }
