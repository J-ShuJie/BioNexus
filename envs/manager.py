"""
环境管理器主控制类
统一管理所有运行时环境，提供高级API接口
"""

import logging
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from .runtime.java_runtime import JavaRuntime
from .runtime.python_runtime import PythonRuntime
from .resolver.dependency_resolver import DependencyResolver
from .installer.download_engine import DownloadEngine
from utils.path_resolver import get_path_resolver


class EnvironmentManager:
    """
    环境管理器主类
    
    提供统一的环境管理接口，支持：
    - 自动环境检测和安装
    - 智能依赖冲突解析
    - 版本管理和更新
    - 环境隔离策略
    """
    
    def __init__(self, base_path: Optional[Path] = None):
        """
        初始化环境管理器

        Args:
            base_path: 环境安装基础路径，默认从配置读取或使用envs_cache
        """
        self.logger = logging.getLogger(__name__)

        # 设置基础路径 - 从配置读取
        if base_path is None:
            path_resolver = get_path_resolver()
            base_path = path_resolver.get_env_cache_dir()
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # 初始化运行时管理器
        self.java_runtime = JavaRuntime(self.base_path / "java")
        self.python_runtime = PythonRuntime(self.base_path / "python") 
        
        # 初始化依赖解析器和下载引擎
        self.dependency_resolver = DependencyResolver()
        self.download_engine = DownloadEngine()
        
        # 环境状态缓存
        self._environment_cache = {}
        
        self.logger.info(f"环境管理器初始化完成，基础路径: {self.base_path}")
    
    def check_tool_environment(self, tool_name: str, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """
        检查工具的环境需求并返回状态
        
        Args:
            tool_name: 工具名称
            requirements: 环境需求字典
            
        Returns:
            环境状态字典，包含缺失的环境和建议的安装策略
        """
        self.logger.info(f"检查工具环境: {tool_name}")
        
        environment_status = {
            'tool_name': tool_name,
            'satisfied': True,
            'missing_requirements': [],
            'available_environments': [],
            'recommended_actions': []
        }
        
        # 检查Java环境需求
        if 'java' in requirements:
            java_req = requirements['java']
            java_status = self.java_runtime.check_requirements(java_req)
            
            if not java_status['satisfied']:
                environment_status['satisfied'] = False
                environment_status['missing_requirements'].append({
                    'type': 'java',
                    'requirement': java_req,
                    'status': java_status
                })
                
                # 生成安装建议
                environment_status['recommended_actions'].append({
                    'action': 'install_java',
                    'description': f"自动安装Java {java_req.get('version', '11+')}",
                    'estimated_size': '45 MB',
                    'estimated_time': '2-3 分钟'
                })
            else:
                environment_status['available_environments'].append({
                    'type': 'java',
                    'version': java_status['available_version'],
                    'path': java_status['java_home']
                })
        
        # 检查Python环境需求
        if 'python' in requirements:
            python_req = requirements['python']
            python_status = self.python_runtime.check_requirements(python_req)
            
            if not python_status['satisfied']:
                environment_status['satisfied'] = False
                environment_status['missing_requirements'].append({
                    'type': 'python',
                    'requirement': python_req,
                    'status': python_status
                })
                
                environment_status['recommended_actions'].append({
                    'action': 'install_python',
                    'description': f"创建Python {python_req.get('version', '3.10+')} 虚拟环境",
                    'estimated_size': '15 MB',
                    'estimated_time': '1-2 分钟'
                })
        
        return environment_status
    
    def install_environment(self, tool_name: str, requirements: Dict[str, Any], 
                          progress_callback: Optional[callable] = None) -> Dict[str, Any]:
        """
        为工具安装所需的环境
        
        Args:
            tool_name: 工具名称
            requirements: 环境需求
            progress_callback: 进度回调函数 (status: str, percent: int)
            
        Returns:
            安装结果字典
        """
        self.logger.info(f"开始安装环境: {tool_name}")
        
        result = {
            'success': True,
            'installed_environments': [],
            'errors': []
        }
        
        try:
            # 解析依赖关系
            if progress_callback:
                progress_callback("解析环境依赖...", 5)
            
            dependency_plan = self.dependency_resolver.resolve_dependencies(
                tool_name, requirements
            )
            
            # 执行安装计划
            total_steps = len(dependency_plan.installation_steps)
            
            for i, step in enumerate(dependency_plan.installation_steps):
                step_progress = int((i / total_steps) * 90) + 10
                
                if progress_callback:
                    progress_callback(f"安装 {step['name']}...", step_progress)
                
                step_result = self._execute_installation_step(step, progress_callback)
                
                if step_result['success']:
                    result['installed_environments'].append(step_result)
                else:
                    result['success'] = False
                    result['errors'].append(step_result['error'])
                    break
            
            if progress_callback and result['success']:
                progress_callback("环境安装完成", 100)
                
        except Exception as e:
            self.logger.error(f"环境安装失败: {e}")
            result['success'] = False
            result['errors'].append(str(e))
            if progress_callback:
                progress_callback(f"安装失败: {str(e)}", -1)
        
        return result
    
    def _execute_installation_step(self, step: Dict[str, Any], 
                                 progress_callback: Optional[callable] = None) -> Dict[str, Any]:
        """执行单个安装步骤"""
        step_type = step['type']
        
        if step_type == 'java':
            return self.java_runtime.install_java(step['version'], progress_callback)
        elif step_type == 'python':
            return self.python_runtime.install_python_env(step['version'], step.get('packages', []), progress_callback)
        else:
            return {
                'success': False,
                'error': f"不支持的环境类型: {step_type}"
            }
    
    def get_environment_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """获取工具的环境信息"""
        # 从缓存中获取或重新检测
        if tool_name in self._environment_cache:
            return self._environment_cache[tool_name]
        
        # TODO: 从工具配置中读取环境信息
        return None
    
    def check_environment_updates(self) -> Dict[str, Any]:
        """
        检查环境更新
        
        Returns:
            环境更新信息字典
        """
        updates = {}
        
        # 检查Java更新
        java_updates = self.java_runtime.check_updates()
        if java_updates:
            updates['java'] = java_updates
        
        # 检查Python包更新  
        python_updates = self.python_runtime.check_package_updates()
        if python_updates:
            updates['python_packages'] = python_updates
        
        return updates
    
    def handle_software_update_dependencies(self, tool_name: str, old_version: str, 
                                          new_version: str) -> Dict[str, Any]:
        """
        处理软件更新时的环境依赖变化
        
        Args:
            tool_name: 工具名称
            old_version: 旧版本
            new_version: 新版本
            
        Returns:
            处理结果和建议
        """
        # TODO: 实现依赖变化分析和处理逻辑
        # 这是软件更新时环境管理的核心逻辑
        
        return {
            'needs_environment_update': False,
            'changes': [],
            'user_notification_needed': False,
            'automatic_resolution': True
        }
    
    def cleanup_unused_environments(self) -> Dict[str, Any]:
        """清理未使用的环境"""
        cleanup_result = {
            'cleaned_size_mb': 0,
            'cleaned_environments': [],
            'errors': []
        }
        
        try:
            # 清理Java环境
            java_cleanup = self.java_runtime.cleanup_unused()
            cleanup_result['cleaned_size_mb'] += java_cleanup.get('size_mb', 0)
            cleanup_result['cleaned_environments'].extend(java_cleanup.get('environments', []))
            
            # 清理Python环境
            python_cleanup = self.python_runtime.cleanup_unused()
            cleanup_result['cleaned_size_mb'] += python_cleanup.get('size_mb', 0)
            cleanup_result['cleaned_environments'].extend(python_cleanup.get('environments', []))
            
        except Exception as e:
            cleanup_result['errors'].append(str(e))
        
        return cleanup_result