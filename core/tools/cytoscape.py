"""
Cytoscape 工具实现（GUI）

说明：
- 仅支持 Windows；自动下载官方发布包，自动解压/安装，点击即可启动。
- 下载源固定为 Cytoscape 官方 GitHub Releases（Windows zip 优先，exe 作为备选）。
"""
import os
import time
import stat
import shutil
import subprocess
import zipfile
import logging
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any
import sys
import json
import re
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

from .base import ToolInterface
from ..downloader import SmartDownloader
from utils.unified_logger import get_logger
from utils.path_resolver import get_path_resolver


class Cytoscape(ToolInterface):
    """
    Cytoscape (GUI) 工具实现 - 初版
    
    当前能力：
    - 元数据公开（标注为 GUI 可视化工具）
    - 支持离线 zip 包安装（将 Cytoscape*.zip 放到项目根的 temp/ 目录）
    - 启动 GUI 程序（Windows: Cytoscape.exe；Linux/macOS: cytoscape.sh）
    
    后续增强：自动在线下载并安装
    """

    _cached_metadata: Optional[Dict[str, Any]] = None

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.unified_logger = get_logger()

        # 安装路径配置
        path_resolver = get_path_resolver()
        self.install_base = path_resolver.get_install_dir()
        self.install_dir = self.install_base / "Cytoscape"
        self.temp_dir = Path("temp")

        # 可执行文件名（Windows-only）
        self.exe_name = "Cytoscape.exe"
        self.exe_path = self.install_dir / self.exe_name

        # 下载器占位（未来用于在线下载）
        self.downloader = SmartDownloader()

        self.unified_logger.log_runtime(f"Cytoscape工具初始化完成: {self.install_dir}")

    def get_metadata(self) -> Dict[str, Any]:
        # 默认元数据（版本号为占位，可在后续版本通过 API 异步更新）
        status = 'installed' if self.verify_installation() else 'available'
        self._cached_metadata = {
            'name': 'Cytoscape',
            'version': '3.10.x',
            'category': 'visualization',
            'description': 'Cytoscape 是流行的网络与通路可视化分析平台（GUI）。',
            'size': '约 400 MB',
            'requires': ['java>=11 (或使用内置运行时)'],
            'status': status,
            'homepage': 'https://cytoscape.org/',
            'documentation': 'https://manual.cytoscape.org/',
            'license': 'LGPL / Mixed (参见官网)'
        }
        return dict(self._cached_metadata)

    def get_download_sources(self) -> List[Dict[str, Any]]:
        """固定返回 Cytoscape 官方 Windows 3.10.4 下载源（zip 优先，exe 备选）"""
        sources: List[Dict[str, Any]] = []
        # 优先 Windows ZIP（统一使用我们管理的 Java 环境）
        sources.append({
            'name': 'Cytoscape 3.10.4 (Windows ZIP)',
            'url': 'https://github.com/cytoscape/cytoscape/releases/download/3.10.4/cytoscape-windows-3.10.4.zip',
            'priority': 1,
            'location': 'global',
            'timeout': 120,
            'description': 'GitHub Releases',
            'expected_size': 358549359,
            'sha256': 'f0e8ad9ec68a19e19d212a6cc8c5da0060742b6a04db080598b98832b0478924'
        })
        # 备选 Windows EXE（若 ZIP 不可用，再尝试 exe）
        sources.append({
            'name': 'Cytoscape 3.10.4 (Windows EXE)',
            'url': 'https://github.com/cytoscape/cytoscape/releases/download/3.10.4/Cytoscape_3_10_4_windows_64bit.exe',
            'priority': 2,
            'location': 'global',
            'timeout': 120,
            'description': 'GitHub Releases',
            'expected_size': 230618624,
            'sha256': '4bd1ce47281d5ca03ec3d90de6a7bc03320a7f81df81d2d6f0c5febbd7a4346b'
        })
        self.unified_logger.log_runtime('Cytoscape下载源', f"已准备固定源: {[s['url'] for s in sources]}")
        return sources

    def _fetch_latest_release(self) -> Optional[Dict[str, Any]]:
        """从 GitHub API 获取最新 Release 信息"""
        api_url = 'https://api.github.com/repos/cytoscape/cytoscape/releases/latest'
        headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'BioNexus-Cytoscape/1.2.26'
        }
        req = Request(api_url, headers=headers)
        with urlopen(req, timeout=8) as resp:
            return json.loads(resp.read().decode('utf-8'))

    def _select_asset_for_windows(self, assets: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """选择 Windows 资产：优先 .zip，如无则回退 .exe（安装器）"""
        name_url = [(a.get('name',''), a.get('browser_download_url',''), a) for a in assets]
        patterns_zip = [
            re.compile(r"(?i)windows.*\.zip$"),
            re.compile(r"(?i)win.*\.zip$"),
            re.compile(r"(?i)cytoscape.*win.*\.zip$"),
        ]
        for pat in patterns_zip:
            for n,u,a in name_url:
                if pat.search(n):
                    return a
        # 回退：允许 .exe 安装器
        patterns_exe = [
            re.compile(r"(?i)windows.*\.exe$"),
            re.compile(r"(?i)win.*\.exe$"),
            re.compile(r"(?i)cytoscape.*win.*\.exe$"),
        ]
        for pat in patterns_exe:
            for n,u,a in name_url:
                if pat.search(n):
                    return a
        return None

    def _fetch_sha256_for_asset(self, selected_asset: Dict[str, Any], all_assets: List[Dict[str, Any]]) -> Optional[str]:
        """尝试从 sha256sums.txt 或资产自带 digest 字段提取 SHA256 校验"""
        try:
            # 优先使用资产自带 digest 字段
            digest = selected_asset.get('digest') or ''
            if isinstance(digest, str) and digest.lower().startswith('sha256:'):
                return digest.split(':', 1)[1].strip()
            # 查找 sha256sums.txt
            sha_asset = None
            for a in all_assets:
                if str(a.get('name','')).lower() == 'sha256sums.txt':
                    sha_asset = a
                    break
            if not sha_asset:
                return None
            url = sha_asset.get('browser_download_url')
            if not url:
                return None
            # 下载并解析
            req = Request(url, headers={'User-Agent': 'BioNexus-Cytoscape/1.2.26'})
            with urlopen(req, timeout=10) as resp:
                text = resp.read().decode('utf-8', errors='ignore')
            target_name = selected_asset.get('name','').strip()
            for line in text.splitlines():
                # 典型行: <sha256>  <filename>
                parts = line.strip().split()
                if len(parts) >= 2 and parts[-1] == target_name:
                    return parts[0]
            return None
        except Exception:
            return None

    def check_dependencies(self) -> Dict[str, bool]:
        """检查 Cytoscape 依赖（Java）。"""
        deps: Dict[str, bool] = {'java': False, 'local_java': False}
        # 系统 Java
        try:
            result = subprocess.run(['java', '-version'], capture_output=True, text=True, timeout=5)
            deps['java'] = (result.returncode == 0)
        except Exception:
            deps['java'] = False
        # 本地缓存 Java
        try:
            from utils.path_resolver import get_path_resolver
            java_base = get_path_resolver().get_env_cache_dir() / 'java'
            deps['local_java'] = java_base.exists() and any(
                d.is_dir() and d.name.startswith('java-') for d in java_base.iterdir()
            )
        except Exception:
            deps['local_java'] = False
        return deps

    def install(self, progress_callback: Optional[Callable[[str, int], None]] = None) -> bool:
        """
        安装 Cytoscape（仅 Windows；在线 ZIP 优先，EXE 备选；全自动）。
        """
        try:
            if progress_callback:
                progress_callback("准备安装目录...", 10)

            self.install_base.mkdir(exist_ok=True)
            self.temp_dir.mkdir(exist_ok=True)
            self.unified_logger.log_installation('Cytoscape安装', '准备目录', '进行中', {
                'install_base': str(self.install_base),
                'install_dir': str(self.install_dir),
                'temp_dir': str(self.temp_dir)
            })

            # Windows-only 保护
            if os.name != 'nt':
                if progress_callback:
                    progress_callback("当前版本仅支持 Windows 平台安装", -1)
                return False

            # 清理旧安装（带重试与解锁，兼容Windows文件被占用的情况）
            if self.install_dir.exists():
                if not self._safe_rmtree(self.install_dir):
                    # 可能是日志文件被占用，做一次针对性清理后重试
                    try:
                        locked_log = self.install_dir / 'cytoscape_launch.log'
                        if os.name == 'nt' and locked_log.exists():
                            try:
                                subprocess.run([
                                    'powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass',
                                    '-Command', f"Remove-Item -LiteralPath '{str(locked_log)}' -Force -ErrorAction SilentlyContinue"
                                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)
                            except Exception:
                                pass
                    except Exception:
                        pass
                    # 结束可能残留的 Cytoscape/karaf 进程
                    self._terminate_cytoscape_processes()
                    # 最后重试一次；若仍失败，执行“部分清理”并继续安装（仅跳过被占用文件）
                    if not self._safe_rmtree(self.install_dir):
                        try:
                            for p in list(self.install_dir.iterdir()):
                                if p.name.lower() == 'cytoscape_launch.log':
                                    continue
                                try:
                                    if p.is_dir():
                                        shutil.rmtree(p, ignore_errors=True)
                                    else:
                                        p.unlink(missing_ok=True)
                                except Exception:
                                    pass
                            self.unified_logger.log_runtime('Cytoscape安装', '部分清理完成（已跳过被占用文件）')
                        except Exception:
                            pass
                self.unified_logger.log_installation('Cytoscape安装', '清理旧安装', '完成', {'path': str(self.install_dir)})

            # Java 依赖：与 FastQC 对齐，安装阶段优先准备（17 优先，11 备选）
            try:
                deps = self.check_dependencies()
                self.unified_logger.log_installation('Cytoscape', '依赖检查', '完成', deps)
                if not deps.get('java') and not deps.get('local_java'):
                    if progress_callback:
                        progress_callback("正在自动安装 Java 环境...", 20)
                    if not self._auto_install_java(progress_callback):
                        # 不强制失败，记录并继续，由 launch 再次尝试
                        self.unified_logger.log_error('Cytoscape安装', 'Java 环境安装失败，后续启动将尝试系统 Java')
            except Exception as e:
                self.unified_logger.log_error('Cytoscape安装', f'依赖检查异常: {e}')

            # 在线下载（不再支持离线）
            sources = self.get_download_sources()
            archive_path: Optional[Path] = None
            if sources:
                # 选择目标文件名（与URL扩展名保持一致，提升识别准确性）
                first_url = sources[0].get('url', '') if isinstance(sources, list) and sources else ''
                url_l = str(first_url).lower()
                if url_l.endswith('.zip'):
                    ext = '.zip'
                elif url_l.endswith('.exe'):
                    ext = '.exe'
                else:
                    ext = '.zip'
                target = self.temp_dir / f'Cytoscape_download{ext}'
                # 确保干净下载，移除历史残留
                for suffix in ('.zip', '.exe'):
                    stale = self.temp_dir / f'Cytoscape_download{suffix}'
                    try:
                        if stale.exists():
                            stale.unlink()
                    except Exception:
                        pass
                if progress_callback:
                    progress_callback("开始下载 Cytoscape...", 30)
                ok = self.downloader.download_with_fallback(
                    sources,
                    target,
                    lambda status, pct: progress_callback and progress_callback(status, 30 + int(max(0, pct) * 0.5))
                )
                if not ok:
                    self.unified_logger.log_error('Cytoscape安装', '在线下载失败', {
                        'sources': [s.get('url') for s in sources]
                    })
                else:
                    archive_path = target
                    try:
                        self.unified_logger.log_installation('Cytoscape安装', '下载完成', '成功', {
                            'path': str(archive_path),
                            'size': archive_path.stat().st_size
                        })
                    except Exception:
                        pass

            # 如果下载失败，退出
            if archive_path is None:
                msg = "Cytoscape 下载失败（ZIP 与 EXE 均不可用）"
                self.unified_logger.log_error('Cytoscape安装', msg)
                if progress_callback:
                    progress_callback(msg, -1)
                return False

            # 规范化下载文件扩展名并识别类型
            archive_type = 'unknown'
            try:
                if zipfile.is_zipfile(str(archive_path)):
                    archive_type = 'zip'
                    # 若扩展名不是 .zip，则重命名为 .zip（避免后续误判）
                    if not str(archive_path).lower().endswith('.zip'):
                        new_path = archive_path.with_suffix('.zip')
                        try:
                            if new_path.exists():
                                new_path.unlink()
                        except Exception:
                            pass
                        archive_path.rename(new_path)
                        archive_path = new_path
                else:
                    # 粗略检测 EXE（MZ 头）
                    with open(archive_path, 'rb') as f:
                        sig = f.read(2)
                    if sig == b'MZ':
                        archive_type = 'exe'
                        if not str(archive_path).lower().endswith('.exe'):
                            new_path = archive_path.with_suffix('.exe')
                            try:
                                if new_path.exists():
                                    new_path.unlink()
                            except Exception:
                                pass
                            archive_path.rename(new_path)
                            archive_path = new_path
            except Exception as e:
                self.unified_logger.log_error('Cytoscape安装', f'识别下载文件类型失败: {e}', {'path': str(archive_path)})

            self.unified_logger.log_runtime(f"Cytoscape安装: 识别下载类型={archive_type}, 路径={archive_path}")

            # 依据识别类型选择对应源用于校验（zip 对应 sources[0]，exe 对应 sources[1]）
            try:
                src_used = None
                if archive_type == 'zip':
                    # 找到带 .zip 的源
                    for s in sources:
                        if str(s.get('url','')).lower().endswith('.zip'):
                            src_used = s; break
                elif archive_type == 'exe':
                    for s in sources:
                        if str(s.get('url','')).lower().endswith('.exe'):
                            src_used = s; break
                if src_used:
                    expected_size = src_used.get('expected_size')
                    expected_sha256 = src_used.get('sha256')
                    self.unified_logger.log_runtime(f"Cytoscape安装: 校验 expected_size={expected_size}, sha256={'yes' if expected_sha256 else 'no'}, actual={archive_path.stat().st_size}")
                    if expected_size and archive_path.exists() and archive_path.stat().st_size != int(expected_size):
                        self.unified_logger.log_error('Cytoscape安装', '文件大小校验失败', {
                            'expected': expected_size,
                            'actual': archive_path.stat().st_size,
                            'url': src_used.get('url')
                        })
                        if progress_callback:
                            progress_callback("文件大小校验失败", -1)
                        try: archive_path.unlink()
                        except Exception: pass
                        return False
                    if expected_sha256:
                        try:
                            from core.downloader import SmartDownloader
                            dl = SmartDownloader()
                            if not dl.verify_file_integrity(archive_path, expected_sha256, 'sha256'):
                                self.unified_logger.log_error('Cytoscape安装', 'SHA256 校验失败', {'url': src_used.get('url')})
                                if progress_callback:
                                    progress_callback("SHA256 校验失败", -1)
                                try: archive_path.unlink()
                                except Exception: pass
                                return False
                        except Exception as e:
                            self.unified_logger.log_error('Cytoscape安装', f'校验异常: {e}', {'path': str(archive_path)})
            except Exception:
                pass

            # 解压安装 或 执行安装器
            if archive_type == 'zip':
                if not self._extract_archive(archive_path, self.install_base):
                    if progress_callback:
                        progress_callback("解压失败", -1)
                    return False
                # 解除Windows从互联网下载的阻止标记（MOTW），避免“Access is denied.”
                if os.name == 'nt':
                    try:
                        self._unblock_windows_files(self.install_base)
                        self.unified_logger.log_installation('Cytoscape', '解除文件阻止标记', '完成', {
                            'path': str(self.install_base)
                        })
                    except Exception as e:
                        self.unified_logger.log_error('Cytoscape安装', f'解除阻止标记异常: {e}')
            elif archive_type == 'exe':
                if progress_callback:
                    progress_callback("执行安装器...", 70)
                if not self._install_from_exe(archive_path, progress_callback):
                    if progress_callback:
                        progress_callback("安装器执行失败", -1)
                    return False
            else:
                if progress_callback:
                    progress_callback("未知安装包格式/内容损坏", -1)
                return False

            # 规范化目录命名（Windows）
            # 优先以实际可执行文件所在目录为准，确保层级正确
            exe_found = None
            try:
                exec_candidates = []
                for p in self.install_base.rglob('*'):
                    nm = p.name.lower()
                    if p.is_file() and nm.startswith('cytoscape') and (nm.endswith('.exe') or nm.endswith('.bat')):
                        exec_candidates.append(p)
                if exec_candidates:
                    # 优先 EXE，其次 BAT；同类型按最近修改排序
                    exec_candidates.sort(key=lambda x: ((0 if x.suffix.lower()=='.exe' else 1), -x.stat().st_mtime))
                    exe_found = exec_candidates[0]
            except Exception:
                exe_found = None

            if exe_found is not None:
                desired_dir = exe_found.parent
                self.unified_logger.log_installation('Cytoscape', '定位可执行文件', '成功', {
                    'exe_path': str(exe_found),
                    'desired_dir': str(desired_dir)
                })
                if desired_dir != self.install_dir:
                    # 如果目标目录已存在，先尝试清理
                    if self.install_dir.exists():
                        self._safe_rmtree(self.install_dir)
                    # 将包含 exe 的目录移动为标准安装目录；若失败则采用原目录作为安装目录（回退策略）
                    moved = False
                    try:
                        shutil.move(str(desired_dir), str(self.install_dir))
                        moved = True
                    except Exception as e:
                        try:
                            desired_dir.rename(self.install_dir)
                            moved = True
                        except Exception as e2:
                            # 回退：直接采用 desired_dir 作为安装目录，避免因残留锁文件阻塞安装
                            self.unified_logger.log_error('Cytoscape目录处理', f"标准化目录失败，采用原目录: {e} / {e2}")
                            self.install_dir = desired_dir
                            self.exe_path = self.install_dir / exe_found.name
                    if moved:
                        # 迁移成功，修正 exe_path 到新目录
                        self.exe_path = self.install_dir / exe_found.name
                # 确保可执行目录存在优化的 vmoptions
                try:
                    vm_dir = self.exe_path.parent
                    vm_file = vm_dir / 'Cytoscape.vmoptions'
                    if not vm_file.exists():
                        # 优化的 JVM 参数：增加内存、禁用更新检查、优化 GC
                        vm_defaults = (
                            '-Xms2048M\n'
                            '-Xmx2048M\n'
                            '-Djdk.util.zip.disableZip64ExtraFieldValidation=true\n'
                            '-Dcytoscape.init.disable.version.check=true\n'
                            '-Dcytoscape.init.disable.update.check=true\n'
                            '-XX:+UseG1GC\n'
                            '-XX:MaxGCPauseMillis=200\n'
                        )
                        vm_file.write_text(vm_defaults, encoding='utf-8')
                        self.unified_logger.log_runtime(f"已在执行目录创建优化的 vmoptions: {vm_file}")
                except Exception:
                    pass
            else:
                # 回退：按目录名包含 cytoscape 选择顶层目录
                extracted_dirs = [d for d in self.install_base.iterdir() if d.is_dir() and 'cytoscape' in d.name.lower()]
                if extracted_dirs:
                    actual_dir = extracted_dirs[0]
                    if actual_dir != self.install_dir:
                        if self.install_dir.exists():
                            self._safe_rmtree(self.install_dir)
                        try:
                            actual_dir.rename(self.install_dir)
                        except Exception:
                            # 回退：直接采用actual_dir
                            self.install_dir = actual_dir

            # 启动文件可能位于子目录，尝试矫正 exe_path（支持 .exe/.bat）
            if not self.exe_path.exists():
                # 广泛搜索 cytoscape 启动文件
                candidate = None
                cand = []
                for p in self.install_dir.rglob('*'):
                    nm = p.name.lower()
                    if p.is_file() and nm.startswith('cytoscape') and (nm.endswith('.exe') or nm.endswith('.bat')):
                        cand.append(p)
                if cand:
                    cand.sort(key=lambda x: ((0 if x.suffix.lower()=='.exe' else 1), -x.stat().st_mtime))
                    candidate = cand[0]
                if candidate:
                    self.exe_path = candidate
                    self.unified_logger.log_installation('Cytoscape', '设置可执行路径', '成功', {
                        'exe_path': str(self.exe_path)
                    })
                else:
                    self.unified_logger.log_error('Cytoscape安装', '未找到 Cytoscape 启动文件(.exe/.bat)')

            if progress_callback:
                progress_callback("验证安装...", 90)

            if not self.verify_installation():
                if progress_callback:
                    progress_callback("安装验证失败", -1)
                return False

            # 创建 Windows 启动包装脚本，保持与 FastQC 一致的启动模式
            try:
                self._create_windows_launcher()
            except Exception:
                pass

            # 在安装目录下准备 jre 目录，指向包含 jdk.unsupported.desktop 的 JDK
            try:
                if os.name == 'nt':
                    from utils.path_resolver import get_path_resolver
                    java_base = get_path_resolver().get_env_cache_dir() / 'java'
                    target = None

                    if java_base.exists():
                        # 优先 jdk-23/22/21（必须包含 jdk.unsupported.desktop 模块）
                        for name in ('jdk-23', 'jdk-22', 'jdk-21', 'java-23', 'java-22', 'java-21'):
                            cand = java_base / name
                            if cand.exists() and (cand / 'bin').exists():
                                # 验证是否包含所需模块
                                java_exe = cand / 'bin' / 'java.exe'
                                if java_exe.exists():
                                    try:
                                        pr = subprocess.run(
                                            [str(java_exe), '--list-modules'],
                                            capture_output=True, text=True, timeout=8
                                        )
                                        if 'jdk.unsupported.desktop' in (pr.stdout or '') + (pr.stderr or ''):
                                            target = cand
                                            break
                                    except Exception:
                                        pass

                    # 如果本地没有满足要求的 JDK，尝试使用系统 JDK 21
                    if not target:
                        for pf in (os.environ.get('ProgramFiles'), os.environ.get('ProgramFiles(x86)')):
                            if not pf:
                                continue
                            base = Path(pf)
                            patterns = [
                                base / 'Eclipse Adoptium' / 'jdk-21*',
                                base / 'Java' / 'jdk-21*',
                                base / 'Microsoft' / 'jdk-21*',
                            ]
                            for pat in patterns:
                                try:
                                    if not pat.parent.exists():
                                        continue
                                    for p in pat.parent.glob(pat.name):
                                        java_exe = p / 'bin' / 'java.exe'
                                        if java_exe.exists():
                                            try:
                                                pr = subprocess.run(
                                                    [str(java_exe), '--list-modules'],
                                                    capture_output=True, text=True, timeout=8
                                                )
                                                if 'jdk.unsupported.desktop' in (pr.stdout or '') + (pr.stderr or ''):
                                                    target = p
                                                    break
                                            except Exception:
                                                pass
                                    if target:
                                        break
                                except Exception:
                                    pass
                            if target:
                                break

                    if target:
                        jre_dir = self.install_dir / 'jre'
                        if jre_dir.exists():
                            try:
                                subprocess.run(
                                    ['cmd', '/c', 'rmdir', '/Q', str(jre_dir)],
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=8
                                )
                            except Exception:
                                pass
                        # 使用目录联接，避免复制整个 JDK
                        try:
                            subprocess.run(
                                ['cmd', '/c', 'mklink', '/J', str(jre_dir), str(target)],
                                cwd=str(self.install_dir),
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=8
                            )
                            self.unified_logger.log_runtime(f"Cytoscape 安装: jre 关联到 {target}")
                        except Exception as e:
                            # 回退：不阻塞安装
                            self.unified_logger.log_error('Cytoscape安装', f'创建 jre 目录联接失败: {e}')
                    else:
                        self.unified_logger.log_error(
                            'Cytoscape安装',
                            '未找到包含 jdk.unsupported.desktop 的 JDK，Cytoscape 可能无法启动'
                        )
            except Exception as e:
                self.unified_logger.log_error('Cytoscape安装', f'jre 联接创建异常: {e}')

            # 确保存在 Cytoscape.vmoptions（避免启动脚本告警，使用优化配置）
            try:
                vm_file = self.install_dir / 'Cytoscape.vmoptions'
                if not vm_file.exists():
                    # 优化的 JVM 参数：
                    # - 增加堆内存到 2GB（加速 OSGi 容器初始化）
                    # - 禁用 ZIP64 校验
                    # - 禁用自动更新检查（加速启动）
                    # - 优化 GC 参数
                    vm_defaults = (
                        '-Xms2048M\n'
                        '-Xmx2048M\n'
                        '-Djdk.util.zip.disableZip64ExtraFieldValidation=true\n'
                        '-Dcytoscape.init.disable.version.check=true\n'
                        '-Dcytoscape.init.disable.update.check=true\n'
                        '-XX:+UseG1GC\n'
                        '-XX:MaxGCPauseMillis=200\n'
                    )
                    vm_file.write_text(vm_defaults, encoding='utf-8')
                    self.unified_logger.log_runtime(f"已创建优化的 Cytoscape.vmoptions: {vm_file}")
            except Exception as e:
                self.unified_logger.log_error('Cytoscape安装', f'创建 vmoptions 失败: {e}')

            if progress_callback:
                progress_callback("Cytoscape 安装完成", 100)
            return True

        except Exception as e:
            self.unified_logger.log_error('Cytoscape安装', f"异常: {e}")
            if progress_callback:
                progress_callback(f"安装失败: {e}", -1)
            return False

    def uninstall(self) -> bool:
        try:
            # 仅允许删除我们管理的安装路径（位于 install_base 下）
            try:
                self.install_dir.resolve().relative_to(self.install_base.resolve())
                is_managed = True
            except Exception:
                is_managed = False
            if is_managed and self.install_dir.exists():
                # 尝试终止相关进程，减少 WinError 32 的概率
                self._terminate_cytoscape_processes()
                if not self._safe_rmtree(self.install_dir):
                    # 再尝试一次，并忽略残留的日志文件
                    try:
                        locked_log = self.install_dir / 'cytoscape_launch.log'
                        if locked_log.exists():
                            try:
                                # 尝试用 PowerShell 强制删除（即使被占用也尽量释放句柄）
                                subprocess.run([
                                    'powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass',
                                    '-Command', f"Remove-Item -LiteralPath '{str(locked_log)}' -Force -ErrorAction SilentlyContinue"
                                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)
                            except Exception:
                                pass
                    except Exception:
                        pass
                    # 最后一次尝试
                    self._safe_rmtree(self.install_dir)
                self.unified_logger.log_installation('Cytoscape卸载', '删除目录', '成功', {'path': str(self.install_dir)})
            else:
                self.unified_logger.log_runtime('Cytoscape卸载', f'非托管路径或不存在，跳过: {self.install_dir}')
            return True
        except Exception as e:
            self.unified_logger.log_error('Cytoscape卸载', f'异常: {e}')
            return False

    def verify_installation(self) -> bool:
        try:
            if os.name != 'nt':
                self.unified_logger.log_runtime('Cytoscape验证', '非Windows平台，视为未安装')
                return False
            # 首先检查托管路径（install_base 下）
            if self.install_dir.exists():
                if self.exe_path.exists():
                    self.unified_logger.log_runtime('Cytoscape验证', f'检测到可执行文件: {self.exe_path}')
                    return True
                try:
                    # 广泛匹配 Cytoscape 启动文件（.exe/.bat），优先 EXE
                    candidates = []
                    for p in self.install_dir.rglob('*'):
                        nm = p.name.lower()
                        if p.is_file() and nm.startswith('cytoscape') and (nm.endswith('.exe') or nm.endswith('.bat')):
                            candidates.append(p)
                    if candidates:
                        candidates.sort(key=lambda x: ((0 if x.suffix.lower()=='.exe' else 1), -x.stat().st_mtime))
                        maybe = candidates[0]
                        self.unified_logger.log_runtime('Cytoscape验证', f'搜索到可执行文件: {maybe}')
                        self.exe_path = maybe
                        return True
                except Exception:
                    pass

            # 仅使用托管路径（installed_tools）作为安装判定，避免误用系统安装
            
            # 全部未找到，记录目录结构以便排障
            try:
                sample = [p.name for p in self.install_dir.iterdir()][:10] if self.install_dir.exists() else []
            except Exception:
                sample = []
            self.unified_logger.log_error('Cytoscape验证', '未找到可执行文件', {
                'install_dir': str(self.install_dir),
                'sample': sample
            })
            return False
        except Exception as e:
            self.unified_logger.log_error('Cytoscape验证', f'异常: {e}')
            return False

    def _search_system_install(self) -> Optional[Path]:
        """在常见系统路径查找 Cytoscape.exe（用于 .exe 安装器未装入托管路径的情况）"""
        try:
            candidates = []
            # Program Files (x64/x86)
            for env_key in ('ProgramFiles', 'ProgramFiles(x86)'):
                base = os.environ.get(env_key)
                if base:
                    base_path = Path(base)
                    # 典型：Cytoscape_v3.10.2、Cytoscape_v3.*、Cytoscape*
                    patterns = [
                        base_path / 'Cytoscape' / 'Cytoscape.exe',
                        base_path / 'Cytoscape' / 'bin' / 'Cytoscape.exe',
                    ]
                    # 深度 2 的递归搜索，避免过慢
                    try:
                        for p in base_path.glob('Cytoscape*/Cytoscape.exe'):
                            candidates.append(p)
                        for p in base_path.glob('Cytoscape*/bin/Cytoscape.exe'):
                            candidates.append(p)
                    except Exception:
                        pass
                    for p in patterns:
                        if p.exists():
                            candidates.append(p)
            # Local AppData (部分安装器可能安装到当前用户路径)
            for env_key in ('LOCALAPPDATA',):
                base = os.environ.get(env_key)
                if base:
                    base_path = Path(base)
                    # 常见布局：%LOCALAPPDATA%\Programs\Cytoscape\Cytoscape.exe 或 %LOCALAPPDATA%\Cytoscape*\Cytoscape.exe
                    try:
                        for p in (base_path / 'Programs').glob('Cytoscape*/Cytoscape.exe'):
                            candidates.append(p)
                    except Exception:
                        pass
                    try:
                        for p in base_path.glob('Cytoscape*/Cytoscape.exe'):
                            candidates.append(p)
                        for p in base_path.glob('Cytoscape*/bin/Cytoscape.exe'):
                            candidates.append(p)
                    except Exception:
                        pass
            # 返回最新修改时间的一个
            if candidates:
                candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
                return candidates[0]
            return None
        except Exception:
            return None

    def launch(self, args: Optional[List[str]] = None) -> bool:
        try:
            if os.name != 'nt':
                self.unified_logger.log_error('Cytoscape启动', '仅支持 Windows 平台')
                return False
            if not self.verify_installation():
                # 兜底：尝试识别系统级安装并生成包装器
                sys_exe = None
                try:
                    sys_exe = self._search_system_install()
                except Exception:
                    sys_exe = None
                if sys_exe and sys_exe.exists():
                    try:
                        self._create_windows_launcher(external_exe=sys_exe)
                        self.exe_path = sys_exe
                        self.unified_logger.log_runtime(f"Cytoscape启动: 使用系统安装路径 {sys_exe}")
                    except Exception as e:
                        self.unified_logger.log_error('Cytoscape启动', f'系统安装包装器创建失败: {e}')
                else:
                    self.unified_logger.log_error('Cytoscape启动', '未安装或缺少可执行文件')
                    return False
            # 使用与 FastQC 一致的隔离环境策略：仅将本地Java加入PATH，不做目录联接/复制
            env = self._get_isolated_java_env()
            # 清理潜在的调试变量，避免 bat 停顿
            env.pop('CY_DEBUG_START', None)

            # Windows: 直接启动 EXE 或 BAT
            # 始终通过包装脚本启动，保持一致的可移植性
            # 无论是否存在都重写一遍，确保最新适配逻辑生效
            self._create_windows_launcher()
            launcher = self.install_dir / 'run_cytoscape.bat'
            launcher_lower = launcher.name.lower()
            cwd = str(self.install_dir)
            self.unified_logger.log_runtime(
                f"Cytoscape 启动准备: launcher={launcher}, exists={launcher.exists()}, cwd={cwd}, args={args or []}"
            )

            # 记录当前 Java 版本与模块信息用于排错
            precheck_lines = []
            try:
                ver = subprocess.run(['java','-version'], env=env, capture_output=True, text=True, timeout=6)
                vline = f"java -version stderr={ver.stderr.strip()} stdout={ver.stdout.strip()}"
                self.unified_logger.log_runtime(f"Cytoscape 启动: {vline}")
                precheck_lines.append(vline)
                mods = subprocess.run(['java','--list-modules'], env=env, capture_output=True, text=True, timeout=6)
                has_mod = 'jdk.unsupported.desktop' in ((mods.stdout or '') + (mods.stderr or ''))
                mline = f"jdk.unsupported.desktop={'yes' if has_mod else 'no'}"
                self.unified_logger.log_runtime(f"Cytoscape 启动: {mline}")
                precheck_lines.append(mline)
            except Exception as e:
                self.unified_logger.log_error('Cytoscape启动', f'Java自检异常: {e}')
            # 如果选择了JAVA_HOME，则创建/更新jre联接，确保bat优先使用正确的JDK
            try:
                if os.name == 'nt':
                    sel_java = env.get('JAVA_HOME')
                    if sel_java:
                        jre_dir = self.install_dir / 'jre'
                        # 删除旧的联接（可能指向错误的 Java 版本）
                        if jre_dir.exists():
                            try:
                                if jre_dir.is_symlink() or jre_dir.is_dir():
                                    # 尝试删除联接/目录
                                    subprocess.run(
                                        ['cmd', '/c', 'rmdir', '/Q', str(jre_dir)],
                                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=8
                                    )
                            except Exception:
                                pass
                        # 创建新的联接
                        if not jre_dir.exists():
                            try:
                                subprocess.run(
                                    ['cmd', '/c', 'mklink', '/J', str(jre_dir), sel_java],
                                    cwd=str(self.install_dir),
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=8
                                )
                                self.unified_logger.log_runtime(f"Cytoscape 启动: 创建 jre 联接 -> {sel_java}")
                            except Exception as e:
                                self.unified_logger.log_error('Cytoscape启动', f'创建jre联接失败: {e}')
            except Exception:
                pass

            # 将子进程输出重定向到会话日志目录，避免锁定安装目录文件
            log_fh = None
            try:
                try:
                    log_dir = self.unified_logger.log_dir  # UnifiedLogger 会话日志目录
                except Exception:
                    log_dir = Path('logs')
                log_dir.mkdir(parents=True, exist_ok=True)
                launch_log = log_dir / 'cytoscape_launch.log'
                log_fh = open(launch_log, 'a', encoding='utf-8', errors='ignore')
                # 写入启动头信息，帮助诊断环境与命令
                header = (
                    f"\n==== Cytoscape Launch @ {time.strftime('%Y-%m-%d %H:%M:%S')} ===="
                    f"\nCWD: {cwd}\nLauncher: {launcher}\nJAVA_HOME: {env.get('JAVA_HOME','(unset)')}\n"
                )
                try:
                    log_fh.write(header)
                    if precheck_lines:
                        for line in precheck_lines:
                            log_fh.write(line + "\n")
                    # 记录 where java 与 PATH 开头片段，辅助确认 java 解析顺序
                    try:
                        w = subprocess.run(['where','java'], env=env, capture_output=True, text=True, timeout=6, shell=True)
                        log_fh.write(f"where java:\n{(w.stdout or '').strip()}\n")
                    except Exception:
                        pass
                    log_fh.flush()
                except Exception:
                    pass
            except Exception:
                log_fh = subprocess.DEVNULL

            if not launcher.exists():
                self.unified_logger.log_error('Cytoscape启动', '启动文件不存在', {
                    'launcher': str(launcher), 'cwd': cwd
                })
                return False

            # 修正启动脚本中的 start 调用为 call，避免新开控制台窗口并确保输出可被重定向
            try:
                txt = launcher.read_text(encoding='utf-8')
                changed = txt
                # 原生 exe 行
                changed = changed.replace('start "" "%HERE%Cytoscape.exe" %*', 'call "%HERE%Cytoscape.exe" %*')
                # 直接 bat 行
                changed = changed.replace('start "" /D "%HERE%" "%HERE%cytoscape.bat" %*', 'pushd "%HERE%"\n  call "%HERE%cytoscape.bat" %*\n  popd')
                changed = changed.replace('start "" /D "%HERE%" "%HERE%bin\\cytoscape.bat" %*', 'pushd "%HERE%"\n  call "%HERE%bin\\cytoscape.bat" %*\n  popd')
                changed = changed.replace('start "" /D "%HERE%" "%HERE%framework\\bin\\cytoscape.bat" %*', 'pushd "%HERE%"\n  call "%HERE%framework\\bin\\cytoscape.bat" %*\n  popd')
                # 递归搜索行
                changed = changed.replace('start "" /D "%%~dpF" "%%F" %*', 'pushd "%%~dpF"\n  call "%%F" %*\n  popd')
                if changed != txt:
                    launcher.write_text(changed, encoding='utf-8')
                    self.unified_logger.log_runtime("Cytoscape 启动: 已将 run_cytoscape.bat 中 start 改为 call")
            except Exception as e:
                self.unified_logger.log_error('Cytoscape启动', f'修正启动脚本失败: {e}')

            # 通过 BAT 启动（GUI 工具），隐藏控制台并将输出重定向到日志文件
            cmd_list = [
                'cmd.exe', '/c', 'call', launcher.name
            ]
            self.unified_logger.log_runtime(f"Cytoscape 启动(BAT): cmd={' '.join(cmd_list)}, cwd={cwd}")

            # Windows: 隐藏命令行窗口
            creationflags = 0
            startupinfo = None
            if os.name == 'nt':
                try:
                    import subprocess as sp
                    creationflags = getattr(sp, 'CREATE_NO_WINDOW', 0)
                    startupinfo = sp.STARTUPINFO()
                    startupinfo.dwFlags |= sp.STARTF_USESHOWWINDOW
                    startupinfo.wShowWindow = 0  # SW_HIDE
                except Exception:
                    creationflags = 0
                    startupinfo = None

            subprocess.Popen(
                cmd_list,
                cwd=cwd,
                env=env,
                stdout=log_fh if log_fh else subprocess.DEVNULL,
                stderr=log_fh if log_fh else subprocess.DEVNULL,
                shell=False,
                creationflags=creationflags,
                startupinfo=startupinfo,
            )

            # 立即刷新日志头（文件句柄可关闭，子进程句柄已继承）
            try:
                if log_fh and log_fh is not subprocess.DEVNULL:
                    log_fh.flush()
                    log_fh.close()
            except Exception:
                pass
            
            self.unified_logger.log_runtime("Cytoscape 启动命令已执行，GUI 正在初始化...")
            return True
        except Exception as e:
            self.unified_logger.log_error('Cytoscape启动', f"启动失败: {e}")
            return False

    def _get_isolated_java_env(self) -> Dict[str, str]:
        """构建隔离的Java运行环境。

        优先使用本地 envs_cache/java 下包含 jdk.unsupported.desktop 模块的 JRE（21/22/23）：
        - 将其 bin 目录前置到 PATH
        - 显式设置 JAVA_HOME 指向该 JRE（满足 cytoscape.bat 的校验）
        如未找到满足模块要求的本地 JRE，则回退到系统 JDK 21/22/23。
        """
        env = os.environ.copy()
        has_needed_module = False
        selected_java = None

        try:
            from utils.path_resolver import get_path_resolver
            java_base = get_path_resolver().get_env_cache_dir() / 'java'

            # Step 1: 检查本地 JDK 是否满足 jdk.unsupported.desktop 模块要求
            if java_base.exists():
                # 优先 JDK 22/23（满足 jdk.unsupported.desktop），然后 21
                prefer_names = (
                    'jdk-23', 'jdk-22', 'jdk-21', 'java-23', 'java-22', 'java-21'
                )
                for name in prefer_names:
                    jh = java_base / name
                    if jh.exists() and (jh / 'bin').exists():
                        # 使用该 JDK 的 java 可执行文件进行模块检查
                        java_exe = jh / 'bin' / ('java.exe' if os.name == 'nt' else 'java')
                        if not java_exe.exists():
                            continue
                        try:
                            pr = subprocess.run(
                                [str(java_exe), '--list-modules'],
                                capture_output=True, text=True, timeout=8
                            )
                            md = (pr.stdout or '') + (pr.stderr or '')
                            if 'jdk.unsupported.desktop' in md:
                                selected_java = jh
                                has_needed_module = True
                                self.unified_logger.log_runtime(
                                    f"Cytoscape 启动环境: 使用本地 Java {name} (包含 jdk.unsupported.desktop)"
                                )
                                break
                            else:
                                self.unified_logger.log_runtime(
                                    f"Cytoscape 启动环境: 本地 Java {name} 缺少 jdk.unsupported.desktop 模块"
                                )
                        except Exception as e:
                            self.unified_logger.log_runtime(
                                f"Cytoscape 启动环境: 检查本地 Java {name} 失败: {e}"
                            )
                            continue

                # 如果本地没有找到满足要求的 JDK，尝试安装 JDK 21/22
                if not selected_java:
                    self.unified_logger.log_runtime(
                        'Cytoscape 启动环境: 本地未找到包含 jdk.unsupported.desktop 的 JDK，尝试自动安装'
                    )
                    try:
                        from envs.runtime.java_runtime import JavaRuntime
                        jr = JavaRuntime(java_base)
                        for ver in ('22', '21'):
                            inst = jr.install_java(ver)
                            self.unified_logger.log_runtime(
                                f"Cytoscape 启动阶段 Java 安装({ver}): {inst}"
                            )
                            if inst.get('success'):
                                java_home = Path(inst.get('java_home'))
                                # 立即验证模块
                                java_exe = java_home / 'bin' / ('java.exe' if os.name == 'nt' else 'java')
                                try:
                                    pr = subprocess.run(
                                        [str(java_exe), '--list-modules'],
                                        capture_output=True, text=True, timeout=8
                                    )
                                    md = (pr.stdout or '') + (pr.stderr or '')
                                    if 'jdk.unsupported.desktop' in md:
                                        selected_java = java_home
                                        has_needed_module = True
                                        break
                                except Exception:
                                    pass
                    except Exception as e:
                        self.unified_logger.log_error(
                            'Cytoscape启动', f'启动阶段 Java 安装异常: {e}'
                        )

            # Step 2: 如果本地仍未找到，搜索系统 JDK（优先 21/22/23）
            if not selected_java:
                self.unified_logger.log_runtime(
                    'Cytoscape 启动环境: 本地未找到满足要求的 JDK，尝试使用系统 JDK（优先 21/22/23）'
                )

                system_jdks = []
                for pf in (os.environ.get('ProgramFiles'), os.environ.get('ProgramFiles(x86)')):
                    if not pf:
                        continue
                    base = Path(pf)

                    # 搜索 Eclipse Adoptium, Microsoft, Oracle 等各种 JDK
                    patterns = [
                        base / 'Eclipse Adoptium' / 'jdk-*',
                        base / 'Java' / 'jdk-*',
                        base / 'Microsoft' / 'jdk-*',
                    ]

                    for pat in patterns:
                        try:
                            if not pat.parent.exists():
                                continue
                            for p in pat.parent.glob(pat.name):
                                java_exe = p / 'bin' / ('java.exe' if os.name == 'nt' else 'java')
                                if java_exe.exists():
                                    system_jdks.append(p)
                        except Exception:
                            pass

                # 按版本优先级检查（21/22/23 优先）
                for jdk_path in sorted(system_jdks, key=lambda p: p.name, reverse=True):
                    java_exe = jdk_path / 'bin' / ('java.exe' if os.name == 'nt' else 'java')
                    try:
                        pr = subprocess.run(
                            [str(java_exe), '--list-modules'],
                            capture_output=True, text=True, timeout=8
                        )
                        md = (pr.stdout or '') + (pr.stderr or '')
                        if 'jdk.unsupported.desktop' in md:
                            selected_java = jdk_path
                            has_needed_module = True
                            self.unified_logger.log_runtime(
                                f"Cytoscape 启动环境: 使用系统 JDK {jdk_path} (包含 jdk.unsupported.desktop)"
                            )
                            break
                    except Exception:
                        continue

            # Step 3: 应用选定的 Java 到环境变量
            if selected_java:
                env['JAVA_HOME'] = str(selected_java)
                env['PATH'] = f"{str(selected_java / 'bin')}{os.pathsep}{env.get('PATH','')}"
            else:
                # 最后回退：使用系统默认 Java（但可能不满足要求）
                self.unified_logger.log_error(
                    'Cytoscape启动',
                    '未找到包含 jdk.unsupported.desktop 的 JDK，将使用系统默认 Java（可能无法启动）'
                )

        except Exception as e:
            self.unified_logger.log_error('Cytoscape启动', f'隔离Java环境构建异常: {e}')

        # 确保 TEMP/TMP 目录存在
        try:
            # 🔥 修改：使用工作目录内的temp文件夹
            tmp_dir = Path(os.getcwd()) / 'temp'
            tmp_dir.mkdir(parents=True, exist_ok=True)
            env['TEMP'] = str(tmp_dir)
            env['TMP'] = str(tmp_dir)
        except Exception:
            pass

        return env

    def _create_windows_launcher(self, external_exe: Optional[Path] = None):
        """创建 Cytoscape 的 Windows 启动包装脚本（run_cytoscape.bat）。

        如果提供 external_exe，则脚本将优先尝试该绝对路径（用于系统级安装场景）。
        """
        if os.name != 'nt':
            return
        try:
            batch_file = self.install_dir / 'run_cytoscape.bat'
            if not batch_file.parent.exists():
                batch_file.parent.mkdir(parents=True, exist_ok=True)
            # 总是写入最新的启动脚本，确保更新回退逻辑生效
            ext_line = ''
            if external_exe is not None:
                ext_path = str(external_exe)
                ext_line = (
                    f'REM 优先使用系统安装路径\n'
                    f'if exist "{ext_path}" (\n'
                    f'  start "" "{ext_path}" %*\n'
                    f'  endlocal\n'
                    f'  exit /b 0\n'
                    f')\n'
                )
            content = (
                    '@echo off\n'
                    'setlocal\n'
                    'set "HERE=%~dp0"\n'
                    f'{ext_line}'
                    'REM 首选原生 EXE\n'
                    'if exist "%HERE%Cytoscape.exe" (\n'
                    '  start "" "%HERE%Cytoscape.exe" %*\n'
                    '  endlocal\n'
                    '  exit /b 0\n'
                    ')\n'
                    'REM 依次尝试 BAT 启动脚本（不同打包布局）\n'
                    'if exist "%HERE%cytoscape.bat" (\n'
                    '  start "" /D "%HERE%" "%HERE%cytoscape.bat" %*\n'
                    '  endlocal\n'
                    '  exit /b 0\n'
                    ')\n'
                    'if exist "%HERE%bin\\cytoscape.bat" (\n'
                    '  start "" /D "%HERE%" "%HERE%bin\\cytoscape.bat" %*\n'
                    '  endlocal\n'
                    '  exit /b 0\n'
                    ')\n'
                    'if exist "%HERE%framework\\bin\\cytoscape.bat" (\n'
                    '  start "" /D "%HERE%" "%HERE%framework\\bin\\cytoscape.bat" %*\n'
                    '  endlocal\n'
                    '  exit /b 0\n'
                    ')\n'
                    'REM 递归搜索任意 cytoscape.bat（兼容带版本子目录的打包）\n'
                    'for /f "delims=" %%F in (\'dir /b /s ""%HERE%cytoscape.bat"" 2^>nul\') do (\n'
                    '  start "" /D "%%~dpF" "%%F" %*\n'
                    '  endlocal\n'
                    '  exit /b 0\n'
                    ')\n'
                    'echo [BioNexus] ERROR: Unable to locate cytoscape launcher in %HERE% >&2\n'
                    'endlocal\n'
                    'exit /b 1\n'
                )
            batch_file.write_text(content, encoding='utf-8')
            self.unified_logger.log_runtime(f"创建Windows启动器: {batch_file}")
        except Exception as e:
            self.unified_logger.log_error('Cytoscape启动', f'创建启动器失败: {e}')

    def _safe_rmtree(self, target: Path) -> bool:
        """在Windows上稳健删除目录，处理权限与占用，并带重试。"""
        try:
            if not target.exists():
                return True
            def on_rm_error(func, path, exc_info):
                try:
                    os.chmod(path, stat.S_IWRITE)
                except Exception:
                    pass
                try:
                    func(path)
                except Exception:
                    pass
            for i in range(4):
                try:
                    shutil.rmtree(target, onerror=on_rm_error)
                    return True
                except Exception as e:
                    self.unified_logger.log_runtime(f"删除目录重试({i+1}/3): {target} -> {e}")
                    time.sleep(0.5)
            return not target.exists()
        except Exception:
            return False

    def _terminate_cytoscape_processes(self) -> None:
        """尝试结束可能占用文件的 Cytoscape/karaf 相关进程（Windows）。"""
        if os.name != 'nt':
            return
        try:
            cmds = [
                ['cmd', '/c', 'taskkill', '/F', '/IM', 'cytoscape*.exe', '/T'],
                ['cmd', '/c', 'taskkill', '/F', '/IM', 'karaf*.exe', '/T'],
                # 仅针对 Cytoscape 的 javaw 进程（尽力而为，不保证一定筛选准确）
                ['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command',
                 "Get-Process javaw -ErrorAction SilentlyContinue | Where-Object { $_.Path -like '*Cytoscape*' } | Stop-Process -Force -ErrorAction SilentlyContinue"],
            ]
            for c in cmds:
                try:
                    subprocess.run(c, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)
                except Exception:
                    pass
        except Exception:
            pass

    def _auto_install_java(self, progress_callback: Optional[Callable[[str, int], None]] = None) -> bool:
        """自动安装 Java（优先 22，其次 17、11），安装到 envs_cache/java 下。"""
        try:
            from envs.runtime.java_runtime import JavaRuntime
            from utils.path_resolver import get_path_resolver
            java_base = get_path_resolver().get_env_cache_dir() / 'java'
            jr = JavaRuntime(java_base)
            for ver in ('22', '17', '11'):
                def jprog(status, pct):
                    if progress_callback and pct >= 0:
                        total = 20 + int(pct * 0.5)  # 安装阶段占比
                        progress_callback(f"Java{ver}: {status}", total)
                inst = jr.install_java(ver, jprog)
                self.unified_logger.log_runtime(f"Cytoscape Java 安装结果({ver}): {inst}")
                if inst.get('success'):
                    return True
            return False
        except Exception as e:
            self.unified_logger.log_error('Cytoscape安装', f'自动安装 Java 异常: {e}')
            return False

    # 内部：zip 解压（Windows）
    def _extract_archive(self, archive_path: Path, target_dir: Path) -> bool:
        try:
            if not archive_path.exists():
                return False
            name = archive_path.name.lower()
            # 以内容判断是否为zip，避免扩展名导致的误判
            try:
                if zipfile.is_zipfile(str(archive_path)):
                    with zipfile.ZipFile(archive_path, 'r') as zf:
                        zf.extractall(target_dir)
                    return True
            except Exception:
                pass
            if name.endswith('.zip'):
                with zipfile.ZipFile(archive_path, 'r') as zf:
                    zf.extractall(target_dir)
                return True
            # 其它格式（.exe/.dmg/.sh）不在自动解压范围
            return False
        except Exception as e:
            self.unified_logger.log_error('Cytoscape解压', f"解压失败: {e}")
            return False

    def _unblock_windows_files(self, base_dir: Path) -> None:
        """移除 Windows 从互联网下载的阻止标记（Zone.Identifier），避免执行被拒绝"""
        if os.name != 'nt':
            return
        try:
            import subprocess
            ps_cmd = [
                'powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass',
                '-Command', f"Get-ChildItem -Path '{str(base_dir)}' -Recurse | Unblock-File -ErrorAction SilentlyContinue"
            ]
            subprocess.run(ps_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30)
        except Exception:
            # 兜底：逐个尝试删除 Zone.Identifier
            try:
                for p in base_dir.rglob('*'):
                    try:
                        zi = Path(str(p) + ':Zone.Identifier')
                        if zi.exists():
                            zi.unlink(missing_ok=True)
                    except Exception:
                        pass
            except Exception:
                pass

    def _install_from_exe(self, exe_path: Path, progress_callback: Optional[Callable[[str, int], None]] = None) -> bool:
        """尝试以静默或交互方式执行 Windows 安装器 (.exe)。"""
        try:
            if not exe_path.exists():
                return False
            # 尝试若干常见静默参数；若都不生效则回退交互
            candidates = [
                [str(exe_path), '/S', f'/D={str(self.install_dir)}'],            # NSIS 常见参数
                [str(exe_path), '/quiet', f'INSTALLDIR={str(self.install_dir)}'],# 常见 MSI 包装参数
                [str(exe_path), '-q', f'-dir={str(self.install_dir)}'],          # Install4j/InstallAnywhere 类参数
                [str(exe_path)]                                                  # 交互模式
            ]
            for idx, cmd in enumerate(candidates, 1):
                try:
                    if progress_callback:
                        progress_callback(f"执行安装器 ({idx}/{len(candidates)}): {' '.join(cmd)}", 75)
                    proc = subprocess.Popen(cmd, cwd=str(exe_path.parent))
                    # 等待最多 20 分钟（大型安装包预留足够时间）
                    ret = proc.wait(timeout=1200)
                    self.unified_logger.log_installation('Cytoscape安装器', '执行完成', '成功' if ret == 0 else '返回非零', {
                        'cmd': ' '.join(cmd), 'returncode': ret
                    })
                    # 无论静默或交互，只要返回 0 先认为成功，由 verify_installation() 最终裁决
                    if ret == 0:
                        return True
                except subprocess.TimeoutExpired:
                    self.unified_logger.log_error('Cytoscape安装器', '超时', {'cmd': ' '.join(cmd)})
                    try:
                        proc.kill()
                    except Exception:
                        pass
                    continue
                except Exception as e:
                    self.unified_logger.log_error('Cytoscape安装器', f'执行异常: {e}', {'cmd': ' '.join(cmd)})
                    continue
            return False
        except Exception as e:
            self.unified_logger.log_error('Cytoscape安装器', f'异常: {e}')
            return False
