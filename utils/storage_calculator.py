#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
存储计算工具模块
提供准确的文件大小计算和磁盘空间检查功能
"""

import os
import shutil
import platform
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import logging


@dataclass
class ToolStorageInfo:
    """工具存储信息"""
    name: str                    # 工具名称
    path: str                   # 安装路径
    size: int                   # 占用空间（字节）
    status: str                 # 安装状态
    dependencies: List[str]     # 依赖环境列表
    install_date: str = ""      # 安装日期（如果有记录）


class StorageCalculator:
    """
    存储计算器
    提供工具和系统的存储相关计算功能
    """
    
    def __init__(self, project_root: Path = None):
        """初始化存储计算器"""
        self.logger = logging.getLogger(__name__)
        
        if project_root is None:
            project_root = Path(__file__).parent.parent
        
        self.project_root = project_root
        self.installed_tools_dir = project_root / "installed_tools"
        self.envs_cache_dir = project_root / "envs_cache"
        
        # 缓存计算结果（避免重复计算大目录）
        self._size_cache = {}
    
    def get_directory_size(self, directory_path: Path, use_cache: bool = True) -> int:
        """
        计算目录占用空间（字节）
        
        Args:
            directory_path: 目录路径
            use_cache: 是否使用缓存
            
        Returns:
            int: 目录大小（字节）
        """
        if not directory_path.exists():
            return 0
        
        directory_str = str(directory_path)
        
        # 检查缓存
        if use_cache and directory_str in self._size_cache:
            return self._size_cache[directory_str]
        
        total_size = 0
        
        try:
            for dirpath, dirnames, filenames in os.walk(directory_path):
                for filename in filenames:
                    file_path = os.path.join(dirpath, filename)
                    try:
                        # 使用os.path.getsize而不是Path.stat，更快速
                        total_size += os.path.getsize(file_path)
                    except (OSError, FileNotFoundError):
                        # 忽略无法访问的文件（可能是符号链接等）
                        continue
        except Exception as e:
            self.logger.warning(f"计算目录大小失败 {directory_path}: {e}")
        
        # 缓存结果
        if use_cache:
            self._size_cache[directory_str] = total_size
        
        return total_size
    
    def get_tool_storage_info(self, tool_name: str) -> Optional[ToolStorageInfo]:
        """
        获取单个工具的存储信息
        
        Args:
            tool_name: 工具名称
            
        Returns:
            ToolStorageInfo: 工具存储信息，不存在返回None
        """
        tool_path = self.installed_tools_dir / tool_name
        
        if not tool_path.exists():
            return None
        
        # 计算工具大小
        tool_size = self.get_directory_size(tool_path)
        
        # 从依赖管理器获取依赖信息
        try:
            from utils.dependency_manager import get_dependency_manager
            dep_manager = get_dependency_manager()
            dependencies = dep_manager.get_tool_dependencies(tool_name)
        except:
            dependencies = []
        
        return ToolStorageInfo(
            name=tool_name,
            path=str(tool_path),
            size=tool_size,
            status="installed",
            dependencies=dependencies
        )
    
    def get_all_tools_storage_info(self) -> List[ToolStorageInfo]:
        """
        获取所有已安装工具的存储信息
        
        Returns:
            List[ToolStorageInfo]: 工具存储信息列表，按大小降序排序
        """
        tools_info = []
        
        if not self.installed_tools_dir.exists():
            return tools_info
        
        for tool_dir in self.installed_tools_dir.iterdir():
            if tool_dir.is_dir():
                tool_info = self.get_tool_storage_info(tool_dir.name)
                if tool_info:
                    tools_info.append(tool_info)
        
        # 按大小降序排序
        tools_info.sort(key=lambda x: x.size, reverse=True)
        
        return tools_info
    
    def get_system_disk_info(self) -> Dict[str, int]:
        """
        获取系统磁盘空间信息
        
        Returns:
            Dict: 包含总空间、已用空间、可用空间的字典（字节）
        """
        try:
            if platform.system() == "Windows":
                # Windows系统使用项目所在驱动器
                drive = Path(self.project_root).drive
                total, used, free = shutil.disk_usage(drive)
            else:
                # Linux/macOS系统使用项目目录的挂载点
                total, used, free = shutil.disk_usage(self.project_root)
            
            return {
                'total': total,
                'used': used, 
                'free': free
            }
        except Exception as e:
            self.logger.error(f"获取磁盘信息失败: {e}")
            return {'total': 0, 'used': 0, 'free': 0}
    
    def check_sufficient_space(self, required_bytes: int) -> Tuple[bool, int]:
        """
        检查磁盘空间是否足够
        
        Args:
            required_bytes: 需要的空间（字节）
            
        Returns:
            Tuple[bool, int]: (是否足够, 可用空间字节)
        """
        disk_info = self.get_system_disk_info()
        free_space = disk_info['free']
        
        return free_space >= required_bytes, free_space
    
    def should_show_space_warning(self, required_bytes: int = 0) -> Tuple[bool, str]:
        """
        检查是否需要显示空间警告
        
        Args:
            required_bytes: 即将安装工具需要的空间（字节）
            
        Returns:
            Tuple[bool, str]: (是否显示警告, 警告信息)
        """
        disk_info = self.get_system_disk_info()
        free_gb = disk_info['free'] / (1024**3)  # 转换为GB
        
        # 系统空间小于10GB时显示警告
        if free_gb < 10.0:
            if required_bytes > 0:
                required_mb = required_bytes / (1024**2)
                warning_msg = (f"您的存储空间仅剩 {self.format_size(disk_info['free'])}，"
                             f"此工具预计需要 {required_mb:.1f} MB，是否继续安装？")
            else:
                warning_msg = f"您的存储空间仅剩 {self.format_size(disk_info['free'])}，是否继续安装？"
            
            return True, warning_msg
        
        return False, ""
    
    def get_storage_summary(self) -> Dict:
        """
        获取存储使用摘要
        
        Returns:
            Dict: 存储摘要信息
        """
        tools_info = self.get_all_tools_storage_info()
        disk_info = self.get_system_disk_info()
        
        # 计算BioNexus占用的总空间
        bionexus_size = 0
        if self.project_root.exists():
            bionexus_size = self.get_directory_size(self.project_root, use_cache=False)
        
        # 计算各部分占用
        tools_size = sum(tool.size for tool in tools_info)
        envs_size = 0
        if self.envs_cache_dir.exists():
            envs_size = self.get_directory_size(self.envs_cache_dir)
        
        return {
            'system_total': disk_info['total'],
            'system_free': disk_info['free'],
            'system_used': disk_info['used'],
            'bionexus_total': bionexus_size,
            'tools_count': len(tools_info),
            'tools_size': tools_size,
            'environments_size': envs_size,
            'largest_tool': tools_info[0] if tools_info else None,
            'total_tools_size': tools_size + envs_size
        }
    
    def calculate_deletion_savings(self, tool_names: List[str]) -> Dict:
        """
        计算删除指定工具能节省的空间
        
        Args:
            tool_names: 要删除的工具名列表
            
        Returns:
            Dict: 删除分析结果
        """
        from utils.dependency_manager import get_dependency_manager
        
        tools_size = 0
        missing_tools = []
        
        # 计算工具占用空间
        for tool_name in tool_names:
            tool_info = self.get_tool_storage_info(tool_name)
            if tool_info:
                tools_size += tool_info.size
            else:
                missing_tools.append(tool_name)
        
        # 计算可清理的环境空间
        dep_manager = get_dependency_manager()
        cleanup_candidates = dep_manager.check_cleanup_candidates(tool_names)
        
        envs_size = sum(env.size for env in cleanup_candidates)
        
        return {
            'tools_size': tools_size,
            'environments_size': envs_size,
            'total_savings': tools_size + envs_size,
            'cleanup_environments': [env.name for env in cleanup_candidates],
            'missing_tools': missing_tools
        }
    
    def clear_cache(self):
        """清空大小计算缓存"""
        self._size_cache.clear()
    
    @staticmethod
    def format_size(size_bytes: int) -> str:
        """
        格式化文件大小显示
        
        Args:
            size_bytes: 字节数
            
        Returns:
            str: 格式化的大小字符串
        """
        if size_bytes == 0:
            return "0 B"
        
        units = ['B', 'KB', 'MB', 'GB', 'TB']
        unit_index = 0
        size = float(size_bytes)
        
        while size >= 1024 and unit_index < len(units) - 1:
            size /= 1024
            unit_index += 1
        
        if unit_index == 0:
            return f"{int(size)} {units[unit_index]}"
        else:
            return f"{size:.1f} {units[unit_index]}"
    
    @staticmethod
    def parse_size_string(size_str: str) -> int:
        """
        解析大小字符串为字节数
        
        Args:
            size_str: 大小字符串，如 "1.5 GB"
            
        Returns:
            int: 字节数
        """
        units = {'B': 1, 'KB': 1024, 'MB': 1024**2, 'GB': 1024**3, 'TB': 1024**4}
        
        try:
            parts = size_str.strip().split()
            if len(parts) != 2:
                return 0
            
            value = float(parts[0])
            unit = parts[1].upper()
            
            return int(value * units.get(unit, 1))
        except:
            return 0


# 全局存储计算器实例
_storage_calculator = None

def get_storage_calculator() -> StorageCalculator:
    """获取全局存储计算器实例"""
    global _storage_calculator
    if _storage_calculator is None:
        _storage_calculator = StorageCalculator()
    return _storage_calculator


if __name__ == "__main__":
    # 测试代码
    calc = StorageCalculator()
    
    print("=== 存储计算器测试 ===")
    
    # 测试磁盘信息
    disk_info = calc.get_system_disk_info()
    print(f"磁盘信息:")
    print(f"  总空间: {calc.format_size(disk_info['total'])}")
    print(f"  可用空间: {calc.format_size(disk_info['free'])}")
    print(f"  已用空间: {calc.format_size(disk_info['used'])}")
    
    # 测试空间警告
    show_warning, msg = calc.should_show_space_warning()
    print(f"\n空间警告: {show_warning}")
    if show_warning:
        print(f"  消息: {msg}")
    
    # 测试工具存储信息
    tools_info = calc.get_all_tools_storage_info()
    print(f"\n已安装工具 ({len(tools_info)} 个):")
    for tool in tools_info[:5]:  # 只显示前5个
        print(f"  {tool.name}: {calc.format_size(tool.size)}")
    
    # 测试存储摘要
    summary = calc.get_storage_summary()
    print(f"\n存储摘要:")
    print(f"  工具总大小: {calc.format_size(summary['tools_size'])}")
    print(f"  环境总大小: {calc.format_size(summary['environments_size'])}")
    print(f"  BioNexus总大小: {calc.format_size(summary['bionexus_total'])}")