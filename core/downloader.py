"""
智能下载器
支持多源下载、断点续传、镜像切换等功能
"""
import os
import requests
import time
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Callable, Optional, Any
from utils.unified_logger import get_logger


class SmartDownloader:
    """
    智能多源下载器
    自动选择最佳下载源，支持失败切换和断点续传
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 使用统一日志系统
        self.unified_logger = get_logger()
        
        self.session = requests.Session()
        # 设置请求头，模拟浏览器
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
    
    def download_with_fallback(
        self, 
        sources: List[Dict[str, Any]], 
        output_path: Path,
        progress_callback: Optional[Callable[[str, int], None]] = None,
        chunk_size: int = 8192
    ) -> bool:
        """
        多源下载，支持自动切换
        
        Args:
            sources: 下载源列表，按优先级排序
            output_path: 输出文件路径
            progress_callback: 进度回调函数(status_text, percentage)
            chunk_size: 下载块大小
            
        Returns:
            bool: 下载是否成功
        """
        # 确保输出目录存在
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 按优先级排序
        sorted_sources = sorted(sources, key=lambda x: x.get('priority', 999))
        
        self.unified_logger.log_runtime(f"下载候选源数量: {len(sorted_sources)}")
        for source in sorted_sources:
            source_name = source.get('name', '未知源')
            source_url = source.get('url')
            timeout = source.get('timeout', 30)
            
            if not source_url:
                self.logger.warning(f"源 {source_name} 缺少URL")
                continue
            
            if progress_callback:
                progress_callback(f"正在从 {source_name} 下载...", 0)
            
            # 详细日志：记录尝试的源
            try:
                self.unified_logger.log_installation(source_name, '下载尝试', '开始', {
                    'url': source_url,
                    'timeout': timeout,
                    'output': str(output_path)
                })
            except Exception:
                pass

            success = self._download_from_source(
                source_url, 
                output_path, 
                source_name, 
                timeout, 
                progress_callback, 
                chunk_size
            )
            
            if success:
                if progress_callback:
                    progress_callback(f"从 {source_name} 下载完成", 100)
                return True
            else:
                if progress_callback:
                    progress_callback(f"{source_name} 失败，尝试下一个源...", -1)
                # 清理失败的部分下载文件
                if output_path.exists():
                    try:
                        output_path.unlink()
                    except:
                        pass
                continue
        
        # 所有源都失败
        if progress_callback:
            progress_callback("所有下载源均失败", -1)
        # 统一日志：所有源失败
        try:
            self.unified_logger.log_error('下载失败', '所有下载源均失败', {
                'targets': [s.get('url') for s in sorted_sources]
            })
        except Exception:
            pass
        return False
    
    def _download_from_source(
        self,
        url: str,
        output_path: Path,
        source_name: str,
        timeout: int,
        progress_callback: Optional[Callable[[str, int], None]],
        chunk_size: int
    ) -> bool:
        """
        从单个源下载文件
        
        Args:
            url: 下载地址
            output_path: 输出路径
            source_name: 源名称
            timeout: 超时时间
            progress_callback: 进度回调
            chunk_size: 块大小
            
        Returns:
            bool: 是否成功
        """
        start_time = time.time()
        retry_count = 0
        
        try:
            # 记录下载开始
            start_time = time.time()
            self.unified_logger.log_installation(source_name, '下载开始', '进行中', {
                'url': url,
                'output_path': str(output_path),
                'timeout': timeout
            })
            
            # 检查是否支持断点续传
            resume_pos = 0
            headers = dict(self.session.headers)  # 复制基础头
            
            if output_path.exists():
                resume_pos = output_path.stat().st_size
                # 先获取文件总大小来判断是否已经完整下载
                try:
                    head_response = self.session.head(url, timeout=timeout)
                    if head_response.status_code == 200:
                        total_size_str = head_response.headers.get('content-length')
                        if total_size_str and resume_pos >= int(total_size_str):
                            # 文件已经完整下载
                            self.logger.info(f"文件已完整下载: {output_path}")
                            self.unified_logger.log_installation(
                                source_name, "文件检查", "已存在", 
                                {"file_size": resume_pos}
                            )
                            return True
                except:
                    pass  # HEAD请求失败，继续正常下载流程
                
                if resume_pos > 0:
                    self.logger.info(f"检测到部分下载文件，从 {resume_pos} 字节处继续")
                    self.unified_logger.log_installation(
                        source_name, "断点续传", "检测到", 
                        {"resume_position": resume_pos}
                    )
                    headers['Range'] = f'bytes={resume_pos}-'
            
            # 发送请求
            request_start = time.time()
            self.unified_logger.log_runtime(f"HTTP GET: {url} (timeout={timeout}, resume_pos={resume_pos})")
            response = self.session.get(
                url, 
                headers=headers, 
                stream=True, 
                timeout=timeout
            )
            
            # 记录网络请求
            request_duration = time.time() - request_start
            content_length = response.headers.get('content-length')
            self.unified_logger.log_network(url, "GET", response.status_code, request_duration)
            
            # 检查响应状态
            if response.status_code not in [200, 206]:  # 206是断点续传状态码
                error_msg = f"HTTP {response.status_code}: {getattr(response, 'reason', '未知错误')}"
                self.logger.warning(f"源 {source_name} 返回状态码: {response.status_code}")
                self.unified_logger.log_error('下载失败', error_msg, {
                    "source": source_name, 
                    "url": url,
                    "final_url": getattr(response, 'url', url),
                    "status_code": response.status_code,
                    "headers": dict(response.headers or {})
                })
                return False
            
            # 获取文件总大小
            content_length = response.headers.get('content-length')
            if content_length:
                total_size = int(content_length)
                if response.status_code == 206:  # 断点续传
                    total_size += resume_pos
            else:
                total_size = 0
                self.logger.warning(f"无法获取文件大小: {url}")
            # 详细记录响应头与内容长度
            try:
                self.unified_logger.log_runtime(
                    f"HTTP响应: status={response.status_code}, final_url={getattr(response,'url',url)}, content_length={content_length}, accept_ranges={response.headers.get('accept-ranges','')}"
                )
            except Exception:
                pass
            
            # 开始下载
            downloaded_size = resume_pos
            mode = 'ab' if resume_pos > 0 else 'wb'
            
            with open(output_path, mode) as f:
                start_time = time.time()
                last_update = start_time
                
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        
                        # 更新进度（每0.1秒更新一次）
                        current_time = time.time()
                        if current_time - last_update >= 0.1:
                            if total_size > 0:
                                percentage = int(downloaded_size * 100 / total_size)
                                speed = downloaded_size / (current_time - start_time)
                                speed_text = self._format_speed(speed)
                                
                                if progress_callback:
                                    status = f"下载中 {source_name} ({speed_text})"
                                    progress_callback(status, percentage)
                            
                            last_update = current_time
            
            # 验证下载完整性
            if total_size > 0 and downloaded_size != total_size:
                error_msg = f"下载大小不匹配: {downloaded_size}/{total_size}"
                self.logger.warning(error_msg)
                self.unified_logger.log_error('下载完整性', error_msg, {
                    "source": source_name,
                    "expected_size": total_size, 
                    "actual_size": downloaded_size
                })
                return False
            
            # 记录下载成功
            download_duration = time.time() - start_time
            self.unified_logger.log_installation(source_name, '下载完成', '成功', {
                'file_size': downloaded_size,
                'duration': f"{download_duration:.2f}s"
            })
            
            self.logger.info(f"成功从 {source_name} 下载: {output_path}")
            return True
            
        except requests.exceptions.Timeout as e:
            self.logger.warning(f"源 {source_name} 连接超时")
            self.unified_logger.log_error('下载超时', repr(e), {"source": source_name, "url": url, "timeout": timeout})
            return False
        except requests.exceptions.ConnectionError as e:
            self.logger.warning(f"源 {source_name} 连接失败")
            self.unified_logger.log_error('下载连接失败', repr(e), {"source": source_name, "url": url})
            return False
        except Exception as e:
            self.logger.error(f"从 {source_name} 下载失败: {e}")
            self.unified_logger.log_error('下载异常', repr(e), {"source": source_name, "url": url})
            return False
    
    def _format_speed(self, bytes_per_second: float) -> str:
        """
        格式化下载速度
        
        Args:
            bytes_per_second: 每秒字节数
            
        Returns:
            格式化的速度字符串
        """
        if bytes_per_second < 1024:
            return f"{bytes_per_second:.1f} B/s"
        elif bytes_per_second < 1024 * 1024:
            return f"{bytes_per_second / 1024:.1f} KB/s"
        else:
            return f"{bytes_per_second / (1024 * 1024):.1f} MB/s"
    
    def verify_file_integrity(self, file_path: Path, expected_hash: str, hash_type: str = 'md5') -> bool:
        """
        验证文件完整性
        
        Args:
            file_path: 文件路径
            expected_hash: 期望的哈希值
            hash_type: 哈希类型 (md5, sha1, sha256)
            
        Returns:
            bool: 文件是否完整
        """
        if not file_path.exists():
            return False
        
        try:
            # 选择哈希算法
            if hash_type.lower() == 'md5':
                hasher = hashlib.md5()
            elif hash_type.lower() == 'sha1':
                hasher = hashlib.sha1()
            elif hash_type.lower() == 'sha256':
                hasher = hashlib.sha256()
            else:
                self.logger.error(f"不支持的哈希类型: {hash_type}")
                return False
            
            # 计算文件哈希
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    hasher.update(chunk)
            
            file_hash = hasher.hexdigest().lower()
            expected_hash = expected_hash.lower()
            
            if file_hash == expected_hash:
                self.logger.info(f"文件完整性验证通过: {file_path}")
                return True
            else:
                self.logger.warning(f"文件完整性验证失败: {file_path}")
                self.logger.warning(f"期望: {expected_hash}, 实际: {file_hash}")
                return False
                
        except Exception as e:
            self.logger.error(f"文件完整性验证异常: {e}")
            return False
    
    def get_file_size(self, url: str, timeout: int = 10) -> Optional[int]:
        """
        获取远程文件大小
        
        Args:
            url: 文件URL
            timeout: 超时时间
            
        Returns:
            文件大小（字节），失败返回None
        """
        try:
            response = self.session.head(url, timeout=timeout)
            if response.status_code == 200:
                content_length = response.headers.get('content-length')
                if content_length:
                    return int(content_length)
            return None
        except Exception as e:
            self.logger.warning(f"获取文件大小失败 {url}: {e}")
            return None
