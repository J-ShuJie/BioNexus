"""
启动器实用工具
支持控制台隐藏、启动画面等功能
"""
import sys
import os
import platform
import ctypes
from typing import Optional, Callable
import logging


class ConsoleManager:
    """控制台窗口管理器"""
    
    @staticmethod
    def hide_console() -> bool:
        """
        隐藏控制台窗口
        
        Returns:
            bool: 是否成功隐藏
        """
        if platform.system() != "Windows":
            return False
            
        try:
            # 获取控制台窗口句柄
            kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
            user32 = ctypes.WinDLL('user32', use_last_error=True)
            
            # 获取当前控制台窗口
            console_window = kernel32.GetConsoleWindow()
            
            if console_window:
                # SW_HIDE = 0, 隐藏窗口
                user32.ShowWindow(console_window, 0)
                return True
            else:
                # 没有控制台窗口（可能已经是pythonw启动）
                return True
                
        except Exception as e:
            logging.warning(f"Failed to hide console: {e}")
            return False
    
    @staticmethod
    def show_console() -> bool:
        """
        显示控制台窗口（调试用）
        
        Returns:
            bool: 是否成功显示
        """
        if platform.system() != "Windows":
            return False
            
        try:
            kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
            user32 = ctypes.WinDLL('user32', use_last_error=True)
            
            console_window = kernel32.GetConsoleWindow()
            
            if console_window:
                # SW_SHOW = 5, 显示窗口
                user32.ShowWindow(console_window, 5)
                return True
                
        except Exception as e:
            logging.warning(f"Failed to show console: {e}")
            return False
    
    @staticmethod
    def is_console_attached() -> bool:
        """
        检查是否附加了控制台
        
        Returns:
            bool: 是否有控制台
        """
        if platform.system() != "Windows":
            return True  # Unix系统默认有terminal
            
        try:
            kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
            console_window = kernel32.GetConsoleWindow()
            return console_window != 0
        except:
            return False


