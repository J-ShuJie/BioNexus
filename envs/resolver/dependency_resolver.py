"""
依赖解析器
智能解析工具的环境依赖需求，解决版本冲突
生成最优的环境安装策略
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class InstallationStep:
    """安装步骤"""
    type: str  # 'java', 'python', 'conda', etc.
    name: str
    version: str
    packages: List[str] = None
    isolation_strategy: str = 'shared'  # 'shared', 'isolated', 'portable'
    priority: int = 1
    dependencies: List[str] = None
    
    def __post_init__(self):
        if self.packages is None:
            self.packages = []
        if self.dependencies is None:
            self.dependencies = []


@dataclass 
class DependencyPlan:
    """依赖安装计划"""
    tool_name: str
    installation_steps: List[Dict[str, Any]]
    conflicts_resolved: List[Dict[str, Any]]
    estimated_time_minutes: int
    estimated_size_mb: int
    isolation_level: str  # 'none', 'partial', 'full'


class DependencyResolver:
    """依赖解析器"""
    
    def __init__(self):
        """初始化依赖解析器"""
        self.logger = logging.getLogger(__name__)
        
        # 加载兼容性规则
        self.compatibility_rules = self._load_compatibility_rules()
        
        # 默认隔离策略
        self.default_isolation_strategies = {
            'java': 'shared',      # Java工具可以共享JRE
            'python': 'isolated',  # Python工具使用虚拟环境
            'conda': 'isolated',   # Conda工具使用独立环境
            'r': 'isolated'        # R工具使用独立环境
        }
    
    def _load_compatibility_rules(self) -> Dict[str, Any]:
        """加载兼容性规则"""
        # 内置兼容性规则
        return {
            'java_compatibility': {
                # Java版本向下兼容性
                '17': ['17', '16', '15', '14', '13', '12', '11'],
                '11': ['11', '10', '9', '8'],
                '8': ['8']
            },
            'python_compatibility': {
                # Python版本兼容性更严格
                '3.11': ['3.11'],
                '3.10': ['3.10'],
                '3.9': ['3.9'],
                '3.8': ['3.8']
            },
            'conflict_resolution': {
                # 冲突解决策略
                'java_version_conflict': 'create_isolated',
                'python_version_conflict': 'create_venv',
                'package_conflict': 'use_latest_compatible'
            }
        }
    
    def resolve_dependencies(self, tool_name: str, requirements: Dict[str, Any]) -> DependencyPlan:
        """
        解析工具的依赖需求
        
        Args:
            tool_name: 工具名称
            requirements: 环境需求字典
            
        Returns:
            依赖安装计划
        """
        self.logger.info(f"解析依赖: {tool_name}")
        
        installation_steps = []
        conflicts_resolved = []
        estimated_time = 0
        estimated_size = 0
        isolation_level = 'none'
        
        # 解析Java依赖
        if 'java' in requirements:
            java_step = self._resolve_java_dependency(tool_name, requirements['java'])
            if java_step:
                installation_steps.append(java_step)
                estimated_time += java_step.get('estimated_time_minutes', 2)
                estimated_size += java_step.get('estimated_size_mb', 45)
                
                if java_step.get('isolation_strategy') == 'isolated':
                    isolation_level = 'partial'
        
        # 解析Python依赖
        if 'python' in requirements:
            python_step = self._resolve_python_dependency(tool_name, requirements['python'])
            if python_step:
                installation_steps.append(python_step)
                estimated_time += python_step.get('estimated_time_minutes', 1)
                estimated_size += python_step.get('estimated_size_mb', 15)
                
                if python_step.get('isolation_strategy') == 'isolated':
                    isolation_level = 'full' if isolation_level == 'partial' else 'partial'
        
        # 转换为字典格式
        step_dicts = []
        for step in installation_steps:
            if isinstance(step, InstallationStep):
                step_dicts.append({
                    'type': step.type,
                    'name': step.name, 
                    'version': step.version,
                    'packages': step.packages,
                    'isolation_strategy': step.isolation_strategy,
                    'priority': step.priority
                })
            else:
                step_dicts.append(step)
        
        return DependencyPlan(
            tool_name=tool_name,
            installation_steps=step_dicts,
            conflicts_resolved=conflicts_resolved,
            estimated_time_minutes=estimated_time,
            estimated_size_mb=estimated_size,
            isolation_level=isolation_level
        )
    
    def _resolve_java_dependency(self, tool_name: str, java_req: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """解析Java依赖"""
        required_version = java_req.get('version', '11+')
        
        # 确定最佳Java版本
        best_version = self._determine_best_java_version(required_version)
        
        # 确定隔离策略
        isolation_strategy = java_req.get('isolation', self.default_isolation_strategies['java'])
        
        # 检查是否需要隔离（如果存在版本冲突）
        if self._has_java_version_conflict(best_version):
            isolation_strategy = 'isolated'
        
        return {
            'type': 'java',
            'name': f'Java {best_version} Runtime',
            'version': best_version,
            'packages': [],
            'isolation_strategy': isolation_strategy,
            'priority': 1,
            'estimated_time_minutes': 2,
            'estimated_size_mb': 45
        }
    
    def _resolve_python_dependency(self, tool_name: str, python_req: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """解析Python依赖"""
        required_version = python_req.get('version', '3.10+')
        required_packages = python_req.get('packages', [])
        
        # 确定最佳Python版本
        best_version = self._determine_best_python_version(required_version)
        
        # Python工具默认使用虚拟环境隔离
        isolation_strategy = python_req.get('isolation', 'isolated')
        
        return {
            'type': 'python',
            'name': f'Python {best_version} Environment',
            'version': best_version,
            'packages': required_packages,
            'isolation_strategy': isolation_strategy,
            'priority': 2,
            'estimated_time_minutes': len(required_packages) // 3 + 1,
            'estimated_size_mb': len(required_packages) * 5 + 15
        }
    
    def _determine_best_java_version(self, requirement: str) -> str:
        """确定最佳Java版本"""
        if '+' in requirement:
            # "8+" -> 推荐11 (当前主流LTS)
            min_version = int(requirement.replace('+', ''))
            if min_version <= 8:
                return '11'
            elif min_version <= 11:
                return '11' 
            else:
                return '17'
        else:
            # 精确版本
            return requirement
    
    def _determine_best_python_version(self, requirement: str) -> str:
        """确定最佳Python版本"""
        if '+' in requirement:
            # "3.8+" -> 推荐3.10
            base_version = requirement.replace('+', '')
            if base_version <= '3.8':
                return '3.10'
            else:
                return base_version
        else:
            return requirement
    
    def _has_java_version_conflict(self, required_version: str) -> bool:
        """检查Java版本冲突"""
        # TODO: 实现实际的冲突检测逻辑
        # 这里应该检查系统中已安装的Java版本和正在使用的工具
        return False
    
    def analyze_dependency_changes(self, tool_name: str, old_requirements: Dict[str, Any], 
                                 new_requirements: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析依赖变化
        
        Args:
            tool_name: 工具名称
            old_requirements: 旧的依赖需求
            new_requirements: 新的依赖需求
            
        Returns:
            依赖变化分析结果
        """
        changes = {
            'has_breaking_changes': False,
            'java_version_changed': False,
            'python_version_changed': False,
            'packages_changed': [],
            'resolution_strategy': 'compatible_update'
        }
        
        # 检查Java版本变化
        old_java = old_requirements.get('java', {}).get('version', '')
        new_java = new_requirements.get('java', {}).get('version', '')
        
        if old_java != new_java:
            changes['java_version_changed'] = True
            
            # 检查是否是破坏性变化
            if not self._is_java_version_compatible(old_java, new_java):
                changes['has_breaking_changes'] = True
                changes['resolution_strategy'] = 'create_isolated_environment'
        
        # 检查Python版本变化
        old_python = old_requirements.get('python', {}).get('version', '')
        new_python = new_requirements.get('python', {}).get('version', '')
        
        if old_python != new_python:
            changes['python_version_changed'] = True
            changes['has_breaking_changes'] = True  # Python版本变化通常需要新虚拟环境
            changes['resolution_strategy'] = 'create_new_venv'
        
        return changes
    
    def _is_java_version_compatible(self, old_version: str, new_version: str) -> bool:
        """检查Java版本兼容性"""
        try:
            old_major = int(old_version.split('.')[0]) if '.' in old_version else int(old_version)
            new_major = int(new_version.split('.')[0]) if '.' in new_version else int(new_version)
            
            # Java向下兼容性检查
            compatibility = self.compatibility_rules.get('java_compatibility', {})
            compatible_versions = compatibility.get(str(new_major), [])
            
            return str(old_major) in compatible_versions
        except (ValueError, KeyError):
            return False