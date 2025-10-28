"""
Web启动器基类
用于需要打开网页的生物信息学工具（如NCBI BLAST在线版）
只记录启动次数，不记录使用时长
"""
import webbrowser
import logging
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any

from .base import ToolInterface
from utils.unified_logger import get_logger


class WebLauncherTool(ToolInterface):
    """
    Web启动器工具基类

    特性:
    1. 通过系统默认浏览器打开指定URL
    2. 只记录启动次数（无法准确记录使用时长）
    3. 不需要安装/卸载
    4. 不需要验证安装状态

    子类只需要定义METADATA字典，包含URL字段
    """

    # 子类需要覆盖这个元数据
    METADATA = {
        'name': 'WebTool',
        'version': '1.0',
        'category': 'web',
        'description': 'Web工具基类',
        'url': 'https://example.com',  # 必需：要打开的URL
        'size': 'N/A',
        'requires': [],
        'status': 'available',  # Web工具始终可用
        'homepage': '',
        'documentation': '',
        'license': '',
        'tool_type': 'web_launcher'  # 标识这是Web启动器
    }

    def __init__(self):
        """初始化Web启动器"""
        self.logger = logging.getLogger(__name__)
        self.unified_logger = get_logger()
        self.unified_logger.log_runtime(f"{self.METADATA['name']} Web启动器初始化完成")

    def get_metadata(self) -> Dict[str, Any]:
        """
        获取工具元数据
        Web工具始终可用，不需要安装
        """
        metadata = dict(self.METADATA)
        metadata['status'] = 'available'  # Web工具始终可用
        return metadata

    def get_download_sources(self) -> List[Dict[str, Any]]:
        """
        Web工具不需要下载
        """
        return []

    def check_dependencies(self) -> Dict[str, bool]:
        """
        Web工具只需要系统浏览器，无其他依赖
        """
        return {
            'browser': True  # 假设系统总有浏览器
        }

    def install(self, progress_callback: Optional[Callable[[str, int], None]] = None) -> bool:
        """
        Web工具不需要安装
        直接返回成功
        """
        if progress_callback:
            progress_callback(f"{self.METADATA['name']} 是Web工具，无需安装", 100)

        self.unified_logger.log_runtime(f"{self.METADATA['name']} 是Web工具，无需安装")
        return True

    def verify_installation(self) -> bool:
        """
        Web工具始终视为"已安装"（可用）
        """
        return True

    def launch(self, args: Optional[List[str]] = None) -> bool:
        """
        启动Web工具
        使用系统默认浏览器打开URL

        Args:
            args: 可选参数（Web工具通常不需要）

        Returns:
            bool: 是否成功打开浏览器
        """
        try:
            url = self.METADATA.get('url')
            if not url:
                self.unified_logger.log_error(
                    f"{self.METADATA['name']}启动",
                    "未配置URL"
                )
                return False

            self.unified_logger.log_runtime(f"打开浏览器访问: {url}")

            # 使用webbrowser模块打开URL
            success = webbrowser.open(url)

            if success:
                self.unified_logger.log_operation(f'启动{self.METADATA["name"]}', {
                    'url': url,
                    'type': 'web_launcher'
                })
                return True
            else:
                self.unified_logger.log_error(
                    f"{self.METADATA['name']}启动",
                    "无法打开浏览器"
                )
                return False

        except Exception as e:
            self.unified_logger.log_error(
                f"{self.METADATA['name']}启动",
                f"启动失败: {e}"
            )
            return False

    def uninstall(self) -> bool:
        """
        Web工具不需要卸载
        直接返回成功
        """
        self.unified_logger.log_runtime(f"{self.METADATA['name']} 是Web工具，无需卸载")
        return True

    def get_installation_info(self) -> Optional[Dict[str, Any]]:
        """
        获取Web工具信息
        """
        return {
            'type': 'web_launcher',
            'url': self.METADATA.get('url', ''),
            'size_mb': 0,
            'size_text': 'N/A (Web工具)'
        }
