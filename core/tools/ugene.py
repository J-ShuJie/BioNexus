"""
UGENE 工具实现
Unipro UGENE - 综合生物信息学分析工具
"""
import os
import shutil
import subprocess
import zipfile
import logging
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any
from concurrent.futures import ThreadPoolExecutor
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

from .base import ToolInterface
from ..downloader import SmartDownloader
from utils.unified_logger import get_logger
from utils.path_resolver import get_path_resolver


class UGENE(ToolInterface):
    """
    UGENE (Unipro UGENE) 工具实现

    功能：
    1. DNA和蛋白质序列可视化
    2. 多序列比对
    3. 序列组装和注释
    4. NGS数据分析
    5. 系统发育树构建
    """

    # 缓存的元数据
    _cached_metadata = None
    _cache_timestamp = 0
    _cache_duration = 300  # 5分钟缓存

    def __init__(self):
        """初始化UGENE工具"""
        self.logger = logging.getLogger(__name__)
        self.unified_logger = get_logger()

        # 安装路径配置
        path_resolver = get_path_resolver()
        self.install_base = path_resolver.get_install_dir()
        self.install_dir = self.install_base / "UGENE"
        self.temp_dir = Path("temp")

        # 可执行文件配置
        if os.name == 'nt':  # Windows
            self.exe_name = "ugeneui.exe"
        else:  # Linux/macOS
            self.exe_name = "ugene"

        self.exe_path = self.install_dir / self.exe_name

        # 下载器
        self.downloader = SmartDownloader()

        # 线程池
        self._executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="UGENE")

        self.unified_logger.log_runtime(f"UGENE工具初始化完成: {self.install_dir}")

    def get_metadata(self) -> Dict[str, Any]:
        """获取UGENE元数据"""
        current_time = time.time()

        # 检查缓存
        if (self._cached_metadata and
            current_time - self._cache_timestamp < self._cache_duration):
            md = dict(self._cached_metadata)
            md['status'] = 'installed' if self.verify_installation() else 'available'
            return md

        # 构建基础元数据
        base_metadata = {
            'name': 'UGENE',
            'version': '52.1',  # 默认版本
            'category': 'genomics',
            'description': '综合生物信息学工具，支持序列查看、比对、组装、注释等功能。集成多种NGS数据分析工具。',
            'size': '约 150 MB',
            'requires': [],
            'status': 'installed' if self.verify_installation() else 'available',
            'homepage': 'https://ugene.net/',
            'documentation': 'https://ugene.net/docs/',
            'license': 'GPL-2.0',
            'published_date': '',
            'release_notes': ''
        }

        # 异步更新版本信息
        if current_time - self._cache_timestamp > self._cache_duration:
            self._executor.submit(self._async_update_metadata, base_metadata)

        # 更新缓存
        self._cached_metadata = base_metadata
        self._cache_timestamp = current_time

        ret = dict(base_metadata)
        ret['status'] = 'installed' if self.verify_installation() else 'available'
        return ret

    def _async_update_metadata(self, base_metadata: Dict[str, Any]):
        """异步更新元数据"""
        try:
            # 从GitHub API获取最新版本
            api_url = "https://api.github.com/repos/ugeneunipro/ugene/releases/latest"
            headers = {
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': 'BioNexus-UGENE/1.3.1'
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
                    self._cached_metadata['release_notes'] = data.get('body', '')[:200]

                    self.unified_logger.log_runtime(f"UGENE版本信息已异步更新: {version}")

        except Exception as e:
            self.unified_logger.log_runtime(f"UGENE版本更新: 异步更新失败: {e}")

    def get_download_sources(self) -> List[Dict[str, Any]]:
        """获取UGENE下载源列表"""
        version = self._cached_metadata.get('version', '52.1') if self._cached_metadata else '52.1'
        # 规范化版本：官方常用 1.xx.y 命名；若是“52.1”形式，追加一个 1.{version} 作为变体
        normalized_variants = {version}
        if version.count('.') == 1 and version.split('.')[0].isdigit():
            normalized_variants.add(f"1.{version}")

        # 先尝试通过 GitHub Releases API 获取资产列表：latest -> releases 列表 -> tag 变体
        sources: List[Dict[str, Any]] = []

        def _pick_win_assets(assets):
            def is_preferred_win_asset(name: str) -> bool:
                n = (name or '').lower()
                return n.endswith('.zip') and ('win' in n or 'windows' in n) and any(k in n for k in ['64', 'x64', 'x86_64'])
            preferred = [a for a in (assets or []) if is_preferred_win_asset(a.get('name'))]
            if not preferred:
                preferred = [a for a in (assets or []) if (a.get('name','').lower().endswith('.zip') and ('win' in a.get('name','').lower() or 'windows' in a.get('name','').lower()))]
            return preferred

        # 1) latest
        try:
            api_url = "https://api.github.com/repos/ugeneunipro/ugene/releases/latest"
            headers = {
                'Accept': 'application/vnd.github+json',
                'User-Agent': 'BioNexus-UGENE-Downloader/1.3.3'
            }
            request = Request(api_url, headers=headers)
            with urlopen(request, timeout=6) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                assets = data.get('assets', []) or []
                preferred = _pick_win_assets(assets)
                prio = 1
                for a in preferred:
                    url = a.get('browser_download_url')
                    if not url:
                        continue
                    sources.append({
                        'name': f'UGENE官方源#{prio}',
                        'url': url,
                        'priority': prio,
                        'location': 'GitHub',
                        'timeout': 45,
                        'description': 'GitHub Releases 资产'
                    })
                    prio += 1
                # 记录网络日志
                self.unified_logger.log_network(api_url, 'GET', getattr(resp, 'status', 200), 0)
        except Exception as e:
            self.unified_logger.log_error('UGENE下载源', f'获取GitHub资产失败: {e}', {'version': version})

        # 2) 如果latest没拿到，尝试 releases 列表（前几条）
        if not sources:
            try:
                api_url = "https://api.github.com/repos/ugeneunipro/ugene/releases"
                headers = {
                    'Accept': 'application/vnd.github+json',
                    'User-Agent': 'BioNexus-UGENE-Downloader/1.3.3'
                }
                request = Request(api_url, headers=headers)
                with urlopen(request, timeout=6) as resp:
                    releases = json.loads(resp.read().decode('utf-8')) or []
                    prio = 1
                    for rel in releases[:5]:
                        preferred = _pick_win_assets(rel.get('assets', []))
                        for a in preferred:
                            url = a.get('browser_download_url')
                            if not url:
                                continue
                            sources.append({
                                'name': f'UGENE官方源#{prio}',
                                'url': url,
                                'priority': prio,
                                'location': 'GitHub',
                                'timeout': 45,
                                'description': 'GitHub Releases 资产'
                            })
                            prio += 1
                    self.unified_logger.log_network(api_url, 'GET', getattr(resp, 'status', 200), 0)
            except Exception as e:
                self.unified_logger.log_error('UGENE下载源', f'获取Releases列表失败: {e}', {})

        # 3) 如果 API 未获取到任何可用资产，回退到 tag 变体 + 静态候选
        # 如果 API 未获取到任何可用资产，回退到静态候选列表
        if not sources:
            # 尝试 tag 变体：v{ver}, {ver} （包含 1.xx 形式）
            tag_variants: List[str] = []
            for ver in normalized_variants:
                tag_variants.extend([f'v{ver}', f'{ver}'])
            bases = [f'https://github.com/ugeneunipro/ugene/releases/download/{tag}' for tag in tag_variants]
            if os.name == 'nt':
                candidate_names: List[str] = []
                for ver in normalized_variants:
                    candidate_names.extend([
                        # 历史 GitHub 命名
                        f'ugene-{ver}-win-x86-64.zip',
                        f'ugene-{ver}-windows-x86_64.zip',
                        f'ugene-{ver}-windows-x86_64-portable.zip',
                        f'UGENEDesktop-{ver}-win-x86_64.zip',
                        f'UGENEDesktop-{ver}-win-qt6-x86_64.zip',
                        f'UGENEDesktop-{ver}-windows-qt6-x86_64.zip',
                        f'UGENE-{ver}-win-x86-64.zip',
                        # 更宽松大小写与分隔
                        f'UGENEDesktop-{ver}-Windows-x86_64.zip',
                        f'ugene-{ver}-Windows-x86_64.zip',
                        f'ugene-{ver}-win-qt6-x86_64.zip',
                    ])
            else:
                candidate_names = [
                    f'ugene-{version}-linux-x86-64.tar.gz',
                    f'ugene-{version}-x86_64.AppImage',
                ]
            prio = 1
            for base in bases:
                for name in candidate_names:
                    sources.append({
                        'name': f'UGENE官方源#{prio}',
                        'url': f'{base}/{name}',
                        'priority': prio,
                        'location': 'GitHub',
                        'timeout': 45,
                        'description': 'UGENE官方GitHub发布（静态候选）'
                    })
                    prio += 1

        self.unified_logger.log_runtime(f"UGENE下载源: {sources[0]['url']}")
        return sources

    def check_dependencies(self) -> Dict[str, bool]:
        """检查UGENE依赖项"""
        dependencies = {}

        # UGENE是独立软件，无特殊依赖
        dependencies['system'] = True

        return dependencies

    def install(self, progress_callback: Optional[Callable[[str, int], None]] = None) -> bool:
        """安装UGENE"""
        try:
            # 1. 检查依赖
            if progress_callback:
                progress_callback("检查系统依赖...", 5)

            deps = self.check_dependencies()
            self.unified_logger.log_installation('UGENE', '依赖检查', '完成', deps)

            # 2. 准备目录
            if progress_callback:
                progress_callback("准备安装目录...", 10)

            self.install_base.mkdir(exist_ok=True)
            self.temp_dir.mkdir(exist_ok=True)

            # 清理旧安装
            if self.install_dir.exists():
                shutil.rmtree(self.install_dir)
                self.unified_logger.log_installation('UGENE', '清理旧版本', '完成')

            # 3. 下载文件
            if progress_callback:
                progress_callback("开始下载UGENE...", 15)

            current_version = self._cached_metadata.get('version', '52.1') if self._cached_metadata else '52.1'
            zip_path = self.temp_dir / f"ugene-{current_version}-win-x86-64.zip"

            self.unified_logger.log_installation('UGENE', '确定版本', '成功', {
                'target_version': current_version,
                'download_file': str(zip_path)
            })

            sources = self.get_download_sources()
            try:
                self.unified_logger.log_runtime(
                    f"UGENE下载源候选: {[s.get('url') for s in sources]}"
                )
            except Exception:
                pass

            # 使用智能下载器
            def download_progress(status, percent):
                if percent >= 0:
                    # 下载占总进度的60% (15% -> 75%)
                    total_percent = 15 + int(percent * 0.6)
                    if progress_callback:
                        progress_callback(status, total_percent)

            success = self.downloader.download_with_fallback(
                sources,
                zip_path,
                download_progress
            )

            if not success:
                self.unified_logger.log_error('UGENE安装', '下载失败', {
                    'candidates': [s.get('url') for s in sources]
                })
                if progress_callback:
                    progress_callback("下载失败", -1)
                return False

            self.unified_logger.log_installation('UGENE', '下载', '完成', {
                'file_size': zip_path.stat().st_size if zip_path.exists() else 0
            })

            # 4. 解压安装
            if progress_callback:
                progress_callback("正在解压安装包...", 80)

            success = self._extract_archive(zip_path, self.install_base)
            if not success:
                self.unified_logger.log_error('UGENE解压', "解压失败")
                if progress_callback:
                    progress_callback("解压失败", -1)
                return False

            # 处理解压后的目录
            try:
                extracted_dirs = [d for d in self.install_base.iterdir()
                                if d.is_dir() and 'ugene' in d.name.lower()]
                if extracted_dirs:
                    actual_dir = extracted_dirs[0]
                    if actual_dir != self.install_dir:
                        if self.install_dir.exists():
                            shutil.rmtree(self.install_dir)
                        actual_dir.rename(self.install_dir)
                    self.unified_logger.log_installation('UGENE', '目录处理', '成功', {
                        'install_dir': str(self.install_dir)
                    })
                else:
                    self.unified_logger.log_error('UGENE解压', '未找到解压的UGENE目录')
                    if progress_callback:
                        progress_callback("解压目录未找到", -1)
                    return False
            except Exception as e:
                self.unified_logger.log_error('UGENE目录处理', f"处理失败: {e}")
                if progress_callback:
                    progress_callback("目录处理失败", -1)
                return False

            # 5. 验证安装
            if progress_callback:
                progress_callback("验证安装...", 95)

            if not self.verify_installation():
                self.unified_logger.log_error('UGENE安装', '验证失败')
                if progress_callback:
                    progress_callback("安装验证失败", -1)
                return False

            # 6. 清理临时文件
            try:
                zip_path.unlink()
                self.unified_logger.log_installation('UGENE', '清理临时文件', '完成')
            except:
                pass

            if progress_callback:
                progress_callback("UGENE安装完成", 100)

            self.unified_logger.log_installation('UGENE', '安装完成', '成功', {
                'install_path': str(self.install_dir),
                'executable': str(self.exe_path)
            })
            return True

        except Exception as e:
            error_msg = f"UGENE安装失败: {e}"
            self.unified_logger.log_error('UGENE安装', error_msg)
            if progress_callback:
                progress_callback(error_msg, -1)
            return False

    def verify_installation(self) -> bool:
        """验证UGENE是否已安装"""
        self.unified_logger.log_runtime(f"开始验证UGENE安装: {self.install_dir}")

        # 1. 检查安装目录
        if not self.install_dir.exists():
            self.unified_logger.log_runtime(f"UGENE验证失败: 安装目录不存在 - {self.install_dir}")
            return False

        self.unified_logger.log_runtime(f"✓ 安装目录存在: {self.install_dir}")

        # 2. 检查可执行文件（考虑不同发布包中的路径差异，如 bin/ugeneui.exe）
        if not self.exe_path.exists():
            # 尝试在目录中自动搜索并修正exe路径
            candidates = []
            if os.name == 'nt':
                candidates = list(self.install_dir.rglob('ugeneui.exe')) + list(self.install_dir.rglob('ugene.exe'))
            else:
                candidates = list(self.install_dir.rglob('ugene'))
            if candidates:
                self.exe_path = candidates[0]
                self.unified_logger.log_runtime(f"✓ 自动发现可执行文件: {self.exe_path}")
            else:
                self.unified_logger.log_runtime(f"UGENE验证失败: 可执行文件不存在 - {self.exe_path}")
                return False

        self.unified_logger.log_runtime(f"✓ 可执行文件存在: {self.exe_path}")

        # 3. 验证通过
        self.unified_logger.log_runtime("✅ UGENE安装验证通过")
        return True

    def launch(self, args: Optional[List[str]] = None) -> bool:
        """启动UGENE"""
        if not self.verify_installation():
            self.unified_logger.log_error('UGENE启动', 'UGENE未安装')
            return False

        try:
            self.unified_logger.log_runtime(f"使用可执行文件: {self.exe_path}")

            # 构建启动命令
            if os.name == 'nt':
                # Windows启动
                cmd_str = f'"{self.exe_path}"'
                if args:
                    cmd_str += ' ' + ' '.join(f'"{arg}"' for arg in args)

                self.unified_logger.log_runtime(f"Windows启动命令: {cmd_str}")

                process = subprocess.Popen(
                    cmd_str,
                    shell=True,
                    cwd=str(self.install_dir)
                )
            else:
                # Linux/macOS启动
                cmd_list = [str(self.exe_path)]
                if args:
                    cmd_list.extend(args)

                self.unified_logger.log_runtime(f"Unix启动命令: {' '.join(cmd_list)}")

                process = subprocess.Popen(
                    cmd_list,
                    cwd=str(self.install_dir)
                )

            self.unified_logger.log_runtime(f"启动UGENE进程: PID {process.pid}")

            self.unified_logger.log_operation('启动UGENE', {
                'executable': str(self.exe_path),
                'working_dir': str(self.install_dir),
                'pid': process.pid
            })

            self.unified_logger.log_runtime("UGENE启动命令已执行，GUI正在初始化...")
            return True

        except Exception as e:
            self.unified_logger.log_error('UGENE启动', f"启动失败: {e}")
            return False

    def uninstall(self) -> bool:
        """卸载UGENE"""
        try:
            if self.install_dir.exists():
                shutil.rmtree(self.install_dir)
                self.unified_logger.log_installation('UGENE', '卸载', '成功')
                return True
            else:
                self.unified_logger.log_runtime("UGENE未安装，无需卸载")
                return True
        except Exception as e:
            self.unified_logger.log_error('UGENE卸载', f"卸载失败: {e}")
            return False

    def _extract_archive(self, archive_path: Path, extract_to: Path) -> bool:
        """解压文件"""
        import shutil

        # 方法1: shutil.unpack_archive
        try:
            self.unified_logger.log_runtime("尝试使用shutil.unpack_archive解压")
            shutil.unpack_archive(str(archive_path), str(extract_to))
            self.unified_logger.log_installation('UGENE', '解压', '成功-shutil', {
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
                self.unified_logger.log_installation('UGENE', '解压', '成功-zipfile', {
                    'method': 'zipfile'
                })
                return True
        except Exception as e:
            self.unified_logger.log_runtime(f"zipfile解压失败: {e}")

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
            self.unified_logger.log_error('UGENE信息', f"获取失败: {e}")
            return None
