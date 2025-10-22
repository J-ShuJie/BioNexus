"""
FastQC工具实现 v1.1.12 - 优化版本
解决架构复杂性、异步化网络调用、简化验证逻辑
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


class FastQC(ToolInterface):
    """
    FastQC工具实现 - 架构优化版本
    
    优化内容:
    1. 异步化网络调用，避免阻塞UI
    2. 简化安装验证，只检查本地文件
    3. 统一日志系统
    4. 缓存机制减少重复网络请求
    """
    
    # 缓存的元数据，避免重复网络调用
    _cached_metadata = None
    _cache_timestamp = 0
    _cache_duration = 300  # 5分钟缓存
    
    def __init__(self):
        """初始化FastQC工具"""
        self.logger = logging.getLogger(__name__)
        self.unified_logger = get_logger()

        # 安装路径配置 - 从配置读取
        path_resolver = get_path_resolver()
        self.install_base = path_resolver.get_install_dir()
        self.install_dir = self.install_base / "FastQC"
        self.temp_dir = Path("temp")
        
        # BioNexus是Windows专用软件，强制使用Windows可执行文件
        # 无论实际运行在什么环境，都使用Windows版本
        self.exe_name = "run_fastqc.bat"  # 强制使用Windows批处理文件
        
        self.exe_path = self.install_dir / self.exe_name
        
        # 下载器
        self.downloader = SmartDownloader()
        
        # 线程池用于异步操作
        self._executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="FastQC")
        
        self.unified_logger.log_runtime(f"FastQC工具初始化完成: {self.install_dir}")
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        获取FastQC元数据（优化版本）
        使用缓存机制，避免频繁网络调用
        """
        current_time = time.time()
        
        # 检查缓存是否有效
        if (self._cached_metadata and 
            current_time - self._cache_timestamp < self._cache_duration):
            return self._cached_metadata
        
        # 构建基础元数据（不依赖网络）
        base_metadata = {
            'name': 'FastQC',
            'version': '0.12.1',  # 默认版本，异步更新
            'category': 'quality',
            'description': '高通量测序数据质量控制工具，提供详细的质量报告和可视化图表。支持FASTQ、SAM、BAM等多种格式。',
            'size': '约 11 MB',
            'requires': ['java>=8'],
            'status': 'installed' if self.verify_installation() else 'available',
            'homepage': 'https://www.bioinformatics.babraham.ac.uk/projects/fastqc/',
            'documentation': 'https://www.bioinformatics.babraham.ac.uk/projects/fastqc/Help/',
            'license': 'GPL v3',
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
            api_url = "https://api.github.com/repos/s-andrews/FastQC/releases/latest"
            headers = {
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': 'BioNexus-VersionChecker/1.1.12'
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
                    
                    self.unified_logger.log_runtime(f"FastQC版本信息已异步更新: {version}")
                
        except Exception as e:
            self.unified_logger.log_error("FastQC版本更新", f"异步更新失败: {e}")
    
    def get_download_sources(self) -> List[Dict[str, Any]]:
        """
        获取FastQC下载源列表（简化版本）
        使用当前缓存的版本信息，不进行实时验证
        """
        version = self._cached_metadata.get('version', '0.12.1') if self._cached_metadata else '0.12.1'
        
        sources = [
            {
                'name': 'FastQC官方源',
                'url': f'https://www.bioinformatics.babraham.ac.uk/projects/fastqc/fastqc_v{version}.zip',
                'priority': 1,
                'location': 'UK',
                'timeout': 30,
                'description': 'FastQC官方网站，最可靠的下载源'
            }
        ]
        
        self.unified_logger.log_runtime(f"FastQC下载源: {sources[0]['url']}")
        return sources
    
    def check_dependencies(self) -> Dict[str, bool]:
        """
        检查FastQC依赖项（简化版本）
        主要检查Java环境，但不阻塞安装流程
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
                java_version = version_output.split()[2].strip('"') if version_output else 'unknown'
                self.unified_logger.log_runtime(f"系统Java版本: {java_version}")
            
        except Exception as e:
            # Java不可用，但不影响安装（会自动安装Java）
            dependencies['java'] = False
            self.unified_logger.log_runtime(f"系统Java不可用: {e}")
        
        # 检查本地Java环境
        java_cache_path = Path("envs_cache") / "java"
        if java_cache_path.exists():
            java_dirs = [d for d in java_cache_path.iterdir() if d.is_dir() and d.name.startswith('java-')]
            if java_dirs:
                dependencies['local_java'] = True
                self.unified_logger.log_runtime(f"检测到本地Java环境: {[d.name for d in java_dirs]}")
            else:
                dependencies['local_java'] = False
        else:
            dependencies['local_java'] = False
        
        return dependencies
    
    def install(self, progress_callback: Optional[Callable[[str, int], None]] = None) -> bool:
        """
        安装FastQC（优化版本）
        简化流程，减少不必要的复杂性
        """
        try:
            # 1. 检查依赖（不阻塞）
            if progress_callback:
                progress_callback("检查系统依赖...", 5)
            
            deps = self.check_dependencies()
            self.unified_logger.log_installation('FastQC', '依赖检查', '完成', deps)
            
            # 2. 如果Java不可用，尝试自动安装
            if not deps.get('java', False) and not deps.get('local_java', False):
                if progress_callback:
                    progress_callback("正在自动安装Java环境...", 10)
                
                java_installed = self._auto_install_java(progress_callback)
                if not java_installed:
                    self.unified_logger.log_error('FastQC安装', 'Java环境安装失败')
                    if progress_callback:
                        progress_callback("Java环境安装失败，继续尝试安装FastQC", 25)
                else:
                    self.unified_logger.log_installation('FastQC', 'Java环境', '安装成功')
            
            # 3. 准备目录
            if progress_callback:
                progress_callback("准备安装目录...", 25)
            
            self.install_base.mkdir(exist_ok=True)
            self.temp_dir.mkdir(exist_ok=True)
            
            # 清理旧安装
            if self.install_dir.exists():
                shutil.rmtree(self.install_dir)
                self.unified_logger.log_installation('FastQC', '清理旧版本', '完成')
            
            # 4. 下载文件
            if progress_callback:
                progress_callback("开始下载FastQC...", 30)
            
            # 获取当前版本
            current_version = self._cached_metadata.get('version', '0.12.1') if self._cached_metadata else '0.12.1'
            zip_path = self.temp_dir / f"fastqc_v{current_version}.zip"
            
            self.unified_logger.log_installation('FastQC', '确定版本', '成功', {
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
                self.unified_logger.log_error('FastQC安装', '下载失败')
                if progress_callback:
                    progress_callback("下载失败", -1)
                return False
            
            self.unified_logger.log_installation('FastQC', '下载', '完成', {
                'file_size': zip_path.stat().st_size if zip_path.exists() else 0
            })
            
            # 5. 解压安装
            if progress_callback:
                progress_callback("正在解压安装包...", 85)
            
            # 使用分层解压策略确保可靠性
            success = self._extract_archive(zip_path, self.install_base)
            if not success:
                self.unified_logger.log_error('FastQC解压', "所有解压方法均失败")
                if progress_callback:
                    progress_callback("解压失败", -1)
                return False
            
            # 重命名解压目录
            try:
                extracted_dirs = [d for d in self.install_base.iterdir() if d.is_dir() and 'fastqc' in d.name.lower()]
                if extracted_dirs:
                    actual_dir = extracted_dirs[0]
                    if actual_dir != self.install_dir:
                        actual_dir.rename(self.install_dir)
                    self.unified_logger.log_installation('FastQC', '目录重命名', '成功', {
                        'from': str(actual_dir),
                        'to': str(self.install_dir)
                    })
                else:
                    self.unified_logger.log_error('FastQC解压', '未找到解压的FastQC目录')
                    if progress_callback:
                        progress_callback("解压目录未找到", -1)
                    return False
            except Exception as e:
                self.unified_logger.log_error('FastQC重命名', f"重命名失败: {e}")
                if progress_callback:
                    progress_callback("重命名失败", -1)
                return False
            
            # 6. 设置权限（Linux/macOS）
            if os.name != 'nt':
                try:
                    os.chmod(self.exe_path, 0o755)
                    self.unified_logger.log_installation('FastQC', '权限设置', '完成')
                except Exception as e:
                    self.unified_logger.log_error('FastQC权限', f"设置失败: {e}")
            
            # 7. 验证安装
            if progress_callback:
                progress_callback("验证安装...", 95)
            
            if not self.verify_installation():
                self.unified_logger.log_error('FastQC安装', '验证失败')
                if progress_callback:
                    progress_callback("安装验证失败", -1)
                return False
            
            # 8. 清理临时文件
            try:
                zip_path.unlink()
                self.unified_logger.log_installation('FastQC', '清理临时文件', '完成')
            except:
                pass
            
            if progress_callback:
                progress_callback("FastQC安装完成", 100)
            
            self.unified_logger.log_installation('FastQC', '安装完成', '成功', {
                'install_path': str(self.install_dir),
                'executable': str(self.exe_path)
            })
            return True
            
        except Exception as e:
            error_msg = f"FastQC安装失败: {e}"
            self.unified_logger.log_error('FastQC安装', error_msg)
            if progress_callback:
                progress_callback(error_msg, -1)
            return False
    
    def verify_installation(self) -> bool:
        """
        验证FastQC是否已安装（增强版本）
        详细检查并记录验证过程
        """
        self.unified_logger.log_runtime(f"开始验证FastQC安装: {self.install_dir}")
        
        # 1. 检查安装目录是否存在
        if not self.install_dir.exists():
            self.unified_logger.log_runtime(f"FastQC验证失败: 安装目录不存在 - {self.install_dir}")
            return False
        
        self.unified_logger.log_runtime(f"✓ 安装目录存在: {self.install_dir}")
        
        # 2. 检查可执行文件是否存在
        self.unified_logger.log_runtime(f"检查可执行文件: {self.exe_path}")
        if not self.exe_path.exists():
            # 尝试检查其他可能的可执行文件
            alternative_exes = []
            if os.name == 'nt':  # Windows
                alternative_exes = ['fastqc.bat', 'run_fastqc.bat', 'fastqc']
            else:
                alternative_exes = ['fastqc', 'run_fastqc']
            
            found_exe = None
            for alt_exe in alternative_exes:
                alt_path = self.install_dir / alt_exe
                if alt_path.exists():
                    found_exe = alt_path
                    self.unified_logger.log_runtime(f"找到可执行文件: {alt_path}")
                    break
            
            if not found_exe:
                self.unified_logger.log_runtime(f"FastQC验证失败: 未找到可执行文件，查找过: {alternative_exes}")
                return False
        else:
            self.unified_logger.log_runtime(f"✓ 可执行文件存在: {self.exe_path}")
        
        # 3. 检查关键JAR文件是否存在
        jar_files = ['cisd-jhdf5.jar', 'htsjdk.jar']
        missing_jars = []
        
        for jar_file in jar_files:
            jar_path = self.install_dir / jar_file
            if not jar_path.exists():
                missing_jars.append(jar_file)
                self.unified_logger.log_runtime(f"✗ 关键文件缺失: {jar_file}")
            else:
                file_size = jar_path.stat().st_size
                self.unified_logger.log_runtime(f"✓ 关键文件存在: {jar_file} ({file_size:,} bytes)")
        
        if missing_jars:
            self.unified_logger.log_runtime(f"FastQC验证失败: 缺少关键JAR文件 - {missing_jars}")
            return False
        
        # 4. 检查其他重要文件
        important_files = ['README.txt', 'Configuration']
        for important_file in important_files:
            file_path = self.install_dir / important_file
            if file_path.exists():
                self.unified_logger.log_runtime(f"✓ 重要文件/目录存在: {important_file}")
            else:
                self.unified_logger.log_runtime(f"⚠ 可选文件缺失: {important_file}")
        
        # 5. 验证通过
        self.unified_logger.log_runtime("✅ FastQC文件完整性验证通过")
        return True
    
    def launch(self, args: Optional[List[str]] = None) -> bool:
        """
        启动FastQC（使用隔离的Java环境）
        """
        if not self.verify_installation():
            self.unified_logger.log_error('FastQC启动', 'FastQC未安装')
            return False
        
        try:
            # BioNexus是Windows专用软件，使用Windows批处理文件
            actual_exe = self.install_dir / 'run_fastqc.bat'
            if not actual_exe.exists():
                # 如果run_fastqc.bat不存在，创建一个
                self._create_windows_launcher()
                actual_exe = self.install_dir / 'run_fastqc.bat'
            else:
                # 检查并修复批处理文件中JAR引用错误
                self._fix_batch_file_if_needed()
            
            self.unified_logger.log_runtime(f"使用可执行文件: {actual_exe}")
            
            # 构建启动命令 - 使用相对路径保持可移植性
            cmd_list = [str(actual_exe.name)]  # 只使用文件名，不包含路径
            if args:
                cmd_list.extend(args)
            
            # 对于Windows shell=True，使用相对路径命令
            # 关键：通过cwd设置正确的工作目录来解决路径问题
            cmd_str = f'"{actual_exe.name}"'  # 只使用文件名
            if args:
                cmd_str += ' ' + ' '.join(f'"{arg}"' for arg in args)
            
            # 获取隔离的Java环境
            env = self._get_isolated_java_env()
            
            # BioNexus Windows启动逻辑 - 使用相对路径保持可移植性
            self.unified_logger.log_runtime(f"BioNexus Windows启动命令(相对路径): {cmd_str}")
            self.unified_logger.log_runtime(f"工作目录: {self.install_dir}")
            
            # Windows批处理文件启动方式
            # 关键原理：通过cwd设置工作目录为FastQC安装目录
            # 这样相对路径"run_fastqc.bat"就能正确找到文件
            process = subprocess.Popen(
                cmd_str,           # 相对路径命令
                shell=True,        # 关键！bat文件需要通过shell执行
                env=env,           # 保留环境隔离功能
                cwd=str(self.install_dir)  # 关键！设置工作目录为FastQC安装目录
                # 注释掉可能导致问题的参数：
                # creationflags=subprocess.CREATE_NEW_CONSOLE,  # 可能阻止GUI显示
                # stdin=subprocess.DEVNULL,   # 可能影响GUI交互
                # stdout=subprocess.DEVNULL,  # 可能阻止GUI显示
                # stderr=subprocess.DEVNULL   # 可能隐藏重要错误信息
            )
            self.unified_logger.log_runtime(f"启动FastQC进程: PID {process.pid}")
            
            self.unified_logger.log_operation('启动FastQC', {
                'command': cmd_str,  # 相对路径命令
                'java_home': env.get('JAVA_HOME', '系统默认'),
                'working_dir': str(self.install_dir),  # 相对路径
                'pid': process.pid
            })
            
            # 注释掉进程退出检查：
            # 原因：GUI程序的启动行为与命令行程序不同
            # - GUI程序可能创建子进程后父进程退出
            # - 或者需要时间来初始化窗口系统
            # - 0.5秒检查对GUI程序来说太短了
            
            # import time
            # time.sleep(0.5)
            # 
            # # 检查进程是否仍在运行
            # if process.poll() is not None:
            #     # 进程已经退出，可能有错误  
            #     self.unified_logger.log_error('FastQC启动', f"进程立即退出，退出码: {process.poll()}")
            #     return False
            
            # 对于GUI程序，只要能成功创建进程就认为启动成功
            self.unified_logger.log_runtime("FastQC启动命令已执行，GUI应该正在初始化...")
            return True
            
        except Exception as e:
            self.unified_logger.log_error('FastQC启动', f"启动失败: {e}")
            return False
    
    def uninstall(self) -> bool:
        """卸载FastQC"""
        try:
            if self.install_dir.exists():
                shutil.rmtree(self.install_dir)
                self.unified_logger.log_installation('FastQC', '卸载', '成功')
                return True
            else:
                self.unified_logger.log_runtime("FastQC未安装，无需卸载")
                return True
        except Exception as e:
            self.unified_logger.log_error('FastQC卸载', f"卸载失败: {e}")
            return False
    
    def _auto_install_java(self, progress_callback: Optional[Callable[[str, int], None]] = None) -> bool:
        """自动安装Java环境（简化版本）"""
        try:
            from envs.runtime.java_runtime import JavaRuntime
            
            java_cache_path = Path("envs_cache") / "java"
            java_manager = JavaRuntime(java_cache_path)
            
            # 检查Java需求
            java_requirements = {
                'version': '11+',
                'heap_size': '2g'
            }
            
            java_check = java_manager.check_requirements(java_requirements)
            
            if java_check.get('satisfied', False):
                self.unified_logger.log_runtime("检测到合适的Java环境")
                return True
            
            # 安装Java
            def java_progress(status, percent):
                self.unified_logger.log_runtime(f"Java安装: {percent}% - {status}")
                if progress_callback and percent >= 0:
                    total_percent = 10 + int(percent * 0.15)
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
        获取适合GUI程序的Java环境变量（保守版本）
        只添加Java路径，保留所有Windows GUI所需的环境变量
        """
        import os
        from pathlib import Path
        
        # 使用系统环境变量作为基础（关键！）
        env = os.environ.copy()
        
        # 查找本地Java
        java_cache_path = Path("envs_cache") / "java"
        
        java_home = None
        if java_cache_path.exists():
            java_dirs = [d for d in java_cache_path.iterdir() if d.is_dir() and d.name.startswith('java-')]
            if java_dirs:
                # 优先使用java-11
                for java_dir in java_dirs:
                    if 'java-11' in java_dir.name:
                        java_home = java_dir
                        break
                if not java_home:
                    java_home = java_dirs[0]
        
        if java_home and java_home.exists():
            # 获取绝对路径
            java_home_abs = java_home.resolve()
            java_bin_abs = java_home_abs / 'bin'
            
            # 只在PATH前面添加我们的Java路径，不设置JAVA_HOME
            if os.name == 'nt':
                # Windows路径处理
                java_bin_str = str(java_bin_abs).replace('/', '\\')
                current_path = env.get('PATH', '')
                env['PATH'] = f"{java_bin_str};{current_path}"
                
                self.unified_logger.log_runtime(f"添加Java路径到PATH: {java_bin_str}")
                # 注释掉JAVA_HOME设置，让系统自动处理
                # env['JAVA_HOME'] = str(java_home_abs).replace('/', '\\')
            else:
                # Linux/macOS路径处理
                current_path = env.get('PATH', '')
                env['PATH'] = f"{java_bin_abs}:{current_path}"
                
                self.unified_logger.log_runtime(f"添加Java路径到PATH: {java_bin_abs}")
                # 注释掉JAVA_HOME设置，让系统自动处理  
                # env['JAVA_HOME'] = str(java_home_abs)
        else:
            self.unified_logger.log_runtime("未找到本地Java环境，使用系统默认Java")
            # 不修改PATH，完全使用系统环境
        
        return env
    
    def _create_windows_launcher(self):
        """
        创建Windows批处理启动器（如果不存在）
        """
        batch_file = self.install_dir / 'run_fastqc.bat'
        
        if not batch_file.exists():
            # 创建一个正确的批处理文件来启动FastQC
            batch_content = '@echo off\n'
            batch_content += 'java -Xmx250m -classpath .;./htsjdk.jar;./jbzip2-0.9.jar;./cisd-jhdf5.jar uk.ac.babraham.FastQC.FastQCApplication %*\n'
            
            batch_file.write_text(batch_content, encoding='utf-8')
            self.unified_logger.log_runtime(f"创建Windows启动器: {batch_file}")
    
    def _fix_batch_file_if_needed(self):
        """
        检查并修复run_fastqc.bat文件中的JAR引用错误
        """
        batch_file = self.install_dir / 'run_fastqc.bat'
        
        if batch_file.exists():
            try:
                content = batch_file.read_text(encoding='utf-8')
                
                # 检查是否包含错误的sam-1.103.jar引用
                if 'sam-1.103.jar' in content:
                    self.unified_logger.log_runtime("检测到错误的JAR引用，正在修复...")
                    
                    # 更新批处理文件内容
                    corrected_content = '@echo off\n'
                    corrected_content += 'java -Xmx250m -classpath .;./htsjdk.jar;./jbzip2-0.9.jar;./cisd-jhdf5.jar uk.ac.babraham.FastQC.FastQCApplication %*\n'
                    
                    batch_file.write_text(corrected_content, encoding='utf-8')
                    self.unified_logger.log_runtime("已修复run_fastqc.bat中JAR文件引用")
                    return True
                else:
                    self.unified_logger.log_runtime("批处理文件JAR引用正确")
                    return False
                    
            except Exception as e:
                self.unified_logger.log_error('FastQC批处理文件检查', f"检查失败: {e}")
                return False
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
            self.unified_logger.log_error('FastQC信息', f"获取失败: {e}")
            return None
    
    def _extract_archive(self, archive_path: Path, extract_to: Path) -> bool:
        """
        分层解压策略，按优先级尝试多种解压方法
        确保在Windows 10环境下的可靠性
        """
        import shutil
        import subprocess
        
        # 方法1: shutil.unpack_archive (最可靠，内置模块)
        try:
            self.unified_logger.log_runtime("尝试使用shutil.unpack_archive解压")
            shutil.unpack_archive(str(archive_path), str(extract_to))
            self.unified_logger.log_installation('FastQC', '解压', '成功-shutil', {
                'method': 'shutil.unpack_archive',
                'archive': str(archive_path),
                'extract_to': str(extract_to)
            })
            return True
        except Exception as e:
            self.unified_logger.log_runtime(f"shutil解压失败: {e}")
        
        # 方法2: zipfile (ZIP专用，内置模块)
        try:
            if archive_path.suffix.lower() == '.zip':
                self.unified_logger.log_runtime("尝试使用zipfile解压ZIP")
                with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_to)
                self.unified_logger.log_installation('FastQC', '解压', '成功-zipfile', {
                    'method': 'zipfile',
                    'archive': str(archive_path),
                    'extract_to': str(extract_to)
                })
                return True
        except Exception as e:
            self.unified_logger.log_runtime(f"zipfile解压失败: {e}")
        
        # 方法3: Windows系统7zip (回退方案)
        if os.name == 'nt':  # Windows
            try:
                # 常见的7zip安装路径
                seven_zip_paths = [
                    r'C:\Program Files\7-Zip\7z.exe',
                    r'C:\Program Files (x86)\7-Zip\7z.exe'
                ]
                
                seven_zip_exe = None
                for path in seven_zip_paths:
                    if Path(path).exists():
                        seven_zip_exe = path
                        break
                
                if seven_zip_exe:
                    self.unified_logger.log_runtime(f"尝试使用系统7zip解压: {seven_zip_exe}")
                    # 7zip命令: 7z x archive.zip -o目标目录
                    cmd = [seven_zip_exe, 'x', str(archive_path), f'-o{extract_to}', '-y']
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    
                    if result.returncode == 0:
                        self.unified_logger.log_installation('FastQC', '解压', '成功-7zip', {
                            'method': '7zip.exe',
                            'path': seven_zip_exe,
                            'archive': str(archive_path),
                            'extract_to': str(extract_to)
                        })
                        return True
                    else:
                        self.unified_logger.log_runtime(f"7zip解压失败: {result.stderr}")
                else:
                    self.unified_logger.log_runtime("未找到系统7zip.exe")
            except Exception as e:
                self.unified_logger.log_runtime(f"7zip解压异常: {e}")
        
        # 所有方法都失败
        self.unified_logger.log_error('解压失败', '所有解压方法均无法处理此文件', {
            'archive': str(archive_path),
            'methods_tried': ['shutil.unpack_archive', 'zipfile', '7zip.exe']
        })
        return False
