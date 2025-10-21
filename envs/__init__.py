"""
BioNexus 环境管理系统
提供完整的运行环境自动化管理功能
支持Java、Python、Conda、R等多种运行时环境

v1.1.12: 全新的环境管理架构
- 零配置用户体验
- 智能依赖解析
- 自动环境隔离
- 统一更新管理
"""

from .manager import EnvironmentManager
from .runtime import JavaRuntime, PythonRuntime
from .resolver import DependencyResolver

__version__ = "1.1.12"
__all__ = [
    'EnvironmentManager',
    'JavaRuntime', 
    'PythonRuntime',
    'DependencyResolver'
]