class LaunchManager:
    """启动管理器"""
    
    def __init__(self, app_name: str = "BioNexus", version: str = "1.2.13"):
        self.app_name = app_name
        self.version = version
        self.logger = logging.getLogger(__name__)
        
    def should_hide_console(self) -> bool:
        """
        判断是否应该隐藏控制台
        
        Returns:
            bool: 是否应该隐藏
        """
        # 检查命令行参数
        if "--debug" in sys.argv or "--console" in sys.argv:
            return False
            
        # 检查环境变量
        if os.environ.get("BIONEXUS_DEBUG") == "1":
            return False
            
        # 检查是否从IDE启动（开发环境）
        if any(ide in sys.modules for ide in ['idlelib', 'IPython', 'ipykernel']):
            return False
            
        # 检查是否在调试器中
        if sys.gettrace() is not None:
            return False
            
        # 默认隐藏控制台
        return True
    
    def setup_environment(self):
        """设置运行环境"""
        # 设置工作目录为脚本所在目录
        if hasattr(sys, 'frozen'):
            # 打包后的exe
            script_dir = os.path.dirname(sys.executable)
        else:
            # Python脚本
            script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        
        os.chdir(script_dir)
        
        # 添加当前目录到Python路径
        if script_dir not in sys.path:
            sys.path.insert(0, script_dir)
        
        # 设置环境变量
        os.environ['BIONEXUS_ROOT'] = script_dir
        os.environ['BIONEXUS_VERSION'] = self.version
    
    def initialize_logging(self):
        """初始化日志系统"""
        log_dir = os.path.join(os.getcwd(), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        # 配置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(os.path.join(log_dir, 'launcher.log')),
                logging.StreamHandler() if not self.should_hide_console() else logging.NullHandler()
            ]
        )
        
        self.logger.info(f"{self.app_name} v{self.version} launcher started")
    
    def launch_application(self, hide_console: bool = True):
        """
        启动应用程序
        
        Args:
            hide_console: 是否隐藏控制台
        """
        self.setup_environment()
        self.initialize_logging()
        
        # 记录详细的启动信息
        self.logger.info(f"Python version: {sys.version}")
        self.logger.info(f"Platform: {platform.platform()}")
        self.logger.info(f"Working directory: {os.getcwd()}")
        self.logger.info(f"Executable: {sys.executable}")
        self.logger.info(f"Command line args: {sys.argv}")
        
        # Windows特定监控
        if platform.system() == "Windows":
            self._log_windows_environment()
        
        # 检查关键依赖
        self._check_dependencies()
        
        # 隐藏控制台（如果需要）
        if hide_console and self.should_hide_console():
            if ConsoleManager.hide_console():
                self.logger.info("Console hidden successfully")
            else:
                self.logger.warning("Failed to hide console")
        
        self.logger.info("Application initialization complete")
    
    def _log_windows_environment(self):
        """记录Windows环境信息"""
        try:
            import subprocess
            
            # 记录Windows版本
            try:
                result = subprocess.run(['ver'], capture_output=True, text=True, shell=True)
                if result.returncode == 0:
                    self.logger.info(f"Windows version: {result.stdout.strip()}")
            except:
                pass
            
            # 检查Python安装位置
            python_path = sys.executable
            self.logger.info(f"Python executable path: {python_path}")
            
            # 检查是否在便携式环境中
            if "runtime" in python_path.lower() or "portable" in python_path.lower():
                self.logger.info("Running in portable Python environment")
            else:
                self.logger.info("Running in system Python environment")
                
            # 记录环境变量
            important_vars = ['PATH', 'PYTHONPATH', 'PYTHON_HOME']
            for var in important_vars:
                value = os.environ.get(var, 'Not set')
                if var == 'PATH':
                    # PATH太长，只记录前几个
                    paths = value.split(';')[:5] if value != 'Not set' else []
                    self.logger.info(f"{var}: {';'.join(paths)}...")
                else:
                    self.logger.info(f"{var}: {value}")
                    
        except Exception as e:
            self.logger.warning(f"Failed to log Windows environment: {e}")
    
    def _check_dependencies(self):
        """检查关键依赖"""
        dependencies = [
            ('PyQt5', 'PyQt5.QtWidgets'),
            ('psutil', 'psutil'),
            ('requests', 'requests')
        ]
        
        for name, module_name in dependencies:
            try:
                __import__(module_name)
                self.logger.info(f"Dependency check passed: {name}")
            except ImportError as e:
                self.logger.error(f"Dependency check failed: {name} - {e}")
                
        # 特殊检查PyQt5
        try:
            from PyQt5.QtWidgets import QApplication
            # 尝试创建临时应用（测试Qt平台）
            temp_app = QApplication.instance()
            if temp_app is None:
                # 这里不真的创建QApplication，只是测试导入
                self.logger.info("PyQt5 QApplication import successful")
            else:
                self.logger.info("PyQt5 QApplication already exists")
        except Exception as e:
            self.logger.error(f"PyQt5 QApplication test failed: {e}")
            # 记录可用的Qt平台插件
            try:
                import os
                qt_plugin_path = os.environ.get('QT_PLUGIN_PATH', 'Not set')
                self.logger.info(f"QT_PLUGIN_PATH: {qt_plugin_path}")
            except:
                pass


# 便捷函数
def auto_hide_console():
    """自动隐藏控制台（在main.py开头调用）"""
    manager = LaunchManager()
    if manager.should_hide_console():
        ConsoleManager.hide_console()


def initialize_launcher():
    """初始化启动器（在main.py开头调用）"""
    manager = LaunchManager()
    manager.launch_application(hide_console=True)


if __name__ == "__main__":
    # 测试代码
    print("Testing launcher utilities...")
    
    manager = LaunchManager()
    print(f"Should hide console: {manager.should_hide_console()}")
    print(f"Console attached: {ConsoleManager.is_console_attached()}")
    
    if input("Hide console? (y/n): ").lower() == 'y':
        if ConsoleManager.hide_console():
            print("Console should be hidden now")
            input("Press Enter to show console again...")
            ConsoleManager.show_console()
        else:
            print("Failed to hide console")