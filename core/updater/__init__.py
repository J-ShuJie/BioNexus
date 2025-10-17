"""
BioNexus更新管理模块
提供自动更新和版本管理功能
"""

from .version_checker import VersionChecker
from .update_manager import UpdateManager

__all__ = ['VersionChecker', 'UpdateManager']