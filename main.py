#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BioNexus Launcher 主程序入口 v1.2.13 Enhanced
生物信息学工具管理器 - Python版本

这是从HTML/JavaScript版本完整转写的Python桌面应用程序
使用PyQt5框架实现现代化的GUI界面

新特性 v1.2.13:
- 智能控制台隐藏（类似IGV模式）
- 便携式Python环境支持
- 增强的启动器功能
- 更好的用户体验

主要功能:
- 生物信息学工具的安装、启动和管理
- 工具搜索和分类筛选
- 最近使用工具快速访问
- 详细的安装进度和状态显示
- 可配置的应用设置

运行要求:
- Python 3.8+
- PyQt5
- 其他依赖见requirements.txt

使用方法:
    python main.py                 # 正常启动
    python main.py --debug         # 调试模式（显示控制台）
    python main.py --console       # 强制显示控制台
"""

# BioNexus版本信息
__version__ = "1.2.13"

import sys
import os

# ============================================================================
# 启动器增强功能 - 在导入PyQt5之前处理控制台
# ============================================================================

# 首先尝试导入启动器工具
try:
    from utils.launcher_utils import LaunchManager, ConsoleManager
    
    # 创建启动管理器
    launcher = LaunchManager("BioNexus", __version__)
    
    # 设置环境和日志
    launcher.setup_environment()
    launcher.initialize_logging()
    
    # 智能隐藏控制台（除非在调试模式）
    if launcher.should_hide_console():
        ConsoleManager.hide_console()
        
except ImportError as e:
    # 如果launcher_utils不可用，使用基础的控制台隐藏
    import platform
    if platform.system() == "Windows" and "--debug" not in sys.argv and "--console" not in sys.argv:
        try:
            import ctypes
            kernel32 = ctypes.WinDLL('kernel32')
            user32 = ctypes.WinDLL('user32')
            console_window = kernel32.GetConsoleWindow()
            if console_window:
                user32.ShowWindow(console_window, 0)  # SW_HIDE
        except:
            pass  # 静默失败，不影响主程序
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from PyQt5.QtWidgets import QApplication, QMessageBox
    from PyQt5.QtCore import Qt, QTimer
    from PyQt5.QtGui import QIcon, QFont
except ImportError as e:
    # 写入启动错误日志
    error_msg = f"PyQt5导入失败: {e}"
    try:
        import os
        from datetime import datetime
        log_dir = os.path.join(os.getcwd(), "logs")
        os.makedirs(log_dir, exist_ok=True)
        
        # 记录到启动错误日志
        with open(os.path.join(log_dir, "startup_error.log"), "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now()}] {error_msg}\n")
            f.write(f"Python版本: {sys.version}\n")
            f.write(f"工作目录: {os.getcwd()}\n")
            f.write(f"Python路径: {sys.path[:3]}\n")
            f.write("=" * 60 + "\n")
    except:
        pass
    
    # 输出用户友好的错误信息
    print("=" * 50)
    print("BioNexus 启动失败")
    print("=" * 50)
    print("错误: 缺少PyQt5依赖")
    print("请安装PyQt5: pip install PyQt5")
    print(f"详细错误: {e}")
    print()
    print("如果您使用的是BioNexus.bat启动器，")
    print("它会自动处理依赖安装问题。")
    print("请检查启动器日志：logs/launcher_debug.log")
    print("=" * 50)
    
    # 等待用户按键（如果在控制台中）
    try:
        if sys.stdin and sys.stdin.isatty():
            input("按回车键退出...")
    except:
        pass
    
    sys.exit(1)

try:
    # 首先初始化全面的日志系统
    from utils.comprehensive_logger import init_comprehensive_logging, get_comprehensive_logger, PerformanceTimer
    import traceback
    
    # 初始化增强日志系统
    comprehensive_logger = init_comprehensive_logging(__version__)
    comprehensive_logger.log_startup_phase("日志系统初始化", "全面日志系统已启动")
    
    # 设置基础日志系统（向后兼容）
    with PerformanceTimer("基础日志系统初始化"):
        from utils.helpers import setup_logging
        from utils.error_handler import initialize_error_handler
        import logging
        
        log_dir = setup_logging()
        startup_logger = logging.getLogger("BioNexus.startup")
        startup_logger.info(f"BioNexus {__version__} 启动初始化")
        comprehensive_logger.log_startup_phase("基础日志系统", "标准logging已配置")
        
        # 初始化错误处理器
        error_handler = initialize_error_handler(log_dir)
        startup_logger.info("错误处理器初始化完成")
        comprehensive_logger.log_startup_phase("错误处理器", "全局异常捕获已设置")
    
    # 然后导入其他模块
    with PerformanceTimer("主要模块导入"):
        try:
            from ui.main_window import MainWindow
            comprehensive_logger.log_module_import("ui.main_window.MainWindow", True)
        except ImportError as e:
            comprehensive_logger.log_module_import("ui.main_window.MainWindow", False, str(e))
            raise
        
        try:
            from data.config import ConfigManager
            comprehensive_logger.log_module_import("data.config.ConfigManager", True)
        except ImportError as e:
            comprehensive_logger.log_module_import("data.config.ConfigManager", False, str(e))
            raise
        
        try:
            from utils.helpers import check_system_requirements
            comprehensive_logger.log_module_import("utils.helpers.check_system_requirements", True)
        except ImportError as e:
            comprehensive_logger.log_module_import("utils.helpers.check_system_requirements", False, str(e))
            raise
        
        try:
            from utils.unified_logger import initialize_monitoring, get_monitor
            comprehensive_logger.log_module_import("utils.unified_logger", True)
        except ImportError as e:
            comprehensive_logger.log_module_import("utils.unified_logger", False, str(e))
            raise
    
    comprehensive_logger.log_startup_phase("所有模块导入", "核心模块导入完成", True)
except ImportError as e:
    error_msg = f"错误: 无法导入应用模块: {e}"
    print(error_msg)
    print("请确保所有应用文件都在正确的位置")
    
    # 使用增强日志系统记录错误
    try:
        if 'comprehensive_logger' in locals():
            comprehensive_logger.log_error("模块导入失败", error_msg, {
                'exception_type': type(e).__name__,
                'traceback': traceback.format_exc()
            })
            comprehensive_logger.log_startup_phase("模块导入", f"失败: {error_msg}", False)
        
        # 向后兼容：尝试记录到标准日志
        if 'startup_logger' in locals():
            startup_logger.error(error_msg)
            startup_logger.error(f"详细堆栈: {traceback.format_exc()}")
        
        # 如果错误处理器已初始化，也使用它记录
        if 'error_handler' in locals():
            from utils.error_handler import log_exception
            log_exception(e, "启动时导入模块失败")
    except Exception as log_error:
        # 如果所有日志系统都失败，创建紧急错误文件
        try:
            emergency_log = f"emergency_startup_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
            with open(emergency_log, "w", encoding="utf-8") as f:
                f.write(f"BioNexus {__version__} 紧急启动错误报告\n")
                f.write(f"时间: {datetime.now().isoformat()}\n")
                f.write(f"原始错误: {error_msg}\n")
                f.write(f"日志错误: {log_error}\n")
                f.write(f"完整堆栈追踪:\n{traceback.format_exc()}\n")
                f.write("=" * 60 + "\n")
            print(f"紧急错误详情已保存到 {emergency_log}")
        except:
            # 最后的措施：至少打印详细信息
            print(f"完整错误信息: {traceback.format_exc()}")
    
    sys.exit(1)
except Exception as e:
    # 捕获任何其他启动错误
    error_msg = f"启动时发生未预期错误: {e}"
    print(error_msg)
    
    try:
        if 'comprehensive_logger' in locals():
            comprehensive_logger.log_critical_error(type(e), e, sys.exc_info()[2])
        
        # 创建完整的错误报告
        emergency_log = f"critical_startup_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        with open(emergency_log, "w", encoding="utf-8") as f:
            f.write(f"BioNexus {__version__} 严重启动错误\n")
            f.write(f"时间: {datetime.now().isoformat()}\n")
            f.write(f"Python版本: {sys.version}\n")
            f.write(f"平台: {sys.platform}\n")
            f.write(f"错误类型: {type(e).__name__}\n")
            f.write(f"错误消息: {e}\n")
            f.write(f"完整堆栈追踪:\n{traceback.format_exc()}\n")
        print(f"严重错误报告已保存到 {emergency_log}")
    except:
        print(f"无法创建错误报告，完整错误信息: {traceback.format_exc()}")
    
    sys.exit(1)


class BioNexusLauncher:
    """
    BioNexus Launcher应用程序主类
    负责应用程序的初始化、启动和生命周期管理
    """
    
    def __init__(self):
        self.app = None
        self.main_window = None
        self.config_manager = None
        self.monitor = None
        self.comprehensive_logger = get_comprehensive_logger()
    
    def initialize_application(self):
        """
        初始化PyQt5应用程序
        设置应用程序属性和全局配置
        """
        try:
            # 启用高DPI支持（必须在创建QApplication之前设置）
            QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
            QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
            
            # 创建QApplication实例
            self.app = QApplication(sys.argv)
            
            # 设置应用程序属性
            self.app.setApplicationName("BioNexus Launcher")
            self.app.setApplicationVersion("1.2.9")
            self.app.setOrganizationName("BioNexus")
            self.app.setApplicationDisplayName("BioNexus Launcher")
            
            startup_logger.info("PyQt5应用程序初始化成功")
            self.comprehensive_logger.log_startup_phase("PyQt5应用程序", "初始化成功")
            
        except Exception as e:
            error_msg = f"PyQt5应用程序初始化失败: {e}"
            startup_logger.error(error_msg)
            startup_logger.error(f"详细堆栈: {traceback.format_exc()}")
            self.comprehensive_logger.log_error("PyQt5初始化失败", error_msg, {
                'exception_type': type(e).__name__,
                'traceback': traceback.format_exc()
            })
            self.comprehensive_logger.log_startup_phase("PyQt5应用程序", f"初始化失败: {error_msg}", False)
            raise
        
        # 设置应用程序图标（如果存在）
        icon_path = project_root / "resources" / "icon.png"
        if icon_path.exists():
            self.app.setWindowIcon(QIcon(str(icon_path)))
        
        # 使用系统默认字体（避免版权风险）
        # 让Windows 10/11自动选择合适的系统字体（Segoe UI + 中文回退字体）
    
    def check_dependencies(self):
        """
        检查系统依赖和运行环境
        确保应用程序能够正常运行
        """
        try:
            # 检查系统要求
            system_ok, message = check_system_requirements()
            if not system_ok:
                QMessageBox.critical(
                    None, 
                    "系统要求不满足", 
                    f"应用程序无法在当前系统上运行:\n{message}"
                )
                return False
            
            # 检查配置目录权限
            config_dir = Path.home() / ".bionexus"
            try:
                config_dir.mkdir(exist_ok=True)
                test_file = config_dir / "test_write.tmp"
                test_file.write_text("test")
                test_file.unlink()
            except Exception as e:
                QMessageBox.critical(
                    None,
                    "权限错误",
                    f"无法访问配置目录: {config_dir}\n错误: {e}"
                )
                return False
            
            return True
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            
            # 记录错误
            if 'startup_logger' in globals():
                startup_logger.error(f"依赖检查失败: {e}")
                startup_logger.error(f"堆栈追踪:\n{error_details}")
            
            if self.monitor:
                self.monitor.log_error("依赖检查失败", str(e), {'traceback': error_details})
            
            # 显示错误对话框
            QMessageBox.critical(
                None,
                "依赖检查失败",
                f"检查系统依赖时发生错误:\n{e}"
            )
            return False
    
    def create_main_window(self):
        """
        创建主窗口
        初始化所有UI组件和业务逻辑
        """
        try:
            self.main_window = MainWindow()
            return True
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            
            # 记录到启动日志
            if 'startup_logger' in globals():
                startup_logger.error(f"主窗口创建失败: {e}")
                startup_logger.error(f"堆栈追踪:\n{error_details}")
            
            # 记录到增强日志系统
            self.comprehensive_logger.log_error("主窗口创建失败", str(e), {
                'exception_type': type(e).__name__,
                'traceback': error_details
            })
            self.comprehensive_logger.log_startup_phase("主窗口创建", f"失败: {str(e)}", False)
            
            # 记录到监控系统
            if self.monitor:
                self.monitor.log_error("主窗口创建失败", str(e), {'traceback': error_details})
            
            # 保存到logs目录下的错误文件
            try:
                from datetime import datetime
                import os as os_module
                
                # 获取当前会话日志目录
                log_date = datetime.now().strftime('%Y-%m-%d')
                log_session = datetime.now().strftime('%Y%m%d_%H%M%S')
                log_dir = f"logs/{log_date}"
                
                # 尝试找到现有会话目录，或创建新的
                existing_sessions = []
                if os_module.path.exists(log_dir):
                    for item in os_module.listdir(log_dir):
                        if item.startswith('session_') and os_module.path.isdir(f"{log_dir}/{item}"):
                            existing_sessions.append(item)
                
                # 使用最新会话目录，如果没有则创建新的
                if existing_sessions:
                    session_dir = f"{log_dir}/{sorted(existing_sessions)[-1]}"
                else:
                    session_dir = f"{log_dir}/session_{log_session}"
                    os_module.makedirs(session_dir, exist_ok=True)
                
                error_file_path = f"{session_dir}/window_creation_error.log"
                
                with open(error_file_path, "w", encoding="utf-8") as f:
                    f.write(f"BioNexus {__version__} 主窗口创建错误\n")
                    f.write(f"时间: {datetime.now().isoformat()}\n")
                    f.write(f"错误: {e}\n")
                    f.write(f"类型: {type(e).__name__}\n")
                    f.write(f"详细堆栈:\n{error_details}\n")
                print(f"窗口创建错误已保存到 {error_file_path}")
            except Exception as save_error:
                # 如果保存到logs失败，回退到主目录
                try:
                    with open("window_creation_error.log", "w", encoding="utf-8") as f:
                        f.write(f"BioNexus {__version__} 主窗口创建错误\n")
                        f.write(f"错误: {e}\n")
                        f.write(f"详细堆栈:\n{error_details}\n")
                    print(f"错误文件已保存到主目录 (logs目录保存失败: {save_error})")
                except:
                    pass
            
            # 显示错误对话框（用户看到的弹窗）
            error_msg = f"创建主窗口时发生错误:\n{e}\n\n请检查应用程序文件是否完整"
            QMessageBox.critical(
                None,
                "窗口创建失败",
                error_msg
            )
            
            # 同时打印到控制台
            print(f"\n{'='*60}")
            print("主窗口创建失败")
            print(f"{'='*60}")
            print(f"错误类型: {type(e).__name__}")
            print(f"错误信息: {e}")
            print(f"{'='*60}")
            print("详细堆栈:")
            print(error_details)
            print(f"{'='*60}\n")
            
            return False
    
    def setup_error_handling(self):
        """
        设置全局错误处理
        捕获未处理的异常并显示错误信息
        """
        def handle_exception(exc_type, exc_value, exc_traceback):
            if issubclass(exc_type, KeyboardInterrupt):
                # 允许Ctrl+C正常退出
                sys.__excepthook__(exc_type, exc_value, exc_traceback)
                return
            
            # 记录错误到日志和监控系统
            import traceback
            error_msg = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
            print(f"未处理的异常:\n{error_msg}")
            
            # 记录到监控系统
            if self.monitor:
                self.monitor.log_error(
                    f"未处理异常: {exc_type.__name__}", 
                    str(exc_value),
                    {'traceback': error_msg[:500]}  # 限制长度避免过长日志
                )
                # 创建崩溃报告
                self.monitor.create_crash_report(error_msg)
            
            # 显示错误对话框
            if self.app:
                QMessageBox.critical(
                    None,
                    "程序错误",
                    f"程序遇到未处理的错误:\n\n{exc_type.__name__}: {exc_value}\n\n请查看控制台获取详细信息"
                )
        
        # 设置异常钩子
        sys.excepthook = handle_exception
    
    def run(self):
        """
        启动应用程序
        这是应用程序的主要入口点
        """
        try:
            # 1. 初始化监控系统
            print("正在初始化监控系统...")
            self.monitor = initialize_monitoring(__version__)
            
            # 记录启动开始
            if 'startup_logger' in globals():
                startup_logger.info("开始启动主应用程序")
            
            # 2. 初始化应用程序
            print("正在初始化 BioNexus Launcher...")
            self.initialize_application()
            
            # 记录启动信息
            startup_info = {
                "版本": __version__,
                "Python版本": sys.version.split()[0],
                "PyQt5版本": "已加载",
                "工作目录": os.getcwd()
            }
            self.monitor.log_startup(startup_info)
            
            # 3. 设置错误处理
            self.setup_error_handling()
            
            # 4. 检查依赖
            print("检查系统要求...")
            if not self.check_dependencies():
                self.monitor.log_error("依赖检查", "系统要求不满足")
                return 1
            
            # 5. 设置日志
            setup_logging()
            
            # 6. 创建主窗口
            print("创建主窗口...")
            if not self.create_main_window():
                self.monitor.log_error("窗口创建", "主窗口创建失败")
                return 1
            
            # 将监控实例传递给主窗口
            self.main_window.monitor = self.monitor
            
            # 7. 显示主窗口
            print("显示主窗口...")
            self.main_window.show()
            self.monitor.log_user_operation("应用启动", {"窗口": "已显示"})
            
            # 8. 启动事件循环
            print("BioNexus Launcher 启动完成")
            result = self.app.exec_()
            
            # 记录应用关闭
            self.monitor.log_shutdown()
            return result
            
        except KeyboardInterrupt:
            print("\n用户中断程序")
            if self.monitor:
                self.monitor.log_user_operation("程序中断", {"类型": "Ctrl+C"})
                self.monitor.log_shutdown()
            return 0
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"启动失败: {e}")
            print(f"详细错误:\n{error_details}")
            
            # 记录到日志文件
            if 'startup_logger' in globals():
                startup_logger.error(f"应用启动失败: {e}")
                startup_logger.error(f"堆栈追踪:\n{error_details}")
            
            # 记录到监控系统
            if self.monitor:
                self.monitor.log_error("应用启动失败", str(e), {'traceback': error_details})
                self.monitor.create_crash_report(error_details)
                self.monitor.log_shutdown()
            
            # 保存错误到logs目录
            try:
                from datetime import datetime
                import os as os_module
                
                log_date = datetime.now().strftime('%Y-%m-%d')
                log_session = datetime.now().strftime('%Y%m%d_%H%M%S')
                log_dir = f"logs/{log_date}"
                
                # 创建当前会话目录
                session_dir = f"{log_dir}/session_{log_session}"
                os_module.makedirs(session_dir, exist_ok=True)
                
                crash_file_path = f"{session_dir}/startup_crash.log"
                
                with open(crash_file_path, "w", encoding="utf-8") as f:
                    f.write(f"BioNexus {__version__} 启动崩溃日志\n")
                    f.write(f"时间: {datetime.now().isoformat()}\n")
                    f.write(f"错误: {e}\n")
                    f.write(f"堆栈追踪:\n{error_details}\n")
                print(f"崩溃详情已保存到 {crash_file_path}")
            except Exception as save_error:
                # 回退到主目录
                try:
                    with open("startup_crash.log", "w", encoding="utf-8") as f:
                        f.write(f"BioNexus {__version__} 启动崩溃日志\n")
                        f.write(f"错误: {e}\n")
                        f.write(f"堆栈追踪:\n{error_details}\n")
                    print(f"崩溃文件已保存到主目录 (logs目录保存失败: {save_error})")
                except:
                    pass
            
            # 显示错误对话框
            if self.app:
                QMessageBox.critical(
                    None,
                    "启动失败",
                    f"应用程序启动时发生错误:\n{e}\n\n详细信息已保存到日志文件"
                )
            return 1
        finally:
            # 清理资源
            if self.main_window:
                try:
                    self.main_window.close()
                except:
                    pass


def main():
    """
    程序主入口函数
    处理命令行参数并启动应用程序
    """
    # 处理命令行参数
    if len(sys.argv) > 1:
        if sys.argv[1] in ['-h', '--help']:
            print(__doc__)
            return 0
        elif sys.argv[1] in ['-v', '--version']:
            print("BioNexus Launcher v1.1.12")
            print("生物信息学工具管理器 - Python版本")
            return 0
    
    # 创建并启动应用程序
    launcher = BioNexusLauncher()
    return launcher.run()


if __name__ == "__main__":
    # 程序入口点
    exit_code = main()
    sys.exit(exit_code)