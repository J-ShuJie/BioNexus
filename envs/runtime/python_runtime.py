"""
Python运行时环境管理器
自动管理Python虚拟环境和包依赖

支持特性：
- 多版本Python虚拟环境
- 自动包依赖管理
- 环境隔离
- 智能包更新检查
"""

import os
import json
import logging
import subprocess
import venv
from pathlib import Path
from typing import Dict, List, Optional, Any


class PythonRuntime:
    """Python运行时环境管理器"""
    
    def __init__(self, base_path: Path):
        """
        初始化Python运行时管理器
        
        Args:
            base_path: Python环境安装基础路径
        """
        self.logger = logging.getLogger(__name__)
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # 虚拟环境目录
        self.venvs_dir = self.base_path / 'venvs'
        self.venvs_dir.mkdir(exist_ok=True)
        
        self.logger.info(f"Python运行时管理器初始化: {self.base_path}")
    
    def check_requirements(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """
        检查Python环境需求
        
        Args:
            requirements: Python需求，如 {'version': '3.10+', 'packages': ['numpy', 'pandas']}
            
        Returns:
            检查结果字典
        """
        required_version = requirements.get('version', '3.8+')
        required_packages = requirements.get('packages', [])
        
        # 检查系统Python
        system_python = self._check_system_python()
        
        # 检查管理的虚拟环境
        managed_envs = self._check_managed_environments()
        
        # 查找满足需求的环境
        suitable_env = None
        
        # 首先检查管理的虚拟环境
        for env_info in managed_envs:
            if self._python_version_satisfies(env_info['python_version'], required_version):
                if self._packages_satisfied(env_info['packages'], required_packages):
                    suitable_env = env_info
                    break
        
        # 如果没有合适的虚拟环境，检查系统Python
        if not suitable_env and system_python:
            if self._python_version_satisfies(system_python['version'], required_version):
                suitable_env = {
                    'python_version': system_python['version'],
                    'python_path': system_python['python_path'],
                    'env_path': None,  # 系统Python没有虚拟环境
                    'packages': [],  # 系统包不做检查
                    'source': 'system'
                }
        
        if suitable_env:
            return {
                'satisfied': True,
                'python_version': suitable_env['python_version'],
                'python_path': suitable_env['python_path'],
                'env_path': suitable_env.get('env_path'),
                'source': suitable_env.get('source', 'managed')
            }
        else:
            return {
                'satisfied': False,
                'required_version': required_version,
                'required_packages': required_packages,
                'available_versions': [env['python_version'] for env in managed_envs],
                'recommended_action': 'create_venv'
            }
    
    def _check_system_python(self) -> Optional[Dict[str, Any]]:
        """检查系统Python"""
        try:
            result = subprocess.run(['python', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                version_str = result.stdout.strip()
                version = version_str.replace('Python ', '')
                
                # 获取Python路径
                python_path_result = subprocess.run(['python', '-c', 'import sys; print(sys.executable)'],
                                                  capture_output=True, text=True, timeout=5)
                
                python_path = python_path_result.stdout.strip() if python_path_result.returncode == 0 else 'python'
                
                return {
                    'version': version,
                    'python_path': python_path
                }
        except (subprocess.TimeoutExpired, FileNotFoundError):
            # 尝试python3
            try:
                result = subprocess.run(['python3', '--version'],
                                      capture_output=True, text=True, timeout=5)
                
                if result.returncode == 0:
                    version_str = result.stdout.strip()
                    version = version_str.replace('Python ', '')
                    
                    python_path_result = subprocess.run(['python3', '-c', 'import sys; print(sys.executable)'],
                                                      capture_output=True, text=True, timeout=5)
                    
                    python_path = python_path_result.stdout.strip() if python_path_result.returncode == 0 else 'python3'
                    
                    return {
                        'version': version,
                        'python_path': python_path
                    }
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
        
        return None
    
    def _check_managed_environments(self) -> List[Dict[str, Any]]:
        """检查管理的Python虚拟环境"""
        managed_envs = []
        
        if not self.venvs_dir.exists():
            return managed_envs
        
        for env_dir in self.venvs_dir.iterdir():
            if env_dir.is_dir():
                env_info = self._get_venv_info(env_dir)
                if env_info:
                    managed_envs.append(env_info)
        
        return managed_envs
    
    def _get_venv_info(self, env_path: Path) -> Optional[Dict[str, Any]]:
        """获取虚拟环境信息"""
        try:
            # 查找Python可执行文件
            if os.name == 'nt':  # Windows
                python_exe = env_path / 'Scripts' / 'python.exe'
            else:  # Linux/macOS
                python_exe = env_path / 'bin' / 'python'
            
            if not python_exe.exists():
                return None
            
            # 获取Python版本
            result = subprocess.run([str(python_exe), '--version'],
                                  capture_output=True, text=True, timeout=5)
            
            if result.returncode != 0:
                return None
            
            version = result.stdout.strip().replace('Python ', '')
            
            # 获取已安装的包列表
            packages = self._get_installed_packages(python_exe)
            
            return {
                'env_name': env_path.name,
                'env_path': str(env_path),
                'python_version': version,
                'python_path': str(python_exe),
                'packages': packages,
                'source': 'managed'
            }
            
        except (subprocess.TimeoutExpired, Exception):
            return None
    
    def _get_installed_packages(self, python_exe: Path) -> List[Dict[str, str]]:
        """获取已安装的包列表"""
        try:
            result = subprocess.run([str(python_exe), '-m', 'pip', 'list', '--format=json'],
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                packages_data = json.loads(result.stdout)
                return [{'name': pkg['name'], 'version': pkg['version']} for pkg in packages_data]
        except (subprocess.TimeoutExpired, json.JSONDecodeError, Exception):
            pass
        
        return []
    
    def _python_version_satisfies(self, available_version: str, requirement: str) -> bool:
        """检查Python版本是否满足需求"""
        try:
            # 解析版本号
            available_parts = [int(x) for x in available_version.split('.')]
            
            if '+' in requirement:
                # "3.8+" 表示3.8或更高版本
                required_version = requirement.replace('+', '')
                required_parts = [int(x) for x in required_version.split('.')]
                
                # 比较主版本和次版本
                if len(available_parts) >= 2 and len(required_parts) >= 2:
                    if available_parts[0] > required_parts[0]:
                        return True
                    elif available_parts[0] == required_parts[0]:
                        return available_parts[1] >= required_parts[1]
            else:
                # 精确版本匹配
                required_parts = [int(x) for x in requirement.split('.')]
                return available_parts[:len(required_parts)] == required_parts
                
        except (ValueError, IndexError):
            return False
        
        return False
    
    def _packages_satisfied(self, installed_packages: List[Dict[str, str]], 
                          required_packages: List[str]) -> bool:
        """检查包依赖是否满足"""
        if not required_packages:
            return True
        
        installed_names = {pkg['name'].lower() for pkg in installed_packages}
        
        for required_pkg in required_packages:
            # 简化版本需求解析，只检查包名
            pkg_name = required_pkg.split('>=')[0].split('==')[0].split('<')[0].strip().lower()
            if pkg_name not in installed_names:
                return False
        
        return True
    
    def install_python_env(self, version: str, packages: List[str] = None, 
                         progress_callback: Optional[callable] = None) -> Dict[str, Any]:
        """
        安装Python虚拟环境
        
        Args:
            version: Python版本要求
            packages: 要安装的包列表
            progress_callback: 进度回调
            
        Returns:
            安装结果
        """
        if packages is None:
            packages = []
        
        self.logger.info(f"创建Python虚拟环境: {version}, 包: {packages}")
        
        try:
            # 检查系统Python是否满足版本要求
            system_python = self._check_system_python()
            if not system_python or not self._python_version_satisfies(system_python['version'], version):
                return {
                    'success': False,
                    'error': f'系统Python版本不满足要求: {version}'
                }
            
            # 创建虚拟环境名称
            env_name = f"python-{version.replace('+', '')}-{hash(tuple(sorted(packages))) % 10000}"
            env_path = self.venvs_dir / env_name
            
            if progress_callback:
                progress_callback(f"创建虚拟环境 {env_name}...", 10)
            
            # 创建虚拟环境
            if env_path.exists():
                import shutil
                shutil.rmtree(env_path)
            
            venv.create(env_path, with_pip=True)
            
            if progress_callback:
                progress_callback("安装Python包...", 30)
            
            # 安装包
            if packages:
                result = self._install_packages_in_venv(env_path, packages, progress_callback)
                if not result['success']:
                    return result
            
            if progress_callback:
                progress_callback("Python环境创建完成", 100)
            
            return {
                'success': True,
                'env_name': env_name,
                'env_path': str(env_path),
                'python_version': system_python['version']
            }
            
        except Exception as e:
            self.logger.error(f"Python环境安装失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _install_packages_in_venv(self, env_path: Path, packages: List[str], 
                                progress_callback: Optional[callable] = None) -> Dict[str, Any]:
        """在虚拟环境中安装包"""
        try:
            # 获取pip路径
            if os.name == 'nt':  # Windows
                pip_exe = env_path / 'Scripts' / 'pip.exe'
            else:  # Linux/macOS
                pip_exe = env_path / 'bin' / 'pip'
            
            if not pip_exe.exists():
                return {
                    'success': False,
                    'error': '虚拟环境中未找到pip'
                }
            
            # 升级pip
            subprocess.run([str(pip_exe), 'install', '--upgrade', 'pip'], 
                         check=True, capture_output=True, timeout=60)
            
            # 安装包
            for i, package in enumerate(packages):
                if progress_callback:
                    percent = 30 + int((i / len(packages)) * 60)
                    progress_callback(f"安装 {package}...", percent)
                
                result = subprocess.run([str(pip_exe), 'install', package],
                                      capture_output=True, text=True, timeout=300)
                
                if result.returncode != 0:
                    self.logger.warning(f"包安装失败 {package}: {result.stderr}")
                    # 继续安装其他包，不中断整个过程
            
            return {'success': True}
            
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            return {
                'success': False,
                'error': f'包安装失败: {str(e)}'
            }
    
    def check_package_updates(self) -> Dict[str, Any]:
        """检查Python包更新"""
        # TODO: 实现包更新检查逻辑
        return {}
    
    def cleanup_unused(self) -> Dict[str, Any]:
        """清理未使用的Python环境"""
        # TODO: 实现Python环境清理逻辑
        return {
            'size_mb': 0,
            'environments': []
        }