"""
Java运行时环境管理器
自动下载、安装、配置Java运行环境

支持特性：
- 多版本Java并存 
- 自动选择最佳版本
- 便携式安装，不污染系统
- 智能版本检测和更新
"""

import os
import json
import shutil
import logging
import platform
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError


class JavaRuntime:
    """Java运行时环境管理器"""
    
    def __init__(self, base_path: Path):
        """
        初始化Java运行时管理器
        
        Args:
            base_path: Java环境安装基础路径
        """
        self.logger = logging.getLogger(__name__)
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # 平台信息
        self.platform_info = self._detect_platform()
        
        # Java版本配置
        self.java_versions_config = self._load_java_versions_config()
        
        # 缓存已安装的Java版本信息
        self._installed_versions = None
        
        self.logger.info(f"Java运行时管理器初始化: {self.base_path}")
    
    def _detect_platform(self) -> Dict[str, str]:
        """
        检测当前平台信息
        ❗ BioNexus专为Windows设计，强制返回Windows平台信息
        """
        # 获取实际系统信息用于调试
        actual_system = platform.system().lower()
        actual_machine = platform.machine().lower()
        
        # 记录实际平台信息
        self.logger.info(f"BioNexus平台检测 - 实际系统: {actual_system}, 架构: {actual_machine}")
        
        # BioNexus是Windows专用软件，强制返回Windows平台信息
        arch_mapping = {
            'x86_64': 'x64',
            'amd64': 'x64', 
            'aarch64': 'aarch64',
            'arm64': 'aarch64'
        }
        
        # 强制设置为Windows平台
        forced_platform = {
            'os': 'windows',  # 强制Windows
            'arch': arch_mapping.get(actual_machine, 'x64'),  # 默认x64
            'system': 'windows'  # 强制Windows
        }
        
        self.logger.info(f"BioNexus平台检测 - 强制使用Windows平台: {forced_platform}")
        return forced_platform
    
    def _load_java_versions_config(self) -> Dict[str, Any]:
        """加载Java版本配置"""
        # 内置Java版本配置，支持主流LTS版本
        return {
            "supported_versions": [
                {
                    "version": "8",
                    "lts": True,
                    "eol": "2030-12",
                    "recommended": False,
                    "download_sources": [
                        {
                            "provider": "eclipse-temurin",
                            "url_template": "https://github.com/adoptium/temurin8-binaries/releases/download/jdk8u{update}-b{build}/OpenJDK8U-jre_{arch}_{os}_hotspot_8u{update}b{build}.{ext}",
                            "latest_info_url": "https://api.github.com/repos/adoptium/temurin8-binaries/releases/latest",
                            "priority": 1
                        }
                    ]
                },
                {
                    "version": "11", 
                    "lts": True,
                    "eol": "2032-09",
                    "recommended": True,
                    "download_sources": [
                        {
                            "provider": "eclipse-temurin",
                            "url_template": "https://github.com/adoptium/temurin11-binaries/releases/download/jdk-11.0.{patch}+{build}/OpenJDK11U-jre_{arch}_{os}_hotspot_11.0.{patch}_{build}.{ext}",
                            "latest_info_url": "https://api.github.com/repos/adoptium/temurin11-binaries/releases/latest",
                            "priority": 1
                        }
                    ]
                },
                {
                    "version": "17",
                    "lts": True, 
                    "eol": "2029-09",
                    "recommended": False,
                    "download_sources": [
                        {
                            "provider": "eclipse-temurin",
                            "url_template": "https://github.com/adoptium/temurin17-binaries/releases/download/jdk-17.0.{patch}+{build}/OpenJDK17U-jre_{arch}_{os}_hotspot_17.0.{patch}_{build}.{ext}",
                            "latest_info_url": "https://api.github.com/repos/adoptium/temurin17-binaries/releases/latest",
                            "priority": 1
                        }
                    ]
                }
            ]
        }
    
    def check_requirements(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """
        检查Java环境需求
        
        Args:
            requirements: Java需求，如 {'version': '8+', 'provider': 'openjdk'}
            
        Returns:
            检查结果字典
        """
        required_version = requirements.get('version', '11+')
        
        # 解析版本需求
        version_spec = self._parse_version_requirement(required_version)
        
        # 检查系统已安装的Java
        system_java = self._check_system_java()
        
        # 检查BioNexus管理的Java
        managed_java = self._check_managed_java()
        
        # 找到满足需求的Java版本
        suitable_java = None
        
        # 优先使用BioNexus管理的Java（更可控）
        for java_info in managed_java:
            if self._version_satisfies(java_info['version'], version_spec):
                suitable_java = java_info
                break
        
        # 如果没有，检查系统Java
        if not suitable_java and system_java:
            if self._version_satisfies(system_java['version'], version_spec):
                suitable_java = system_java
        
        if suitable_java:
            return {
                'satisfied': True,
                'available_version': suitable_java['version'],
                'java_home': suitable_java['java_home'],
                'source': suitable_java['source']
            }
        else:
            return {
                'satisfied': False,
                'required_version': required_version,
                'available_versions': [j['version'] for j in system_java + managed_java] if system_java or managed_java else [],
                'recommended_version': self._get_recommended_version_for_requirement(version_spec)
            }
    
    def _parse_version_requirement(self, requirement: str) -> Dict[str, Any]:
        """解析版本需求字符串"""
        if '+' in requirement:
            # "8+" 表示8或更高版本
            min_version = requirement.replace('+', '')
            return {'type': 'min', 'version': min_version}
        elif '..' in requirement:
            # "8..11" 表示8到11之间
            min_ver, max_ver = requirement.split('..')
            return {'type': 'range', 'min_version': min_ver, 'max_version': max_ver}
        else:
            # "11" 表示精确版本
            return {'type': 'exact', 'version': requirement}
    
    def _version_satisfies(self, available_version: str, requirement: Dict[str, Any]) -> bool:
        """检查版本是否满足需求"""
        try:
            # 提取主版本号
            available_major = int(available_version.split('.')[0])
            
            if requirement['type'] == 'exact':
                required_major = int(requirement['version'])
                return available_major == required_major
            elif requirement['type'] == 'min':
                required_major = int(requirement['version'])
                return available_major >= required_major
            elif requirement['type'] == 'range':
                min_major = int(requirement['min_version'])
                max_major = int(requirement['max_version'])
                return min_major <= available_major <= max_major
        except ValueError:
            return False
        
        return False
    
    def _check_system_java(self) -> Optional[Dict[str, Any]]:
        """检查系统安装的Java"""
        try:
            # 尝试java -version命令
            result = subprocess.run(['java', '-version'], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                # 解析版本信息
                version_output = result.stderr
                version = self._extract_java_version(version_output)
                
                if version:
                    # 获取JAVA_HOME
                    java_home = os.environ.get('JAVA_HOME')
                    if not java_home:
                        # 尝试通过java.home系统属性获取
                        try:
                            java_home_result = subprocess.run([
                                'java', '-XshowSettings:properties', '-version'
                            ], capture_output=True, text=True, timeout=5)
                            
                            for line in java_home_result.stderr.split('\n'):
                                if 'java.home' in line:
                                    java_home = line.split('=')[1].strip()
                                    break
                        except:
                            pass
                    
                    return {
                        'version': version,
                        'java_home': java_home,
                        'source': 'system'
                    }
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            pass
        
        return None
    
    def _check_managed_java(self) -> List[Dict[str, Any]]:
        """检查BioNexus管理的Java版本"""
        managed_javas = []
        
        if not self.base_path.exists():
            return managed_javas
        
        # 扫描安装目录
        for version_dir in self.base_path.iterdir():
            if version_dir.is_dir() and version_dir.name.startswith('java-'):
                java_home = version_dir
                
                # 验证Java安装
                if self._verify_java_installation(java_home):
                    version = self._get_installed_java_version(java_home)
                    if version:
                        managed_javas.append({
                            'version': version,
                            'java_home': str(java_home),
                            'source': 'managed'
                        })
        
        return managed_javas
    
    def _extract_java_version(self, version_output: str) -> Optional[str]:
        """从java -version输出中提取版本号"""
        try:
            lines = version_output.split('\n')
            first_line = lines[0]
            
            # 处理不同格式的版本输出
            if 'version' in first_line:
                # 提取引号中的版本号
                start = first_line.find('"') + 1
                end = first_line.find('"', start)
                version_str = first_line[start:end]
                
                # 处理1.8.0_xxx格式和11.0.xx格式
                if version_str.startswith('1.'):
                    # 1.8.0_xx -> 8
                    return version_str.split('.')[1]
                else:
                    # 11.0.xx -> 11.0.xx
                    return version_str
        except (IndexError, ValueError):
            pass
        
        return None
    
    def _verify_java_installation(self, java_home: Path) -> bool:
        """验证Java安装是否有效"""
        java_exe = java_home / 'bin' / ('java.exe' if self.platform_info['os'] == 'windows' else 'java')
        return java_exe.exists() and java_exe.is_file()
    
    def _get_installed_java_version(self, java_home: Path) -> Optional[str]:
        """获取已安装Java的版本"""
        java_exe = java_home / 'bin' / ('java.exe' if self.platform_info['os'] == 'windows' else 'java')
        
        try:
            result = subprocess.run([str(java_exe), '-version'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return self._extract_java_version(result.stderr)
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        return None
    
    def _get_recommended_version_for_requirement(self, requirement: Dict[str, Any]) -> str:
        """根据需求获取推荐的Java版本"""
        # 默认推荐Java 11（当前主流LTS版本）
        if requirement['type'] == 'min':
            required_version = int(requirement['version'])
            if required_version <= 8:
                return '11'  # 推荐升级到11
            elif required_version <= 11:
                return '11'
            else:
                return '17'  # 对于更高需求推荐17
        elif requirement['type'] == 'exact':
            return requirement['version']
        else:
            return '11'  # 默认推荐11
    
    def install_java(self, version: str, progress_callback: Optional[callable] = None) -> Dict[str, Any]:
        """
        安装指定版本的Java
        
        Args:
            version: Java版本
            progress_callback: 进度回调
            
        Returns:
            安装结果
        """
        self.logger.info(f"🚀 开始安装Java {version}")
        self.logger.info(f"📍 平台信息: {self.platform_info}")
        
        try:
            # 查找版本配置
            version_config = self._find_version_config(version)
            if not version_config:
                error_msg = f"不支持的Java版本: {version}"
                self.logger.error(f"❌ {error_msg}")
                return {
                    'success': False,
                    'error': error_msg
                }
            
            self.logger.info(f"✅ 找到版本配置: Java {version_config['version']} (LTS: {version_config['lts']})")
            
            # 获取最新的下载信息
            if progress_callback:
                progress_callback("获取下载信息...", 5)
            
            download_info = self._get_latest_download_info(version_config)
            if not download_info:
                return {
                    'success': False, 
                    'error': f"无法获取Java {version}的下载信息"
                }
            
            # 下载Java
            if progress_callback:
                progress_callback("下载Java运行环境...", 10)
            
            download_result = self._download_java(download_info, progress_callback)
            if not download_result['success']:
                return download_result
            
            # 安装Java
            if progress_callback:
                progress_callback("安装Java运行环境...", 80)
            
            install_result = self._install_java_archive(
                download_result['file_path'], version, progress_callback
            )
            
            if install_result['success']:
                if progress_callback:
                    progress_callback("Java安装完成", 100)
            
            return install_result
            
        except Exception as e:
            self.logger.error(f"Java安装失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _find_version_config(self, version: str) -> Optional[Dict[str, Any]]:
        """查找版本配置"""
        for version_config in self.java_versions_config['supported_versions']:
            if version_config['version'] == version:
                return version_config
        return None
    
    def _get_latest_download_info(self, version_config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """获取最新的下载信息，使用GitHub API和URL模板系统"""
        self.logger.info(f"🔍 获取Java {version_config['version']}最新下载信息...")
        
        try:
            download_sources = version_config.get('download_sources', [])
            if not download_sources:
                self.logger.error(f"❌ Java {version_config['version']} 没有配置下载源")
                return None
            
            # 使用第一个下载源 (Eclipse Temurin)
            source = download_sources[0]
            api_url = source['latest_info_url']
            
            self.logger.info(f"📡 调用GitHub API: {api_url}")
            
            # 调用GitHub API获取最新版本
            import json
            from urllib.request import urlopen, Request
            from urllib.error import URLError, HTTPError
            
            headers = {
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': 'BioNexus-JavaInstaller/1.1.12'
            }
            
            request = Request(api_url, headers=headers)
            
            with urlopen(request, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
                
                tag_name = data.get('tag_name', '')
                self.logger.info(f"📦 获取到最新版本标签: {tag_name}")
                
                # 解析版本信息
                version_info = self._parse_version_tag(tag_name, version_config['version'])
                if not version_info:
                    self.logger.error(f"❌ 无法解析版本标签: {tag_name}")
                    return None
                
                # 构建下载URL
                platform_info = self.platform_info
                file_ext = 'zip' if platform_info['os'] == 'windows' else 'tar.gz'
                
                url_template = source['url_template']
                download_url = url_template.format(
                    arch=platform_info['arch'],
                    os=platform_info['os'], 
                    ext=file_ext,
                    **version_info
                )
                
                self.logger.info(f"🔗 构建的下载URL: {download_url}")
                
                # 验证URL可用性
                self.logger.info("🧪 验证下载URL可用性...")
                test_request = Request(download_url, headers=headers)
                test_request.get_method = lambda: 'HEAD'
                
                try:
                    with urlopen(test_request, timeout=5) as test_response:
                        content_length = test_response.headers.get('Content-Length', '0')
                        size_mb = int(content_length) / 1024 / 1024 if content_length.isdigit() else 45
                        
                        self.logger.info(f"✅ 下载URL验证成功，文件大小: {size_mb:.1f}MB")
                        
                        return {
                            'version': tag_name,
                            'download_url': download_url,
                            'file_name': f"openjdk-{version_config['version']}-jre-{platform_info['os']}-{platform_info['arch']}.{file_ext}",
                            'estimated_size': int(size_mb * 1024 * 1024)
                        }
                        
                except HTTPError as e:
                    self.logger.error(f"❌ 下载URL验证失败: {e.code} - {e.reason}")
                    self.logger.error(f"   尝试的URL: {download_url}")
                    return None
                
        except Exception as e:
            self.logger.error(f"❌ 获取Java下载信息失败: {e}")
            import traceback
            self.logger.debug(f"详细错误: {traceback.format_exc()}")
            return None
    
    def _parse_version_tag(self, tag_name: str, major_version: str) -> Optional[Dict[str, str]]:
        """解析GitHub版本标签"""
        try:
            if major_version == '11' and tag_name.startswith('jdk-'):
                # 格式: jdk-11.0.28+6
                version_part = tag_name[4:]  # 去掉 'jdk-'
                if '+' in version_part:
                    version, build = version_part.split('+', 1)
                    if '.' in version:
                        parts = version.split('.')
                        if len(parts) >= 3:
                            patch = parts[2]
                            return {
                                'patch': patch,
                                'build': build
                            }
                            
            elif major_version == '8' and 'jdk8u' in tag_name:
                # 格式: jdk8u392-b08
                # 提取 update 和 build
                import re
                match = re.search(r'jdk8u(\d+)-b(\d+)', tag_name)
                if match:
                    update, build = match.groups()
                    return {
                        'update': update,
                        'build': build
                    }
                    
            elif major_version == '17' and tag_name.startswith('jdk-'):
                # 格式: jdk-17.0.12+7
                version_part = tag_name[4:]  # 去掉 'jdk-'
                if '+' in version_part:
                    version, build = version_part.split('+', 1)
                    if '.' in version:
                        parts = version.split('.')
                        if len(parts) >= 3:
                            patch = parts[2]
                            return {
                                'patch': patch,
                                'build': build
                            }
            
            return None
            
        except Exception as e:
            self.logger.error(f"解析版本标签失败: {e}")
            return None
    
    def _download_java(self, download_info: Dict[str, Any], 
                      progress_callback: Optional[callable] = None) -> Dict[str, Any]:
        """下载Java安装包"""
        self.logger.info(f"📥 开始下载Java: {download_info['version']}")
        self.logger.info(f"🔗 下载URL: {download_info['download_url']}")
        self.logger.info(f"📦 文件大小: {download_info['estimated_size'] / 1024 / 1024:.1f}MB")
        
        from ..installer.download_engine import DownloadEngine
        
        download_engine = DownloadEngine()
        download_path = self.base_path / 'downloads' / download_info['file_name']
        download_path.parent.mkdir(exist_ok=True)
        
        self.logger.info(f"💾 下载到: {download_path}")
        
        def download_progress(status, percent):
            if percent >= 0:
                self.logger.debug(f"📈 下载进度: {percent}% - {status}")
            else:
                self.logger.error(f"❌ 下载错误: {status}")
                
            if progress_callback and percent >= 0:
                # 下载占总进度的70% (10% -> 80%)
                total_percent = 10 + int(percent * 0.7)
                progress_callback(status, total_percent)
        
        success = download_engine.download_file(
            download_info['download_url'],
            download_path,
            download_progress
        )
        
        if success:
            return {
                'success': True,
                'file_path': download_path
            }
        else:
            return {
                'success': False,
                'error': '下载Java安装包失败'
            }
    
    def _install_java_archive(self, archive_path: Path, version: str, 
                            progress_callback: Optional[callable] = None) -> Dict[str, Any]:
        """安装Java归档文件"""
        try:
            install_dir = self.base_path / f'java-{version}'
            
            # 清理旧安装
            if install_dir.exists():
                shutil.rmtree(install_dir)
            install_dir.mkdir(parents=True)
            
            # 解压归档
            if progress_callback:
                progress_callback("解压Java安装包...", 85)
            
            if archive_path.suffix == '.zip':
                import zipfile
                with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                    zip_ref.extractall(install_dir)
            else:  # .tar.gz
                import tarfile
                with tarfile.open(archive_path, 'r:gz') as tar_ref:
                    tar_ref.extractall(install_dir)
            
            # 查找实际的Java目录（通常在解压后的子目录中）
            java_dirs = [d for d in install_dir.iterdir() if d.is_dir()]
            if java_dirs:
                actual_java_dir = java_dirs[0]
                # 移动到正确位置
                temp_dir = install_dir.parent / f'temp_java_{version}'
                actual_java_dir.rename(temp_dir)
                shutil.rmtree(install_dir)
                temp_dir.rename(install_dir)
            
            # 验证安装
            if progress_callback:
                progress_callback("验证Java安装...", 95)
            
            if not self._verify_java_installation(install_dir):
                return {
                    'success': False,
                    'error': 'Java安装验证失败'
                }
            
            # 清理下载文件
            try:
                archive_path.unlink()
            except:
                pass
            
            return {
                'success': True,
                'java_home': str(install_dir),
                'version': version
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Java安装失败: {str(e)}'
            }
    
    def check_updates(self) -> Dict[str, Any]:
        """检查Java环境更新"""
        # TODO: 实现Java更新检查逻辑
        return {}
    
    def cleanup_unused(self) -> Dict[str, Any]:
        """清理未使用的Java环境"""
        # TODO: 实现Java环境清理逻辑
        return {
            'size_mb': 0,
            'environments': []
        }