"""
辅助工具函数
提供应用程序所需的各种工具函数和系统检查功能
"""
import sys
import platform
import logging
from pathlib import Path
from typing import Tuple


def setup_logging():
    """
    设置应用程序日志系统
    配置日志格式和输出位置
    
    Returns:
        Path: 日志目录路径
    """
    # 创建logs目录 - 使用项目本地目录而非home目录
    # 这样更容易找到日志文件
    project_dir = Path(__file__).parent.parent
    log_dir = project_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # 创建带日期的日志文件
    from datetime import datetime
    log_filename = datetime.now().strftime("bionexus_%Y%m%d.log")
    log_file = log_dir / log_filename
    
    # 配置日志格式
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # 设置日志处理器
    logging.basicConfig(
        level=logging.DEBUG,  # 改为DEBUG以捕获更多信息
        format=log_format,
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # 创建应用程序专用日志器
    logger = logging.getLogger('BioNexus')
    logger.info("日志系统初始化完成")
    logger.info(f"日志文件: {log_file}")
    
    # 返回日志目录
    return log_dir


def check_system_requirements() -> Tuple[bool, str]:
    """
    检查系统要求
    确保应用程序能在当前系统上正常运行
    
    Returns:
        Tuple[bool, str]: (是否满足要求, 详细信息)
    """
    try:
        # 检查Python版本
        python_version = sys.version_info
        if python_version < (3, 6):
            return False, f"需要Python 3.6或更高版本，当前版本: {python_version.major}.{python_version.minor}"
        
        # 检查操作系统
        system = platform.system()
        if system not in ['Windows', 'Linux', 'Darwin']:
            return False, f"不支持的操作系统: {system}"
        
        # 检查PyQt5
        try:
            import PyQt5
            pyqt_version = PyQt5.QtCore.QT_VERSION_STR
        except ImportError:
            return False, "缺少PyQt5依赖，请运行: pip install PyQt5"
        
        # 检查必要的Python模块
        required_modules = ['json', 'pathlib', 'subprocess', 'threading', 'datetime']
        missing_modules = []
        
        for module in required_modules:
            try:
                __import__(module)
            except ImportError:
                missing_modules.append(module)
        
        if missing_modules:
            return False, f"缺少必要模块: {', '.join(missing_modules)}"
        
        # 检查磁盘空间（至少需要100MB）
        try:
            import shutil
            free_space = shutil.disk_usage(Path.home()).free
            if free_space < 100 * 1024 * 1024:  # 100MB
                return False, "磁盘空间不足，至少需要100MB可用空间"
        except Exception:
            # 磁盘空间检查失败不阻止程序运行
            pass
        
        # 所有检查通过
        return True, f"系统要求满足 - Python {python_version.major}.{python_version.minor}, PyQt5 {pyqt_version}, {system}"
        
    except Exception as e:
        return False, f"系统检查时发生错误: {str(e)}"


def get_system_info() -> dict:
    """
    获取系统信息
    用于调试和问题排查
    
    Returns:
        dict: 包含系统详细信息的字典
    """
    try:
        import psutil
        memory_info = psutil.virtual_memory()
        disk_info = psutil.disk_usage('/')
    except ImportError:
        memory_info = None
        disk_info = None
    
    info = {
        'platform': platform.platform(),
        'system': platform.system(),
        'architecture': platform.architecture(),
        'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        'python_executable': sys.executable,
    }
    
    if memory_info:
        info['memory_total'] = f"{memory_info.total // (1024**3)} GB"
        info['memory_available'] = f"{memory_info.available // (1024**3)} GB"
    
    if disk_info:
        info['disk_total'] = f"{disk_info.total // (1024**3)} GB"
        info['disk_free'] = f"{disk_info.free // (1024**3)} GB"
    
    try:
        import PyQt5.QtCore
        info['pyqt_version'] = PyQt5.QtCore.QT_VERSION_STR
    except ImportError:
        info['pyqt_version'] = "未安装"
    
    return info


def format_file_size(size_bytes: int) -> str:
    """
    格式化文件大小显示
    
    Args:
        size_bytes: 字节数
        
    Returns:
        str: 格式化的大小字符串，如 "1.2 MB"
    """
    if size_bytes == 0:
        return "0 B"
    
    units = ["B", "KB", "MB", "GB", "TB"]
    unit_index = 0
    size = float(size_bytes)
    
    while size >= 1024.0 and unit_index < len(units) - 1:
        size /= 1024.0
        unit_index += 1
    
    if unit_index == 0:
        return f"{int(size)} {units[unit_index]}"
    else:
        return f"{size:.1f} {units[unit_index]}"


def format_duration(seconds: int) -> str:
    """
    格式化时间长度显示
    
    Args:
        seconds: 秒数
        
    Returns:
        str: 格式化的时间字符串，如 "2小时30分钟"
    """
    if seconds < 60:
        return f"{seconds}秒"
    elif seconds < 3600:
        minutes = seconds // 60
        secs = seconds % 60
        if secs > 0:
            return f"{minutes}分{secs}秒"
        else:
            return f"{minutes}分钟"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        if minutes > 0:
            return f"{hours}小时{minutes}分钟"
        else:
            return f"{hours}小时"


def is_tool_name_valid(tool_name: str) -> bool:
    """
    验证工具名称是否有效
    
    Args:
        tool_name: 工具名称
        
    Returns:
        bool: 是否为有效的工具名称
    """
    if not tool_name or not isinstance(tool_name, str):
        return False
    
    # 检查长度
    if len(tool_name) < 1 or len(tool_name) > 50:
        return False
    
    # 检查字符（允许字母、数字、连字符、下划线）
    import re
    if not re.match(r'^[a-zA-Z0-9_-]+$', tool_name):
        return False
    
    return True


def safe_file_name(filename: str) -> str:
    """
    生成安全的文件名
    移除或替换不安全的字符
    
    Args:
        filename: 原始文件名
        
    Returns:
        str: 安全的文件名
    """
    import re
    
    # 移除或替换不安全字符
    safe_name = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # 移除首尾空格和点
    safe_name = safe_name.strip(' .')
    
    # 确保不为空
    if not safe_name:
        safe_name = "unnamed"
    
    # 限制长度
    if len(safe_name) > 200:
        safe_name = safe_name[:200]
    
    return safe_name


def create_desktop_shortcut(app_path: str, shortcut_name: str = "BioNexus Launcher") -> bool:
    """
    创建桌面快捷方式
    
    Args:
        app_path: 应用程序路径
        shortcut_name: 快捷方式名称
        
    Returns:
        bool: 是否创建成功
    """
    try:
        import os
        from pathlib import Path
        
        system = platform.system()
        
        if system == "Windows":
            # Windows快捷方式
            import winshell
            desktop = winshell.desktop()
            shortcut_path = Path(desktop) / f"{shortcut_name}.lnk"
            
            with winshell.shortcut(str(shortcut_path)) as shortcut:
                shortcut.path = app_path
                shortcut.description = "生物信息学工具管理器"
                shortcut.working_directory = str(Path(app_path).parent)
            
            return True
            
        elif system == "Linux":
            # Linux桌面文件
            desktop_dir = Path.home() / "Desktop"
            if not desktop_dir.exists():
                desktop_dir = Path.home() / ".local" / "share" / "applications"
                desktop_dir.mkdir(parents=True, exist_ok=True)
            
            desktop_file = desktop_dir / f"{shortcut_name.replace(' ', '_')}.desktop"
            
            desktop_content = f"""[Desktop Entry]
Name={shortcut_name}
Comment=生物信息学工具管理器
Exec=python3 "{app_path}"
Icon=application-x-executable
Terminal=false
Type=Application
Categories=Science;Biology;
"""
            desktop_file.write_text(desktop_content, encoding='utf-8')
            
            # 设置可执行权限
            os.chmod(desktop_file, 0o755)
            
            return True
            
        elif system == "Darwin":  # macOS
            # macOS别名（简化实现）
            desktop_dir = Path.home() / "Desktop"
            alias_path = desktop_dir / f"{shortcut_name}.command"
            
            script_content = f"""#!/bin/bash
cd "{Path(app_path).parent}"
python3 "{app_path}"
"""
            alias_path.write_text(script_content, encoding='utf-8')
            os.chmod(alias_path, 0o755)
            
            return True
        
    except Exception as e:
        logging.error(f"创建桌面快捷方式失败: {e}")
        return False
    
    return False


def get_conda_environments() -> list:
    """
    获取系统中的Conda环境列表
    
    Returns:
        list: Conda环境名称列表
    """
    import subprocess
    
    try:
        # 尝试运行conda env list命令
        result = subprocess.run(
            ['conda', 'env', 'list'], 
            capture_output=True, 
            text=True, 
            timeout=10
        )
        
        if result.returncode == 0:
            environments = []
            for line in result.stdout.split('\n'):
                line = line.strip()
                if line and not line.startswith('#'):
                    # 提取环境名称（第一列）
                    env_name = line.split()[0]
                    if env_name not in environments:
                        environments.append(env_name)
            
            return environments
    
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
        pass
    
    return []