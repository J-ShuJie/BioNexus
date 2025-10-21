"""
日志清理工具
负责清理旧的日志文件，节省磁盘空间
"""
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional
import logging


class LogCleaner:
    """日志清理器"""

    def __init__(self, logs_dir: Path = None):
        """
        初始化日志清理器

        Args:
            logs_dir: 日志目录，默认为 logs/
        """
        self.logs_dir = logs_dir or Path("logs")
        self.logger = logging.getLogger(__name__)

    def clean_old_logs(self, days: int = 30) -> dict:
        """
        清理N天前的日志

        Args:
            days: 保留最近N天的日志，默认30天

        Returns:
            清理结果字典：{
                'success': bool,
                'cleaned_count': int,
                'freed_space': int (bytes),
                'error': str (if failed)
            }
        """
        result = {
            'success': False,
            'cleaned_count': 0,
            'freed_space': 0,
            'error': None
        }

        try:
            if not self.logs_dir.exists():
                result['success'] = True
                return result

            # 计算截止日期
            cutoff_date = datetime.now() - timedelta(days=days)

            # 扫描日志目录
            for date_folder in self.logs_dir.iterdir():
                if not date_folder.is_dir():
                    continue

                # 解析文件夹名称（格式：YYYY-MM-DD）
                folder_date = self._parse_date_from_name(date_folder.name)

                if folder_date and folder_date < cutoff_date:
                    try:
                        # 计算文件夹大小
                        folder_size = self._get_dir_size(date_folder)

                        # 删除文件夹
                        shutil.rmtree(date_folder)

                        result['cleaned_count'] += 1
                        result['freed_space'] += folder_size

                        self.logger.info(f"已清理旧日志: {date_folder.name}")

                    except Exception as e:
                        self.logger.error(f"清理日志文件夹 {date_folder.name} 失败: {e}")

            result['success'] = True
            return result

        except Exception as e:
            result['error'] = str(e)
            self.logger.error(f"日志清理失败: {e}")
            return result

    def _parse_date_from_name(self, folder_name: str) -> Optional[datetime]:
        """
        从文件夹名称解析日期

        Args:
            folder_name: 文件夹名称，格式 YYYY-MM-DD

        Returns:
            datetime对象，解析失败返回None
        """
        try:
            # 尝试解析 YYYY-MM-DD 格式
            return datetime.strptime(folder_name, "%Y-%m-%d")
        except ValueError:
            return None

    def _get_dir_size(self, directory: Path) -> int:
        """
        计算目录大小

        Args:
            directory: 目录路径

        Returns:
            目录总大小（字节）
        """
        total_size = 0
        try:
            for item in directory.rglob('*'):
                if item.is_file():
                    total_size += item.stat().st_size
        except Exception as e:
            self.logger.warning(f"计算目录大小失败 {directory}: {e}")
        return total_size

    def get_logs_info(self) -> dict:
        """
        获取日志统计信息

        Returns:
            日志信息字典：{
                'total_size': int (bytes),
                'folder_count': int,
                'oldest_date': str,
                'newest_date': str
            }
        """
        info = {
            'total_size': 0,
            'folder_count': 0,
            'oldest_date': None,
            'newest_date': None
        }

        try:
            if not self.logs_dir.exists():
                return info

            dates = []

            for date_folder in self.logs_dir.iterdir():
                if not date_folder.is_dir():
                    continue

                info['folder_count'] += 1
                info['total_size'] += self._get_dir_size(date_folder)

                folder_date = self._parse_date_from_name(date_folder.name)
                if folder_date:
                    dates.append(folder_date)

            if dates:
                info['oldest_date'] = min(dates).strftime("%Y-%m-%d")
                info['newest_date'] = max(dates).strftime("%Y-%m-%d")

        except Exception as e:
            self.logger.error(f"获取日志信息失败: {e}")

        return info


def get_log_cleaner() -> LogCleaner:
    """获取日志清理器实例"""
    return LogCleaner()
