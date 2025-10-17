#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
依赖管理模块
管理工具与运行环境的依赖关系，支持智能清理
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any
from dataclasses import dataclass


@dataclass
class EnvironmentInfo:
    """环境信息"""
    name: str                    # 环境名称，如 "java-11"
    path: str                    # 环境路径
    size: int                    # 占用空间（字节）
    users: List[str]            # 使用这个环境的工具列表
    version: str = ""           # 版本号
    description: str = ""       # 描述


class DependencyManager:
    """
    依赖管理器
    负责追踪工具与环境的依赖关系，支持智能清理
    """
    
    def __init__(self, project_root: Path = None):
        """初始化依赖管理器"""
        self.logger = logging.getLogger(__name__)
        
        if project_root is None:
            project_root = Path(__file__).parent.parent
        
        self.project_root = project_root
        self.envs_cache_dir = project_root / "envs_cache"
        self.dependencies_file = project_root / "data" / "dependencies.json"
        
        # 依赖关系映射
        self._tool_dependencies: Dict[str, List[str]] = {}
        self._environment_users: Dict[str, List[str]] = {}
        
        # 加载依赖关系
        self.load_dependencies()
    
    def load_dependencies(self):
        """加载依赖关系配置"""
        if self.dependencies_file.exists():
            try:
                with open(self.dependencies_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._tool_dependencies = data.get('tool_dependencies', {})
                    self.logger.info(f"已加载 {len(self._tool_dependencies)} 个工具的依赖关系")
            except Exception as e:
                self.logger.error(f"加载依赖关系失败: {e}")
        else:
            # 创建默认依赖关系
            self._create_default_dependencies()
        
        # 构建反向索引
        self._build_environment_users()
    
    def _create_default_dependencies(self):
        """创建默认的依赖关系"""
        self._tool_dependencies = {
            "FastQC": ["java-11"],
            "BLAST": ["python-3.8"],
            "BWA": ["gcc-runtime"],
            "SAMtools": ["python-3.8"],
            "HISAT2": ["python-3.8", "gcc-runtime"],
            "IQ-TREE": ["gcc-runtime"],
        }
        self.save_dependencies()
    
    def _build_environment_users(self):
        """构建环境用户的反向索引"""
        self._environment_users = {}
        
        for tool, envs in self._tool_dependencies.items():
            for env in envs:
                if env not in self._environment_users:
                    self._environment_users[env] = []
                if tool not in self._environment_users[env]:
                    self._environment_users[env].append(tool)
    
    def save_dependencies(self):
        """保存依赖关系到文件"""
        try:
            # 确保目录存在
            self.dependencies_file.parent.mkdir(exist_ok=True)
            
            data = {
                'tool_dependencies': self._tool_dependencies,
                'last_updated': '2025-01-15',
                'version': '1.0'
            }
            
            with open(self.dependencies_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            self.logger.info("依赖关系已保存")
        except Exception as e:
            self.logger.error(f"保存依赖关系失败: {e}")
    
    def get_tool_dependencies(self, tool_name: str) -> List[str]:
        """获取工具的依赖环境列表"""
        return self._tool_dependencies.get(tool_name, [])
    
    def get_environment_users(self, env_name: str) -> List[str]:
        """获取使用指定环境的工具列表"""
        return self._environment_users.get(env_name, [])
    
    def add_tool_dependency(self, tool_name: str, env_name: str):
        """添加工具依赖"""
        if tool_name not in self._tool_dependencies:
            self._tool_dependencies[tool_name] = []
        
        if env_name not in self._tool_dependencies[tool_name]:
            self._tool_dependencies[tool_name].append(env_name)
            self._build_environment_users()
            self.save_dependencies()
            self.logger.info(f"已添加依赖: {tool_name} -> {env_name}")
    
    def remove_tool_dependencies(self, tool_name: str):
        """移除工具的所有依赖"""
        if tool_name in self._tool_dependencies:
            del self._tool_dependencies[tool_name]
            self._build_environment_users()
            self.save_dependencies()
            self.logger.info(f"已移除工具依赖: {tool_name}")
    
    def check_cleanup_candidates(self, tools_to_delete: List[str]) -> List[EnvironmentInfo]:
        """
        检查删除工具后可以清理的环境
        
        Args:
            tools_to_delete: 要删除的工具列表
            
        Returns:
            可以清理的环境信息列表
        """
        # 1. 收集所有要删除工具的依赖环境
        all_dependencies = set()
        for tool in tools_to_delete:
            dependencies = self.get_tool_dependencies(tool)
            all_dependencies.update(dependencies)
        
        # 2. 检查每个依赖环境是否还被其他工具使用
        cleanup_candidates = []
        
        for env_name in all_dependencies:
            users = self.get_environment_users(env_name)
            # 移除即将删除的工具
            remaining_users = [u for u in users if u not in tools_to_delete]
            
            if not remaining_users:
                # 没有其他工具使用这个环境了，可以清理
                env_info = self.get_environment_info(env_name)
                if env_info:
                    cleanup_candidates.append(env_info)
        
        return cleanup_candidates
    
    def get_environment_info(self, env_name: str) -> EnvironmentInfo:
        """获取环境详细信息"""
        env_path = self.envs_cache_dir / env_name
        
        if not env_path.exists():
            return None
        
        # 计算环境占用空间
        size = self._calculate_directory_size(env_path)
        
        # 获取使用者列表
        users = self.get_environment_users(env_name)
        
        return EnvironmentInfo(
            name=env_name,
            path=str(env_path),
            size=size,
            users=users,
            version=self._detect_version(env_path),
            description=self._get_environment_description(env_name)
        )
    
    def get_all_environments(self) -> List[EnvironmentInfo]:
        """获取所有环境信息"""
        environments = []
        
        if not self.envs_cache_dir.exists():
            return environments
        
        for env_dir in self.envs_cache_dir.iterdir():
            if env_dir.is_dir():
                env_info = self.get_environment_info(env_dir.name)
                if env_info:
                    environments.append(env_info)
        
        return environments
    
    def _calculate_directory_size(self, directory: Path) -> int:
        """计算目录占用空间（字节）"""
        total_size = 0
        try:
            for dirpath, dirnames, filenames in os.walk(directory):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    try:
                        total_size += os.path.getsize(filepath)
                    except (OSError, FileNotFoundError):
                        # 忽略无法访问的文件
                        continue
        except Exception as e:
            self.logger.warning(f"计算目录大小失败 {directory}: {e}")
        
        return total_size
    
    def _detect_version(self, env_path: Path) -> str:
        """检测环境版本"""
        # Java环境版本检测
        if "java" in env_path.name.lower():
            return env_path.name.replace("java-", "").replace("java", "")
        
        # Python环境版本检测  
        if "python" in env_path.name.lower():
            return env_path.name.replace("python-", "").replace("python", "")
        
        return "unknown"
    
    def _get_environment_description(self, env_name: str) -> str:
        """获取环境描述"""
        descriptions = {
            "java-11": "Java 11 运行时环境",
            "java-8": "Java 8 运行时环境",
            "python-3.8": "Python 3.8 运行环境",
            "gcc-runtime": "GCC 运行时库",
        }
        return descriptions.get(env_name, f"{env_name} 运行环境")
    
    def cleanup_environment(self, env_name: str) -> bool:
        """
        清理指定环境
        
        Args:
            env_name: 环境名称
            
        Returns:
            是否成功清理
        """
        env_path = self.envs_cache_dir / env_name
        
        if not env_path.exists():
            self.logger.warning(f"环境不存在: {env_name}")
            return False
        
        # 检查是否还有工具在使用
        users = self.get_environment_users(env_name)
        if users:
            self.logger.warning(f"环境 {env_name} 仍被工具使用: {users}")
            return False
        
        try:
            import shutil
            shutil.rmtree(env_path)
            self.logger.info(f"已清理环境: {env_name}")
            return True
        except Exception as e:
            self.logger.error(f"清理环境失败 {env_name}: {e}")
            return False
    
    def format_size(self, size_bytes: int) -> str:
        """格式化文件大小显示"""
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
    
    def get_dependency_summary(self) -> Dict[str, Any]:
        """获取依赖关系统计摘要"""
        summary = {
            'total_tools': len(self._tool_dependencies),
            'total_environments': len(self._environment_users),
            'environment_usage': {},
            'orphaned_environments': []
        }
        
        # 统计每个环境的使用情况
        for env_name, users in self._environment_users.items():
            summary['environment_usage'][env_name] = len(users)
            
            # 检查是否有孤立环境（无工具使用）
            if not users:
                summary['orphaned_environments'].append(env_name)
        
        return summary


# 全局依赖管理器实例
_dependency_manager = None

def get_dependency_manager() -> DependencyManager:
    """获取全局依赖管理器实例"""
    global _dependency_manager
    if _dependency_manager is None:
        _dependency_manager = DependencyManager()
    return _dependency_manager


if __name__ == "__main__":
    # 测试代码
    manager = DependencyManager()
    
    # 测试依赖关系
    print("=== 依赖关系测试 ===")
    tools = ["FastQC", "BLAST", "SAMtools"]
    for tool in tools:
        deps = manager.get_tool_dependencies(tool)
        print(f"{tool} 依赖: {deps}")
    
    # 测试清理检查
    print("\n=== 清理检查测试 ===")
    to_delete = ["FastQC"]
    candidates = manager.check_cleanup_candidates(to_delete)
    print(f"删除 {to_delete} 后可清理的环境:")
    for env in candidates:
        print(f"  {env.name}: {manager.format_size(env.size)}")
    
    # 测试环境信息
    print("\n=== 环境信息测试 ===")
    all_envs = manager.get_all_environments()
    for env in all_envs:
        print(f"{env.name}: {manager.format_size(env.size)}, 用户: {env.users}")