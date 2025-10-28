"""
SAMtools 工具实现
通过Conda/Bioconda安装，支持Windows环境
"""
import os
import shutil
import subprocess
import logging
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any
from concurrent.futures import ThreadPoolExecutor

from .cli_tool_base import CLIToolBase
from utils.unified_logger import get_logger
from utils.path_resolver import get_path_resolver


class SAMtools(CLIToolBase):
    """
    SAMtools (Sequence Alignment/Map Tools)

    功能：
    1. 处理SAM/BAM/CRAM格式文件
    2. 排序、索引、查看比对结果
    3. 统计比对质量
    4. 格式转换

    安装方式：
    - 通过Conda/Bioconda安装到独立环境
    - 启动时激活conda环境并打开终端窗口
    """

    # 缓存的元数据
    _cached_metadata = None
    _cache_timestamp = 0
    _cache_duration = 300

    def __init__(self):
        """初始化SAMtools工具"""
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.unified_logger = get_logger()

        # 使用conda环境
        self.conda_env_name = "bionexus_samtools"
        self.conda_env_path = Path("envs") / self.conda_env_name

        # 线程池
        self._executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="SAMtools")

        self.unified_logger.log_runtime(f"SAMtools工具初始化完成")

    def get_metadata(self) -> Dict[str, Any]:
        """获取SAMtools元数据"""
        current_time = time.time()

        if (self._cached_metadata and
            current_time - self._cache_timestamp < self._cache_duration):
            md = dict(self._cached_metadata)
            md['status'] = 'installed' if self.verify_installation() else 'available'
            return md

        base_metadata = {
            'name': 'SAMtools',
            'version': '1.22',  # 默认版本
            'category': 'genomics',
            'description': '处理高通量测序比对数据的工具集，支持SAM/BAM/CRAM格式。提供排序、索引、查看等功能。',
            'size': '约 20 MB',
            'requires': ['conda'],
            'status': 'installed' if self.verify_installation() else 'available',
            'homepage': 'http://www.htslib.org/',
            'documentation': 'http://www.htslib.org/doc/samtools.html',
            'license': 'MIT/Expat',
            'published_date': ''
        }

        self._cached_metadata = base_metadata
        self._cache_timestamp = current_time

        ret = dict(base_metadata)
        ret['status'] = 'installed' if self.verify_installation() else 'available'
        return ret

    def get_download_sources(self) -> List[Dict[str, Any]]:
        """
        SAMtools通过Conda安装，不需要直接下载源
        """
        return []

    def check_dependencies(self) -> Dict[str, bool]:
        """检查依赖项（主要是Conda）"""
        dependencies = {}

        # 检查是否有conda
        try:
            result = subprocess.run(
                ['conda', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            dependencies['conda'] = result.returncode == 0
            if dependencies['conda']:
                self.unified_logger.log_runtime(f"检测到Conda: {result.stdout.strip()}")
        except Exception as e:
            dependencies['conda'] = False
            self.unified_logger.log_runtime(f"Conda不可用: {e}")

        return dependencies

    def install(self, progress_callback: Optional[Callable[[str, int], None]] = None) -> bool:
        """
        通过Conda安装SAMtools
        """
        try:
            # 1. 检查Conda
            if progress_callback:
                progress_callback("检查Conda环境...", 5)

            deps = self.check_dependencies()
            if not deps.get('conda', False):
                error_msg = "Conda未安装，无法安装SAMtools。请先安装Miniconda或Anaconda。"
                self.unified_logger.log_error('SAMtools安装', error_msg)
                if progress_callback:
                    progress_callback(error_msg, -1)
                return False

            self.unified_logger.log_installation('SAMtools', 'Conda检查', '通过')

            # 2. 创建Conda环境
            if progress_callback:
                progress_callback("创建Conda环境...", 20)

            # 检查环境是否已存在
            env_exists = self._check_conda_env_exists()

            if env_exists:
                self.unified_logger.log_runtime(f"Conda环境已存在: {self.conda_env_name}")
                if progress_callback:
                    progress_callback("Conda环境已存在，准备更新...", 30)
            else:
                # 创建新环境
                if progress_callback:
                    progress_callback(f"正在创建Conda环境 {self.conda_env_name}...", 30)

                create_cmd = [
                    'conda', 'create',
                    '-n', self.conda_env_name,
                    '-y',  # 自动确认
                    'python=3.9'  # 指定Python版本
                ]

                result = subprocess.run(
                    create_cmd,
                    capture_output=True,
                    text=True,
                    timeout=300  # 5分钟超时
                )

                if result.returncode != 0:
                    error_msg = f"创建Conda环境失败: {result.stderr}"
                    self.unified_logger.log_error('SAMtools安装', error_msg)
                    if progress_callback:
                        progress_callback(error_msg, -1)
                    return False

                self.unified_logger.log_installation('SAMtools', '创建Conda环境', '成功')

            # 3. 添加Bioconda频道
            if progress_callback:
                progress_callback("配置Bioconda频道...", 40)

            channel_cmds = [
                ['conda', 'config', '--add', 'channels', 'defaults'],
                ['conda', 'config', '--add', 'channels', 'bioconda'],
                ['conda', 'config', '--add', 'channels', 'conda-forge']
            ]

            for cmd in channel_cmds:
                subprocess.run(cmd, capture_output=True, timeout=30)

            self.unified_logger.log_installation('SAMtools', 'Bioconda频道', '已配置')

            # 4. 在环境中安装SAMtools
            if progress_callback:
                progress_callback("正在安装SAMtools（这可能需要几分钟）...", 50)

            install_cmd = [
                'conda', 'install',
                '-n', self.conda_env_name,
                '-c', 'bioconda',
                '-c', 'conda-forge',
                '-y',
                'samtools'
            ]

            self.unified_logger.log_runtime(f"执行安装命令: {' '.join(install_cmd)}")

            result = subprocess.run(
                install_cmd,
                capture_output=True,
                text=True,
                timeout=600  # 10分钟超时
            )

            if result.returncode != 0:
                error_msg = f"安装SAMtools失败: {result.stderr}"
                self.unified_logger.log_error('SAMtools安装', error_msg)
                if progress_callback:
                    progress_callback(error_msg, -1)
                return False

            self.unified_logger.log_installation('SAMtools', '安装', '成功')

            # 5. 验证安装
            if progress_callback:
                progress_callback("验证安装...", 95)

            if not self.verify_installation():
                error_msg = "SAMtools安装验证失败"
                self.unified_logger.log_error('SAMtools安装', error_msg)
                if progress_callback:
                    progress_callback(error_msg, -1)
                return False

            if progress_callback:
                progress_callback("SAMtools安装完成", 100)

            self.unified_logger.log_installation('SAMtools', '完成', '成功', {
                'conda_env': self.conda_env_name
            })
            return True

        except Exception as e:
            error_msg = f"SAMtools安装失败: {e}"
            self.unified_logger.log_error('SAMtools安装', error_msg)
            if progress_callback:
                progress_callback(error_msg, -1)
            return False

    def _check_conda_env_exists(self) -> bool:
        """检查Conda环境是否存在"""
        try:
            result = subprocess.run(
                ['conda', 'env', 'list'],
                capture_output=True,
                text=True,
                timeout=30
            )
            return self.conda_env_name in result.stdout
        except Exception:
            return False

    def verify_installation(self) -> bool:
        """验证SAMtools是否已安装"""
        try:
            # 在conda环境中运行samtools --version
            if os.name == 'nt':
                # Windows
                cmd = f'conda run -n {self.conda_env_name} samtools --version'
            else:
                cmd = f'conda run -n {self.conda_env_name} samtools --version'

            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0 and 'samtools' in result.stdout.lower():
                version_line = result.stdout.split('\n')[0]
                self.unified_logger.log_runtime(f"✅ SAMtools验证通过: {version_line}")
                return True
            else:
                self.unified_logger.log_runtime(f"SAMtools验证失败: {result.stderr}")
                return False

        except Exception as e:
            self.unified_logger.log_runtime(f"SAMtools验证异常: {e}")
            return False

    def launch(self, args: Optional[List[str]] = None) -> bool:
        """
        启动SAMtools
        打开新的cmd窗口，激活conda环境
        """
        if not self.verify_installation():
            self.unified_logger.log_error('SAMtools启动', 'SAMtools未安装')
            return False

        try:
            # 构建启动命令
            welcome_msg = """
================================
  SAMtools - BioNexus
  Conda环境已激活
================================

SAMtools已配置好，您可以直接使用命令：
  samtools --help       查看帮助
  samtools view         查看BAM文件
  samtools sort         排序BAM文件
  samtools index        索引BAM文件

示例：
  samtools view input.bam | head
  samtools sort input.bam -o sorted.bam
  samtools index sorted.bam

关闭此窗口将自动记录使用时长
================================
"""

            if os.name == 'nt':
                # Windows: 激活conda环境并保持窗口打开
                cmd = f'cmd.exe /K "conda activate {self.conda_env_name} && echo {welcome_msg}"'

                self.unified_logger.log_runtime(f"Windows启动命令")

                process = subprocess.Popen(
                    cmd,
                    shell=True,
                    creationflags=subprocess.CREATE_NEW_CONSOLE
                )
            else:
                # Linux/macOS
                cmd = f'conda activate {self.conda_env_name} && bash'
                process = subprocess.Popen(
                    ['xterm', '-e', cmd]
                )

            pid = process.pid
            self.unified_logger.log_runtime(f"启动SAMtools终端窗口: PID {pid}")

            self.unified_logger.log_operation('启动SAMtools', {
                'type': 'cli_tool',
                'conda_env': self.conda_env_name,
                'pid': pid
            })

            return True

        except Exception as e:
            self.unified_logger.log_error('SAMtools启动', f"启动失败: {e}")
            return False

    def uninstall(self) -> bool:
        """卸载SAMtools（删除Conda环境）"""
        try:
            if not self._check_conda_env_exists():
                self.unified_logger.log_runtime("SAMtools环境不存在，无需卸载")
                return True

            # 删除conda环境
            cmd = ['conda', 'env', 'remove', '-n', self.conda_env_name, '-y']

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120
            )

            if result.returncode == 0:
                self.unified_logger.log_installation('SAMtools', '卸载', '成功')
                return True
            else:
                error_msg = f"卸载失败: {result.stderr}"
                self.unified_logger.log_error('SAMtools卸载', error_msg)
                return False

        except Exception as e:
            self.unified_logger.log_error('SAMtools卸载', f"卸载失败: {e}")
            return False

    def _get_tool_path(self) -> Optional[Path]:
        """
        获取工具路径
        对于conda环境中的工具，这个方法不太适用
        """
        # SAMtools在conda环境中，路径会随环境变化
        # 这里返回一个标识性路径
        return Path(f"conda_env:{self.conda_env_name}:samtools")

    def get_installation_info(self) -> Optional[Dict[str, Any]]:
        """获取安装信息"""
        if not self.verify_installation():
            return None

        return {
            'install_path': f'Conda环境: {self.conda_env_name}',
            'executable_path': 'conda run -n ' + self.conda_env_name + ' samtools',
            'size_mb': 20,  # 估计值
            'size_text': '约 20 MB',
            'type': 'cli_tool_conda'
        }
