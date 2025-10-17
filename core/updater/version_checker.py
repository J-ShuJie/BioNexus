"""
版本检查器
用于检查GitHub上的最新版本并比较当前版本
"""

import json
import logging
from typing import Optional, Dict, Any
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
import sys
from pathlib import Path

# 添加主目录到路径以导入main模块
sys.path.append(str(Path(__file__).parent.parent.parent))
from main import __version__

class VersionChecker:
    """版本检查器类"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.github_api_url = "https://api.github.com/repos/your-username/BioNexus/releases/latest"
        self.current_version = __version__
    
    def check_latest_version(self) -> Optional[Dict[str, Any]]:
        """
        检查GitHub上的最新版本
        
        Returns:
            Dict: 包含版本信息的字典，如果检查失败返回None
            格式: {
                'version': '1.1.11',
                'download_url': 'https://github.com/...',
                'release_notes': '更新说明',
                'published_at': '2025-09-02T12:00:00Z',
                'is_newer': True
            }
        """
        try:
            headers = {
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': 'BioNexus-UpdateChecker/1.0'
            }
            
            request = Request(self.github_api_url, headers=headers)
            
            with urlopen(request, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
                
                latest_version = data.get('tag_name', '').lstrip('v')
                download_url = None
                
                # 查找Windows可执行文件下载链接
                for asset in data.get('assets', []):
                    if asset['name'].endswith('.exe') or 'windows' in asset['name'].lower():
                        download_url = asset['browser_download_url']
                        break
                
                # 如果没找到特定的exe，使用源码包
                if not download_url and data.get('assets'):
                    download_url = data['assets'][0]['browser_download_url']
                
                # 比较版本
                is_newer = self._is_newer_version(latest_version, self.current_version)
                
                version_info = {
                    'version': latest_version,
                    'download_url': download_url or data.get('zipball_url'),
                    'release_notes': data.get('body', ''),
                    'published_at': data.get('published_at'),
                    'is_newer': is_newer,
                    'current_version': self.current_version
                }
                
                self.logger.info(f"版本检查完成: 当前 {self.current_version}, 最新 {latest_version}")
                return version_info
                
        except (URLError, HTTPError, json.JSONDecodeError, KeyError) as e:
            self.logger.error(f"检查版本更新失败: {e}")
            return None
        except Exception as e:
            self.logger.error(f"版本检查出现意外错误: {e}")
            return None
    
    def _is_newer_version(self, remote_version: str, current_version: str) -> bool:
        """
        比较版本号
        
        Args:
            remote_version: 远程版本号
            current_version: 当前版本号
            
        Returns:
            bool: 如果远程版本更新则返回True
        """
        try:
            def parse_version(v):
                return tuple(map(int, v.split('.')))
            
            remote_parts = parse_version(remote_version)
            current_parts = parse_version(current_version)
            
            return remote_parts > current_parts
            
        except (ValueError, AttributeError):
            # 如果版本号格式异常，保守地返回False
            self.logger.warning(f"版本号格式异常: remote={remote_version}, current={current_version}")
            return False
    
    def set_github_repo(self, username: str, repo_name: str):
        """
        设置GitHub仓库信息
        
        Args:
            username: GitHub用户名
            repo_name: 仓库名
        """
        self.github_api_url = f"https://api.github.com/repos/{username}/{repo_name}/releases/latest"
        self.logger.info(f"GitHub仓库已设置为: {username}/{repo_name}")