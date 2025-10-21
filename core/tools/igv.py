"""
IGV (Integrative Genomics Viewer) 工具实现
基于FastQC的实现模式，提供完整的安装、配置和启动功能
"""
import os
import shutil
import subprocess
import zipfile
import logging
import json
import threading
import time
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

from .base import ToolInterface
from ..downloader import SmartDownloader
from utils.unified_logger import get_logger
from utils.path_resolver import get_path_resolver


class IGV(ToolInterface):
    """
    IGV (Integrative Genomics Viewer) 工具实现
    强大的基因组数据可视化工具，支持多种格式
    
    特性:
    1. 支持BAM、VCF、BED、GFF等多种格式
    2. 交互式基因组浏览
    3. 多轨道同步显示
    4. 自动管理Java环境
    """
    
    # 缓存的元数据，避免重复网络调用
    _cached_metadata = None
    _cache_timestamp = 0
    _cache_duration = 300  # 5分钟缓存
    
    def __init__(self):
        """初始化IGV工具"""
        self.logger = logging.getLogger(__name__)
        self.unified_logger = get_logger()

        # 安装路径配置 - 从配置读取
        path_resolver = get_path_resolver()
        self.install_base = path_resolver.get_install_dir()
        self.install_dir = self.install_base / "IGV"
        self.temp_dir = Path("temp")
        
        # 可执行文件配置
        if os.name == 'nt':  # Windows
            self.exe_name = "igv.bat"
        else:  # Linux/macOS
            self.exe_name = "igv.sh"
        
        self.exe_path = self.install_dir / self.exe_name
        
        # 下载器
        self.downloader = SmartDownloader()
        
        # 线程池用于异步操作
        self._executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="IGV")
        
        self.unified_logger.log_runtime(f"IGV工具初始化完成: {self.install_dir}")
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        获取IGV元数据
        使用缓存机制，避免频繁网络调用
        """
        current_time = time.time()
        
        # 检查缓存是否有效
        if (self._cached_metadata and 
            current_time - self._cache_timestamp < self._cache_duration):
            return self._cached_metadata
        
        # 构建基础元数据（不依赖网络）
        base_metadata = {
            'name': 'IGV',
            'version': '2.17.4',  # 默认版本，异步更新
            'category': 'visualization',
            'description': '强大的基因组数据可视化工具，支持BAM、VCF、BED等多种格式。可以同时查看序列比对、变异、注释等多层数据。',
            'size': '约 350 MB',
            'requires': ['java>=11'],
            'status': 'installed' if self.verify_installation() else 'available',
            'homepage': 'https://igv.org/',
            'documentation': 'https://igv.org/doc/desktop/',
            'license': 'MIT',
            'published_date': '',
            'release_notes': ''
        }
        
        # 异步更新版本信息（不阻塞返回）
        if current_time - self._cache_timestamp > self._cache_duration:
            self._executor.submit(self._async_update_metadata, base_metadata)
        
        # 更新缓存
        self._cached_metadata = base_metadata
        self._cache_timestamp = current_time
        
        return base_metadata
    
    def _async_update_metadata(self, base_metadata: Dict[str, Any]):
        """异步更新元数据中的版本信息"""
        try:
            import time
            
            # 获取GitHub最新版本
            api_url = "https://api.github.com/repos/igvteam/igv/releases/latest"
            headers = {
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': 'BioNexus-IGV/1.2.12'
            }
            
            start_time = time.time()
            request = Request(api_url, headers=headers)
            
            with urlopen(request, timeout=5) as response:
                data = json.loads(response.read().decode('utf-8'))
                
                duration = time.time() - start_time
                self.unified_logger.log_network(api_url, "GET", response.getcode(), duration)
                
                # 更新缓存的元数据
                version = data.get('tag_name', '').lstrip('v')
                if version:
                    self._cached_metadata['version'] = version
                    self._cached_metadata['published_date'] = data.get('published_at', '')
                    self._cached_metadata['release_notes'] = data.get('body', '')[:200]  # 限制长度
                    
                    self.unified_logger.log_runtime(f"IGV版本信息已异步更新: {version}")
                
        except Exception as e:
            self.unified_logger.log_error("IGV版本更新", f"异步更新失败: {e}")
    
    def get_download_sources(self) -> List[Dict[str, Any]]:
        """
        获取IGV下载源列表
        优先使用官方下载，GitHub作为备用
        """
        version = self._cached_metadata.get('version', '2.17.4') if self._cached_metadata else '2.17.4'
        
        # 从完整版本号中提取主版本号（如 2.17.4 -> 2.17）
        major_version = '.'.join(version.split('.')[:2])
        
        sources = [
            {
                'name': 'IGV官方源',
                'url': f'https://data.broadinstitute.org/igv/projects/downloads/{major_version}/IGV_{version}.zip',
                'priority': 1,
                'location': 'US',
                'timeout': 30,
                'description': 'Broad Institute官方下载源'
            }
        ]
        
        self.unified_logger.log_runtime(f"IGV下载源: {sources[0]['url']}")
        return sources
    
    def check_dependencies(self) -> Dict[str, bool]:
        """
        检查IGV依赖项
        主要检查Java环境（需要Java 11或更高版本）
        """
        dependencies = {}
        
        try:
            # 检查系统Java
            result = subprocess.run(['java', '-version'], 
                                   capture_output=True, 
                                   text=True, 
                                   timeout=5)
            dependencies['java'] = result.returncode == 0
            
            if dependencies['java']:
                version_output = result.stderr
                # 尝试提取Java版本号
                if 'version' in version_output:
                    import re
                    version_match = re.search(r'version "(\d+)', version_output)
                    if version_match:
                        java_major = int(version_match.group(1))
                        dependencies['java_version_ok'] = java_major >= 11
                        self.unified_logger.log_runtime(f"系统Java版本: {java_major} {'✓' if java_major >= 11 else '(需要11+)'}")
                    else:
                        dependencies['java_version_ok'] = False
                else:
                    dependencies['java_version_ok'] = False
            
        except Exception as e:
            # Java不可用，但不影响安装（会自动安装Java）
            dependencies['java'] = False
            dependencies['java_version_ok'] = False
            self.unified_logger.log_runtime(f"系统Java不可用: {e}")
        
        # 检查本地Java环境
        java_cache_path = Path("envs_cache") / "java"
        if java_cache_path.exists():
            java_dirs = [d for d in java_cache_path.iterdir() if d.is_dir() and d.name.startswith('java-')]
            if java_dirs:
                # 优先查找Java 11或更高版本
                suitable_java = None
                for java_dir in java_dirs:
                    if 'java-11' in java_dir.name or 'java-17' in java_dir.name or 'java-21' in java_dir.name:
                        suitable_java = java_dir
                        break
                
                if suitable_java:
                    dependencies['local_java'] = True
                    dependencies['local_java_suitable'] = True
                    self.unified_logger.log_runtime(f"检测到合适的本地Java环境: {suitable_java.name}")
                else:
                    dependencies['local_java'] = True
                    dependencies['local_java_suitable'] = False
                    self.unified_logger.log_runtime(f"本地Java版本可能不兼容: {[d.name for d in java_dirs]}")
            else:
                dependencies['local_java'] = False
                dependencies['local_java_suitable'] = False
        else:
            dependencies['local_java'] = False
            dependencies['local_java_suitable'] = False
        
        return dependencies
    
    def install(self, progress_callback: Optional[Callable[[str, int], None]] = None) -> bool:
        """
        安装IGV
        完整的下载、解压、配置流程
        """
        try:
            # 1. 检查依赖
            if progress_callback:
                progress_callback("检查系统依赖...", 5)
            
            deps = self.check_dependencies()
            self.unified_logger.log_installation('IGV', '依赖检查', '完成', deps)
            
            # 2. 如果Java不合适，尝试自动安装
            if not (deps.get('java_version_ok', False) or deps.get('local_java_suitable', False)):
                if progress_callback:
                    progress_callback("正在安装Java 11环境...", 10)
                
                java_installed = self._auto_install_java(progress_callback)
                if not java_installed:
                    self.unified_logger.log_error('IGV安装', 'Java环境安装失败')
                    if progress_callback:
                        progress_callback("Java环境安装失败，继续尝试安装IGV", 20)
                else:
                    self.unified_logger.log_installation('IGV', 'Java环境', '安装成功')
            
            # 3. 准备目录
            if progress_callback:
                progress_callback("准备安装目录...", 25)
            
            self.install_base.mkdir(exist_ok=True)
            self.temp_dir.mkdir(exist_ok=True)
            
            # 清理旧安装
            if self.install_dir.exists():
                shutil.rmtree(self.install_dir)
                self.unified_logger.log_installation('IGV', '清理旧版本', '完成')
            
            # 4. 下载文件
            if progress_callback:
                progress_callback("开始下载IGV...", 30)
            
            # 获取当前版本
            current_version = self._cached_metadata.get('version', '2.17.4') if self._cached_metadata else '2.17.4'
            zip_path = self.temp_dir / f"IGV_{current_version}.zip"
            
            self.unified_logger.log_installation('IGV', '确定版本', '成功', {
                'target_version': current_version,
                'download_file': str(zip_path)
            })
            
            sources = self.get_download_sources()
            
            # 使用智能下载器
            def download_progress(status, percent):
                if percent >= 0:
                    # 下载占总进度的50% (30% -> 80%)
                    total_percent = 30 + int(percent * 0.5)
                    if progress_callback:
                        progress_callback(status, total_percent)
            
            success = self.downloader.download_with_fallback(
                sources, 
                zip_path, 
                download_progress
            )
            
            if not success:
                self.unified_logger.log_error('IGV安装', '下载失败')
                if progress_callback:
                    progress_callback("下载失败", -1)
                return False
            
            self.unified_logger.log_installation('IGV', '下载', '完成', {
                'file_size': zip_path.stat().st_size if zip_path.exists() else 0
            })
            
            # 5. 解压安装
            if progress_callback:
                progress_callback("正在解压安装包...", 85)
            
            # 使用分层解压策略
            success = self._extract_archive(zip_path, self.install_base)
            if not success:
                self.unified_logger.log_error('IGV解压', "解压失败")
                if progress_callback:
                    progress_callback("解压失败", -1)
                return False
            
            # 处理解压后的目录（IGV通常解压为IGV_版本号目录）
            try:
                extracted_dirs = [d for d in self.install_base.iterdir() 
                                if d.is_dir() and d.name.upper().startswith('IGV')]
                if extracted_dirs:
                    actual_dir = extracted_dirs[0]
                    if actual_dir != self.install_dir:
                        # 如果目标目录已存在，先删除
                        if self.install_dir.exists():
                            shutil.rmtree(self.install_dir)
                        actual_dir.rename(self.install_dir)
                    self.unified_logger.log_installation('IGV', '目录处理', '成功', {
                        'install_dir': str(self.install_dir)
                    })
                else:
                    self.unified_logger.log_error('IGV解压', '未找到解压的IGV目录')
                    if progress_callback:
                        progress_callback("解压目录未找到", -1)
                    return False
            except Exception as e:
                self.unified_logger.log_error('IGV目录处理', f"处理失败: {e}")
                if progress_callback:
                    progress_callback("目录处理失败", -1)
                return False
            
            # 6. 设置权限（Linux/macOS）
            if os.name != 'nt':
                try:
                    # 设置shell脚本为可执行
                    sh_files = list(self.install_dir.glob('*.sh'))
                    for sh_file in sh_files:
                        os.chmod(sh_file, 0o755)
                        self.unified_logger.log_installation('IGV', f'权限设置: {sh_file.name}', '完成')
                except Exception as e:
                    self.unified_logger.log_error('IGV权限', f"设置失败: {e}")
            
            # 7. 创建或修复启动脚本
            self._create_or_fix_launcher()
            
            # 8. 验证安装
            if progress_callback:
                progress_callback("验证安装...", 95)
            
            if not self.verify_installation():
                self.unified_logger.log_error('IGV安装', '验证失败')
                if progress_callback:
                    progress_callback("安装验证失败", -1)
                return False
            
            # 9. 清理临时文件
            try:
                zip_path.unlink()
                self.unified_logger.log_installation('IGV', '清理临时文件', '完成')
            except:
                pass
            
            if progress_callback:
                progress_callback("IGV安装完成", 100)
            
            self.unified_logger.log_installation('IGV', '安装完成', '成功', {
                'install_path': str(self.install_dir),
                'executable': str(self.exe_path)
            })
            return True
            
        except Exception as e:
            error_msg = f"IGV安装失败: {e}"
            self.unified_logger.log_error('IGV安装', error_msg)
            if progress_callback:
                progress_callback(error_msg, -1)
            return False
    
    def verify_installation(self) -> bool:
        """
        验证IGV是否已安装
        检查关键文件和目录
        """
        self.unified_logger.log_runtime(f"开始验证IGV安装: {self.install_dir}")
        
        # 1. 检查安装目录是否存在
        if not self.install_dir.exists():
            self.unified_logger.log_runtime(f"IGV验证失败: 安装目录不存在 - {self.install_dir}")
            return False
        
        self.unified_logger.log_runtime(f"✓ 安装目录存在: {self.install_dir}")
        
        # 2. 检查可执行文件
        launcher_exists = False
        if os.name == 'nt':
            # Windows: 检查批处理文件
            bat_files = ['igv.bat', 'igv_hidpi.bat']
            for bat_file in bat_files:
                if (self.install_dir / bat_file).exists():
                    launcher_exists = True
                    self.unified_logger.log_runtime(f"✓ 找到启动脚本: {bat_file}")
                    break
        else:
            # Linux/macOS: 检查shell脚本
            sh_files = ['igv.sh', 'igv_hidpi.sh', 'igv.command']
            for sh_file in sh_files:
                if (self.install_dir / sh_file).exists():
                    launcher_exists = True
                    self.unified_logger.log_runtime(f"✓ 找到启动脚本: {sh_file}")
                    break
        
        if not launcher_exists:
            self.unified_logger.log_runtime("IGV验证失败: 未找到启动脚本")
            return False
        
        # 3. 检查IGV的JAR文件
        lib_dir = self.install_dir / 'lib'
        if lib_dir.exists():
            jar_files = list(lib_dir.glob('igv*.jar'))
            if jar_files:
                self.unified_logger.log_runtime(f"✓ 找到IGV JAR文件: {len(jar_files)}个")
            else:
                # 旧版本IGV可能直接在根目录
                jar_files = list(self.install_dir.glob('igv*.jar'))
                if jar_files:
                    self.unified_logger.log_runtime(f"✓ 找到IGV JAR文件（根目录）: {len(jar_files)}个")
                else:
                    self.unified_logger.log_runtime("IGV验证失败: 未找到IGV JAR文件")
                    return False
        else:
            # 检查根目录
            jar_files = list(self.install_dir.glob('igv*.jar'))
            if jar_files:
                self.unified_logger.log_runtime(f"✓ 找到IGV JAR文件: {len(jar_files)}个")
            else:
                self.unified_logger.log_runtime("IGV验证失败: 未找到lib目录或IGV JAR文件")
                return False
        
        # 4. 验证通过
        self.unified_logger.log_runtime("✅ IGV安装验证通过")
        return True
    
    def launch(self, args: Optional[List[str]] = None) -> bool:
        """
        启动IGV
        使用隔离的Java环境
        """
        if not self.verify_installation():
            self.unified_logger.log_error('IGV启动', 'IGV未安装')
            return False
        
        try:
            # 查找实际的启动脚本
            if os.name == 'nt':
                # Windows: 优先使用igv.bat
                launcher_candidates = ['igv.bat', 'igv_hidpi.bat']
            else:
                # Linux/macOS: 优先使用igv.sh
                launcher_candidates = ['igv.sh', 'igv_hidpi.sh', 'igv.command']
            
            actual_launcher = None
            for launcher in launcher_candidates:
                launcher_path = self.install_dir / launcher
                if launcher_path.exists():
                    actual_launcher = launcher_path
                    break
            
            if not actual_launcher:
                self.unified_logger.log_error('IGV启动', '未找到启动脚本')
                return False
            
            self.unified_logger.log_runtime(f"使用启动脚本: {actual_launcher}")
            
            # 获取隔离的Java环境
            env = self._get_isolated_java_env()
            
            # 构建启动命令
            if os.name == 'nt':
                # Windows: 使用批处理文件
                cmd_str = f'"{actual_launcher.name}"'
                if args:
                    cmd_str += ' ' + ' '.join(f'"{arg}"' for arg in args)
                
                self.unified_logger.log_runtime(f"Windows启动命令: {cmd_str}")
                
                process = subprocess.Popen(
                    cmd_str,
                    shell=True,
                    env=env,
                    cwd=str(self.install_dir)
                )
            else:
                # Linux/macOS: 使用shell脚本
                cmd_list = [str(actual_launcher)]
                if args:
                    cmd_list.extend(args)
                
                self.unified_logger.log_runtime(f"Unix启动命令: {' '.join(cmd_list)}")
                
                process = subprocess.Popen(
                    cmd_list,
                    env=env,
                    cwd=str(self.install_dir)
                )
            
            self.unified_logger.log_runtime(f"启动IGV进程: PID {process.pid}")
            
            self.unified_logger.log_operation('启动IGV', {
                'launcher': str(actual_launcher.name),
                'java_home': env.get('JAVA_HOME', '系统默认'),
                'working_dir': str(self.install_dir),
                'pid': process.pid
            })
            
            self.unified_logger.log_runtime("IGV启动命令已执行，GUI正在初始化...")
            return True
            
        except Exception as e:
            self.unified_logger.log_error('IGV启动', f"启动失败: {e}")
            return False
    
    def uninstall(self) -> bool:
        """卸载IGV"""
        try:
            if self.install_dir.exists():
                shutil.rmtree(self.install_dir)
                self.unified_logger.log_installation('IGV', '卸载', '成功')
                return True
            else:
                self.unified_logger.log_runtime("IGV未安装，无需卸载")
                return True
        except Exception as e:
            self.unified_logger.log_error('IGV卸载', f"卸载失败: {e}")
            return False
    
    def _auto_install_java(self, progress_callback: Optional[Callable[[str, int], None]] = None) -> bool:
        """自动安装Java环境（需要Java 11+）"""
        try:
            from envs.runtime.java_runtime import JavaRuntime
            
            java_cache_path = Path("envs_cache") / "java"
            java_manager = JavaRuntime(java_cache_path)
            
            # IGV需要Java 11或更高版本
            java_requirements = {
                'version': '11+',
                'heap_size': '4g'  # IGV需要更多内存
            }
            
            java_check = java_manager.check_requirements(java_requirements)
            
            if java_check.get('satisfied', False):
                self.unified_logger.log_runtime("检测到合适的Java环境")
                return True
            
            # 安装Java 11
            def java_progress(status, percent):
                self.unified_logger.log_runtime(f"Java安装: {percent}% - {status}")
                if progress_callback and percent >= 0:
                    total_percent = 10 + int(percent * 0.1)
                    progress_callback(f"Java: {status}", total_percent)
            
            install_result = java_manager.install_java("11", java_progress)
            
            if install_result.get('success', False):
                self.unified_logger.log_installation('Java', '自动安装', '成功', install_result)
                return True
            else:
                self.unified_logger.log_error('Java安装', install_result.get('error', '未知错误'))
                return False
                
        except Exception as e:
            self.unified_logger.log_error('Java安装', f"异常: {e}")
            return False
    
    def _get_isolated_java_env(self) -> Dict[str, str]:
        """
        获取适合IGV的Java环境变量
        """
        import os
        from pathlib import Path
        
        # 使用系统环境变量作为基础
        env = os.environ.copy()
        
        # 查找本地Java
        java_cache_path = Path("envs_cache") / "java"
        
        java_home = None
        if java_cache_path.exists():
            java_dirs = [d for d in java_cache_path.iterdir() if d.is_dir() and d.name.startswith('java-')]
            if java_dirs:
                # 优先使用java-11或更高版本
                for java_dir in sorted(java_dirs, reverse=True):  # 倒序，优先选择高版本
                    if 'java-11' in java_dir.name or 'java-17' in java_dir.name or 'java-21' in java_dir.name:
                        java_home = java_dir
                        break
                if not java_home and java_dirs:
                    java_home = java_dirs[0]  # 如果没有合适版本，使用第一个
        
        if java_home and java_home.exists():
            # 获取绝对路径
            java_home_abs = java_home.resolve()
            java_bin_abs = java_home_abs / 'bin'
            
            # 设置Java环境变量
            if os.name == 'nt':
                # Windows路径处理
                java_bin_str = str(java_bin_abs).replace('/', '\\')
                java_home_str = str(java_home_abs).replace('/', '\\')
                current_path = env.get('PATH', '')
                env['PATH'] = f"{java_bin_str};{current_path}"
                env['JAVA_HOME'] = java_home_str
                
                self.unified_logger.log_runtime(f"设置Java环境: JAVA_HOME={java_home_str}")
            else:
                # Linux/macOS路径处理
                current_path = env.get('PATH', '')
                env['PATH'] = f"{java_bin_abs}:{current_path}"
                env['JAVA_HOME'] = str(java_home_abs)
                
                self.unified_logger.log_runtime(f"设置Java环境: JAVA_HOME={java_home_abs}")
        else:
            self.unified_logger.log_runtime("未找到本地Java环境，使用系统默认Java")
        
        # IGV特定的JVM参数
        env['IGV_MAX_MEMORY'] = '4096m'  # 最大内存4GB
        
        return env
    
    def _create_or_fix_launcher(self):
        """
        创建或修复启动脚本
        确保启动脚本正确配置
        """
        if os.name == 'nt':
            # Windows: 创建或检查批处理文件
            bat_file = self.install_dir / 'igv.bat'
            
            # 如果文件不存在或需要修复，创建新的
            if not bat_file.exists():
                # 查找IGV JAR文件位置
                lib_dir = self.install_dir / 'lib'
                if lib_dir.exists():
                    jar_pattern = 'lib\\igv*.jar'
                else:
                    jar_pattern = 'igv*.jar'
                
                batch_content = f'''@echo off
setlocal
set JAVA_OPTIONS=-Xmx4g --module-path=lib -Dapple.laf.useScreenMenuBar=true
java %JAVA_OPTIONS% -jar {jar_pattern} %*
'''
                bat_file.write_text(batch_content, encoding='utf-8')
                self.unified_logger.log_runtime(f"创建Windows启动器: {bat_file}")
        else:
            # Linux/macOS: 检查shell脚本
            sh_file = self.install_dir / 'igv.sh'
            if sh_file.exists():
                # 确保有执行权限
                os.chmod(sh_file, 0o755)
                self.unified_logger.log_runtime(f"设置执行权限: {sh_file}")
    
    def _extract_archive(self, archive_path: Path, extract_to: Path) -> bool:
        """
        解压文件（支持多种方法）
        """
        import shutil
        import subprocess
        
        # 方法1: shutil.unpack_archive
        try:
            self.unified_logger.log_runtime("尝试使用shutil.unpack_archive解压")
            shutil.unpack_archive(str(archive_path), str(extract_to))
            self.unified_logger.log_installation('IGV', '解压', '成功-shutil', {
                'method': 'shutil.unpack_archive'
            })
            return True
        except Exception as e:
            self.unified_logger.log_runtime(f"shutil解压失败: {e}")
        
        # 方法2: zipfile
        try:
            if archive_path.suffix.lower() == '.zip':
                self.unified_logger.log_runtime("尝试使用zipfile解压ZIP")
                with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_to)
                self.unified_logger.log_installation('IGV', '解压', '成功-zipfile', {
                    'method': 'zipfile'
                })
                return True
        except Exception as e:
            self.unified_logger.log_runtime(f"zipfile解压失败: {e}")
        
        # 所有方法都失败
        return False
    
    def get_installation_info(self) -> Optional[Dict[str, Any]]:
        """获取安装信息"""
        if not self.verify_installation():
            return None
        
        try:
            total_size = 0
            for file_path in self.install_dir.rglob('*'):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
            
            size_mb = total_size / (1024 * 1024)
            
            return {
                'install_path': str(self.install_dir),
                'executable_path': str(self.exe_path),
                'size_mb': round(size_mb, 1),
                'size_text': f"{size_mb:.1f} MB"
            }
        except Exception as e:
            self.unified_logger.log_error('IGV信息', f"获取失败: {e}")
            return None