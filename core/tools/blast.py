"""
BLAST工具占位符实现
⚠️ 注意：这是一个占位符，仅用于UI展示，不具备实际功能
实际的BLAST安装功能将在后续版本中实现
"""
from .placeholder_base import PlaceholderTool


class BLAST(PlaceholderTool):
    """
    BLAST (Basic Local Alignment Search Tool) 占位符
    未来将实现：
    - 从NCBI官网下载
    - 自动配置数据库
    - 支持多种BLAST变体（blastn, blastp, blastx等）
    """
    
    METADATA = {
        'name': 'BLAST',
        'version': '2.13.0',
        'category': 'sequence',
        'description': '基本局部比对搜索工具，用于寻找序列相似性的标准工具。支持核酸和蛋白质序列比对。',
        'size': '约 200 MB',
        'requires': [],
        'status': 'available',
        'homepage': 'https://blast.ncbi.nlm.nih.gov/',
        'documentation': 'https://www.ncbi.nlm.nih.gov/books/NBK279690/',
        'license': 'Public Domain'
    }