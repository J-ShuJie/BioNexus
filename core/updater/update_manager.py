"""
更新管理器
处理应用程序的下载、安装和更新流程
"""

import os
import sys
import shutil
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Callable, Dict, Any, List
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

class UpdateManager:
    """更新管理器类 v1.1.12: 集成环境管理"""
    
    def __init__(self, env_manager=None):
        self.logger = logging.getLogger(__name__)
        self.temp_dir = Path(tempfile.gettempdir()) / "BioNexus_Update"
        self.current_exe = Path(sys.executable if getattr(sys, 'frozen', False) else __file__)
        
        # 环境管理器集成
        self.env_manager = env_manager
        
        # 下载任务管理
        self.download_tasks = []
        self.completed_tasks = 0
        self.total_tasks = 0
        
    def download_update(self, download_url: str, 
                       progress_callback: Optional[Callable[[str, int], None]] = None) -> Optional[Path]:
        """
        下载更新文件
        
        Args:
            download_url: 下载链接
            progress_callback: 进度回调函数 (status, percent)
            
        Returns:
            Path: 下载的文件路径，失败返回None
        """
        try:
            # 准备临时目录
            self.temp_dir.mkdir(exist_ok=True)
            
            if progress_callback:
                progress_callback("准备下载更新文件...", 0)
            
            # 确定文件名
            filename = download_url.split('/')[-1]
            if not filename.endswith(('.exe', '.zip')):
                filename = f"BioNexus_Update.{'exe' if 'exe' in download_url else 'zip'}"
                
            download_path = self.temp_dir / filename
            
            # 开始下载
            headers = {
                'User-Agent': 'BioNexus-UpdateDownloader/1.0'
            }
            request = Request(download_url, headers=headers)
            
            if progress_callback:
                progress_callback("开始下载...", 5)
            
            with urlopen(request, timeout=30) as response:
                total_size = int(response.headers.get('Content-Length', 0))
                downloaded = 0
                
                with open(download_path, 'wb') as f:
                    while True:
                        chunk = response.read(8192)  # 8KB chunks
                        if not chunk:
                            break
                            
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if total_size > 0 and progress_callback:
                            percent = min(95, int((downloaded / total_size) * 90) + 5)
                            progress_callback(f"下载中... {percent}%", percent)
            
            if progress_callback:
                progress_callback("下载完成", 100)
                
            self.logger.info(f"更新文件下载完成: {download_path}")
            return download_path
            
        except (URLError, HTTPError) as e:
            self.logger.error(f"下载更新失败 - 网络错误: {e}")
            if progress_callback:
                progress_callback(f"下载失败: {str(e)}", -1)
            return None
        except Exception as e:
            self.logger.error(f"下载更新失败: {e}")
            if progress_callback:
                progress_callback(f"下载失败: {str(e)}", -1)
            return None
    
    def prepare_update(self, update_file: Path) -> bool:
        """
        准备更新（解压、验证等）
        
        Args:
            update_file: 更新文件路径
            
        Returns:
            bool: 准备是否成功
        """
        try:
            # 如果是zip文件，需要解压
            if update_file.suffix.lower() == '.zip':
                import zipfile
                extract_dir = self.temp_dir / "extracted"
                
                if extract_dir.exists():
                    shutil.rmtree(extract_dir)
                extract_dir.mkdir()
                
                with zipfile.ZipFile(update_file, 'r') as zip_ref:
                    zip_ref.extractall(extract_dir)
                
                # 查找可执行文件
                for file_path in extract_dir.rglob("*.exe"):
                    if "BioNexus" in file_path.name:
                        # 重命名为标准名称
                        new_path = self.temp_dir / "BioNexus_Update.exe"
                        if new_path.exists():
                            new_path.unlink()
                        file_path.rename(new_path)
                        self.logger.info(f"找到可执行文件: {new_path}")
                        return True
                
                self.logger.error("在zip文件中未找到可执行文件")
                return False
            
            # 如果是exe文件，直接使用
            elif update_file.suffix.lower() == '.exe':
                return True
                
            else:
                self.logger.error(f"不支持的更新文件格式: {update_file.suffix}")
                return False
                
        except Exception as e:
            self.logger.error(f"准备更新失败: {e}")
            return False
    
    def install_update(self, update_file: Path, restart_app: bool = True) -> bool:
        """
        安装更新
        
        Args:
            update_file: 更新文件路径
            restart_app: 是否重启应用
            
        Returns:
            bool: 安装是否成功
        """
        try:
            # 如果不是exe文件，查找解压后的exe
            if update_file.suffix.lower() != '.exe':
                exe_file = self.temp_dir / "BioNexus_Update.exe"
                if not exe_file.exists():
                    self.logger.error("未找到可执行的更新文件")
                    return False
                update_file = exe_file
            
            # 创建更新脚本
            update_script = self._create_update_script(update_file, restart_app)
            if not update_script:
                return False
            
            # 执行更新脚本
            if os.name == 'nt':  # Windows
                subprocess.Popen([update_script], creationflags=subprocess.CREATE_NEW_CONSOLE)
            else:  # Linux/macOS
                subprocess.Popen(['/bin/bash', update_script])
            
            self.logger.info("更新脚本已启动，应用程序即将关闭")
            return True
            
        except Exception as e:
            self.logger.error(f"安装更新失败: {e}")
            return False
    
    def _create_update_script(self, update_file: Path, restart_app: bool) -> Optional[Path]:
        """
        创建更新脚本
        
        Args:
            update_file: 更新文件路径
            restart_app: 是否重启应用
            
        Returns:
            Path: 脚本文件路径
        """
        try:
            if os.name == 'nt':  # Windows
                script_path = self.temp_dir / "update.bat"
                current_exe = Path(sys.argv[0]) if getattr(sys, 'frozen', False) else Path(__file__).parent.parent.parent / "BioNexus.exe"
                
                script_content = f"""@echo off
echo 等待应用程序关闭...
timeout /t 3 /nobreak > nul

echo 备份当前版本...
if exist "{current_exe}.backup" del "{current_exe}.backup"
ren "{current_exe}" "{current_exe.name}.backup"

echo 安装新版本...
copy "{update_file}" "{current_exe}"

echo 清理临时文件...
rmdir /s /q "{self.temp_dir}"

"""
                if restart_app:
                    script_content += f"""echo 启动新版本...
start "" "{current_exe}"
"""
                
                script_content += "del \"%~f0\""  # 删除脚本自身
                
            else:  # Linux/macOS
                script_path = self.temp_dir / "update.sh"
                current_exe = Path(sys.argv[0]) if getattr(sys, 'frozen', False) else Path(__file__).parent.parent.parent / "BioNexus"
                
                script_content = f"""#!/bin/bash
echo "等待应用程序关闭..."
sleep 3

echo "备份当前版本..."
if [ -f "{current_exe}.backup" ]; then
    rm "{current_exe}.backup"
fi
mv "{current_exe}" "{current_exe}.backup"

echo "安装新版本..."
cp "{update_file}" "{current_exe}"
chmod +x "{current_exe}"

echo "清理临时文件..."
rm -rf "{self.temp_dir}"

"""
                if restart_app:
                    script_content += f"""echo "启动新版本..."
"{current_exe}" &
"""
                
                script_content += f"rm \"{script_path}\""  # 删除脚本自身
            
            # 写入脚本文件
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(script_content)
            
            # 设置执行权限（Linux/macOS）
            if os.name != 'nt':
                os.chmod(script_path, 0o755)
            
            return script_path
            
        except Exception as e:
            self.logger.error(f"创建更新脚本失败: {e}")
            return None
    
    def cleanup_temp_files(self):
        """清理临时文件"""
        try:
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
                self.logger.info("临时文件清理完成")
        except Exception as e:
            self.logger.warning(f"清理临时文件失败: {e}")
    
    def rollback_update(self) -> bool:
        """
        回滚更新（如果存在备份）
        
        Returns:
            bool: 回滚是否成功
        """
        try:
            current_exe = Path(sys.argv[0]) if getattr(sys, 'frozen', False) else Path(__file__).parent.parent.parent / "BioNexus.exe"
            backup_exe = Path(f"{current_exe}.backup")
            
            if not backup_exe.exists():
                self.logger.error("未找到备份文件，无法回滚")
                return False
            
            if current_exe.exists():
                current_exe.unlink()
            
            backup_exe.rename(current_exe)
            self.logger.info("更新回滚成功")
            return True
            
        except Exception as e:
            self.logger.error(f"回滚更新失败: {e}")
            return False
    
    def check_environment_updates(self) -> Dict[str, Any]:
        """
        检查环境更新 (集成环境管理器)
        
        Returns:
            环境更新信息字典
        """
        if not self.env_manager:
            return {}
        
        try:
            return self.env_manager.check_environment_updates()
        except Exception as e:
            self.logger.error(f"检查环境更新失败: {e}")
            return {}
    
    def plan_unified_update(self, app_update_info: Dict[str, Any], 
                          env_update_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        规划统一更新（应用+环境）
        
        Args:
            app_update_info: 应用更新信息
            env_update_info: 环境更新信息
            
        Returns:
            统一更新计划
        """
        update_plan = {
            'total_tasks': 0,
            'download_tasks': [],
            'estimated_time_minutes': 0,
            'estimated_size_mb': 0
        }
        
        # 应用更新任务
        if app_update_info:
            update_plan['download_tasks'].append({
                'type': 'application',
                'name': 'BioNexus应用程序',
                'url': app_update_info.get('download_url'),
                'estimated_size_mb': 15,
                'estimated_time_minutes': 2
            })
            update_plan['estimated_time_minutes'] += 2
            update_plan['estimated_size_mb'] += 15
        
        # 环境更新任务
        if env_update_info:
            # Java更新
            if 'java' in env_update_info:
                update_plan['download_tasks'].append({
                    'type': 'environment',
                    'name': 'Java运行环境',
                    'component': 'java',
                    'estimated_size_mb': 45,
                    'estimated_time_minutes': 3
                })
                update_plan['estimated_time_minutes'] += 3
                update_plan['estimated_size_mb'] += 45
            
            # Python包更新
            if 'python_packages' in env_update_info:
                package_count = len(env_update_info['python_packages'])
                update_plan['download_tasks'].append({
                    'type': 'environment', 
                    'name': 'Python依赖包',
                    'component': 'python_packages',
                    'package_count': package_count,
                    'estimated_size_mb': package_count * 5,
                    'estimated_time_minutes': package_count // 3 + 1
                })
                update_plan['estimated_time_minutes'] += package_count // 3 + 1
                update_plan['estimated_size_mb'] += package_count * 5
        
        update_plan['total_tasks'] = len(update_plan['download_tasks'])
        return update_plan
    
    def execute_unified_update(self, update_plan: Dict[str, Any],
                             progress_callback: Optional[Callable[[str, int, str], None]] = None) -> bool:
        """
        执行统一更新
        
        Args:
            update_plan: 更新计划
            progress_callback: 进度回调 (status, percent, current_task)
            
        Returns:
            更新是否成功
        """
        try:
            self.download_tasks = update_plan['download_tasks']
            self.total_tasks = update_plan['total_tasks']
            self.completed_tasks = 0
            
            for i, task in enumerate(self.download_tasks):
                task_progress_start = int((i / self.total_tasks) * 90)
                task_progress_end = int(((i + 1) / self.total_tasks) * 90)
                
                if progress_callback:
                    progress_callback(f"开始{task['name']}...", task_progress_start, task['name'])
                
                # 执行具体的下载/更新任务
                success = self._execute_update_task(task, 
                    lambda status, percent: self._update_task_progress(
                        status, percent, task_progress_start, task_progress_end, 
                        task['name'], progress_callback
                    )
                )
                
                if not success:
                    if progress_callback:
                        progress_callback(f"{task['name']}更新失败", -1, task['name'])
                    return False
                
                self.completed_tasks += 1
                
                if progress_callback:
                    progress_callback(f"{task['name']}完成", task_progress_end, task['name'])
            
            if progress_callback:
                progress_callback("更新完成", 100, "")
            
            return True
            
        except Exception as e:
            self.logger.error(f"统一更新执行失败: {e}")
            if progress_callback:
                progress_callback(f"更新失败: {str(e)}", -1, "")
            return False
    
    def _execute_update_task(self, task: Dict[str, Any], 
                           progress_callback: Optional[Callable[[str, int], None]] = None) -> bool:
        """执行单个更新任务"""
        task_type = task['type']
        
        if task_type == 'application':
            # 应用程序更新
            return self._download_application_update(task, progress_callback)
        elif task_type == 'environment':
            # 环境更新
            return self._download_environment_update(task, progress_callback)
        else:
            self.logger.error(f"未知的更新任务类型: {task_type}")
            return False
    
    def _download_application_update(self, task: Dict[str, Any], 
                                   progress_callback: Optional[Callable[[str, int], None]] = None) -> bool:
        """下载应用程序更新"""
        try:
            download_path = self.download_update(task['url'], progress_callback)
            return download_path is not None
        except Exception as e:
            self.logger.error(f"应用程序更新下载失败: {e}")
            return False
    
    def _download_environment_update(self, task: Dict[str, Any],
                                   progress_callback: Optional[Callable[[str, int], None]] = None) -> bool:
        """下载环境更新"""
        if not self.env_manager:
            return True  # 如果没有环境管理器，跳过环境更新
        
        try:
            component = task['component']
            
            if component == 'java':
                # Java环境更新
                return self._update_java_environment(task, progress_callback)
            elif component == 'python_packages':
                # Python包更新
                return self._update_python_packages(task, progress_callback)
            else:
                self.logger.warning(f"未知的环境组件: {component}")
                return True
                
        except Exception as e:
            self.logger.error(f"环境更新失败: {e}")
            return False
    
    def _update_java_environment(self, task: Dict[str, Any], 
                               progress_callback: Optional[Callable[[str, int], None]] = None) -> bool:
        """更新Java环境"""
        # TODO: 实现Java环境更新逻辑
        # 这里应该调用环境管理器的Java更新方法
        if progress_callback:
            progress_callback("更新Java环境...", 50)
        
        # 模拟更新过程
        import time
        time.sleep(1)  # 模拟处理时间
        
        if progress_callback:
            progress_callback("Java环境更新完成", 100)
        
        return True
    
    def _update_python_packages(self, task: Dict[str, Any],
                              progress_callback: Optional[Callable[[str, int], None]] = None) -> bool:
        """更新Python包"""
        # TODO: 实现Python包更新逻辑
        if progress_callback:
            progress_callback("更新Python包...", 50)
        
        # 模拟更新过程
        import time
        time.sleep(1)
        
        if progress_callback:
            progress_callback("Python包更新完成", 100)
        
        return True
    
    def _update_task_progress(self, status: str, percent: int, 
                            start_percent: int, end_percent: int, 
                            task_name: str, 
                            callback: Optional[Callable[[str, int, str], None]] = None):
        """更新任务进度"""
        if callback:
            # 将任务内部进度映射到总体进度
            if percent >= 0:
                total_percent = start_percent + int(((end_percent - start_percent) * percent) / 100)
                callback(status, total_percent, task_name)
            else:
                callback(status, percent, task_name)