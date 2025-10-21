"""
路径解析工具
负责解析相对路径和绝对路径，从配置读取路径设置
"""
import os
from pathlib import Path
from typing import Optional


class PathResolver:
    """路径解析器 - 统一管理所有路径设置"""

    _instance = None
    _config_manager = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def set_config_manager(cls, config_manager):
        """设置配置管理器"""
        cls._config_manager = config_manager

    @classmethod
    def resolve_path(cls, path_str: str) -> Path:
        """
        解析路径（支持相对路径和绝对路径）

        Args:
            path_str: 路径字符串

        Returns:
            Path: 解析后的完整路径
        """
        if not path_str:
            return Path.cwd()

        path = Path(path_str)

        # 判断是否为绝对路径
        if path.is_absolute():
            return path
        else:
            # 相对路径：相对于软件运行目录
            return Path.cwd() / path

    @classmethod
    def get_install_dir(cls) -> Path:
        """
        获取工具安装目录

        Returns:
            Path: 工具安装目录的完整路径
        """
        if cls._config_manager is None:
            # 如果没有配置管理器，使用默认值
            return Path.cwd() / "installed_tools"

        # 从配置读取
        install_dir = getattr(cls._config_manager.settings, 'default_install_dir', '')

        if not install_dir:
            # 如果配置为空，使用默认值
            return Path.cwd() / "installed_tools"

        # 解析路径
        return cls.resolve_path(install_dir)

    @classmethod
    def get_env_cache_dir(cls) -> Path:
        """
        获取环境缓存目录（Conda/Java/Python等）

        Returns:
            Path: 环境缓存目录的完整路径
        """
        if cls._config_manager is None:
            # 如果没有配置管理器，使用默认值
            return Path.cwd() / "envs_cache"

        # 从配置读取
        env_path = getattr(cls._config_manager.settings, 'conda_env_path', '')

        if not env_path:
            # 如果配置为空，使用默认值
            return Path.cwd() / "envs_cache"

        # 解析路径
        return cls.resolve_path(env_path)


def get_path_resolver() -> PathResolver:
    """获取路径解析器单例"""
    return PathResolver()
