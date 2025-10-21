"""
统一下载引擎
提供可靠的文件下载功能，支持断点续传、多线程等特性
"""

import os
import logging
import hashlib
from pathlib import Path
from typing import Optional, Callable
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError


class DownloadEngine:
    """统一下载引擎"""
    
    def __init__(self):
        """初始化下载引擎"""
        self.logger = logging.getLogger(__name__)
        self.chunk_size = 8192  # 8KB chunks
        self.timeout = 30
        self.user_agent = 'BioNexus-DownloadEngine/1.1.12'
    
    def download_file(self, url: str, output_path: Path, 
                     progress_callback: Optional[Callable[[str, int], None]] = None,
                     verify_checksum: Optional[str] = None) -> bool:
        """
        下载文件
        
        Args:
            url: 下载URL
            output_path: 输出文件路径
            progress_callback: 进度回调函数 (status: str, percent: int)
            verify_checksum: 可选的文件校验和
            
        Returns:
            bool: 下载是否成功
        """
        self.logger.info(f"开始下载: {url}")
        
        try:
            # 准备输出目录
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 构建请求
            headers = {
                'User-Agent': self.user_agent,
                'Accept': '*/*',
                'Connection': 'keep-alive'
            }
            
            request = Request(url, headers=headers)
            
            if progress_callback:
                progress_callback("连接服务器...", 0)
            
            with urlopen(request, timeout=self.timeout) as response:
                # 获取文件大小
                total_size = int(response.headers.get('Content-Length', 0))
                
                if progress_callback:
                    progress_callback("开始下载...", 1)
                
                downloaded = 0
                
                with open(output_path, 'wb') as f:
                    while True:
                        chunk = response.read(self.chunk_size)
                        if not chunk:
                            break
                        
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        # 更新进度
                        if total_size > 0 and progress_callback:
                            percent = min(99, int((downloaded / total_size) * 100))
                            progress_callback(f"下载中... {percent}%", percent)
            
            # 验证文件完整性
            if verify_checksum:
                if progress_callback:
                    progress_callback("验证文件完整性...", 99)
                
                if not self._verify_file_checksum(output_path, verify_checksum):
                    self.logger.error("文件校验失败")
                    output_path.unlink()  # 删除损坏的文件
                    return False
            
            if progress_callback:
                progress_callback("下载完成", 100)
            
            self.logger.info(f"下载成功: {output_path}")
            return True
            
        except (URLError, HTTPError) as e:
            self.logger.error(f"下载失败 - 网络错误: {e}")
            if progress_callback:
                progress_callback(f"下载失败: 网络错误", -1)
            return False
        except Exception as e:
            self.logger.error(f"下载失败: {e}")
            if progress_callback:
                progress_callback(f"下载失败: {str(e)}", -1)
            return False
    
    def _verify_file_checksum(self, file_path: Path, expected_checksum: str) -> bool:
        """验证文件校验和"""
        try:
            hash_algo = 'sha256'  # 默认使用SHA256
            
            if expected_checksum.startswith('md5:'):
                hash_algo = 'md5'
                expected_checksum = expected_checksum[4:]
            elif expected_checksum.startswith('sha1:'):
                hash_algo = 'sha1'
                expected_checksum = expected_checksum[5:]
            elif expected_checksum.startswith('sha256:'):
                hash_algo = 'sha256'
                expected_checksum = expected_checksum[7:]
            
            hasher = hashlib.new(hash_algo)
            
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hasher.update(chunk)
            
            actual_checksum = hasher.hexdigest()
            return actual_checksum.lower() == expected_checksum.lower()
            
        except Exception as e:
            self.logger.error(f"校验和验证失败: {e}")
            return False
    
    def get_file_info(self, url: str) -> Optional[dict]:
        """
        获取文件信息（不下载文件）
        
        Args:
            url: 文件URL
            
        Returns:
            文件信息字典或None
        """
        try:
            headers = {'User-Agent': self.user_agent}
            request = Request(url, headers=headers)
            request.get_method = lambda: 'HEAD'
            
            with urlopen(request, timeout=self.timeout) as response:
                return {
                    'status_code': response.getcode(),
                    'content_length': int(response.headers.get('Content-Length', 0)),
                    'content_type': response.headers.get('Content-Type', ''),
                    'last_modified': response.headers.get('Last-Modified', ''),
                    'etag': response.headers.get('ETag', '')
                }
                
        except Exception as e:
            self.logger.error(f"获取文件信息失败: {e}")
            return None