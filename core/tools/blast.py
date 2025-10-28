"""
NCBI BLAST Web启动器
打开NCBI BLAST在线版网页，用于序列比对分析
"""
from .web_launcher_base import WebLauncherTool


class BLAST(WebLauncherTool):
    """
    NCBI BLAST (在线版)

    功能：
    - 打开NCBI BLAST官方网站
    - 支持各种BLAST变体（blastn, blastp, blastx等）
    - 无需本地安装，直接使用在线服务
    - 只记录启动次数（无法记录使用时长）
    """

    METADATA = {
        'name': 'BLAST NCBI',
        'version': 'Online',
        'category': 'sequence',
        'description': 'NCBI官方在线BLAST工具，用于核酸和蛋白质序列相似性搜索。支持blastn、blastp、blastx等多种比对方式。',
        'url': 'https://blast.ncbi.nlm.nih.gov/Blast.cgi',
        'size': 'N/A',
        'requires': [],
        'status': 'available',
        'homepage': 'https://blast.ncbi.nlm.nih.gov/',
        'documentation': 'https://blast.ncbi.nlm.nih.gov/Blast.cgi?CMD=Web&PAGE_TYPE=BlastDocs',
        'license': 'Public Domain',
        'tool_type': 'web_launcher'
    }
