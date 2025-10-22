"""
BWA工具占位符实现
⚠️ 注意：这是一个占位符，仅用于UI展示，不具备实际功能
"""
from .placeholder_base import PlaceholderTool


class BWA(PlaceholderTool):
    """
    BWA (Burrows-Wheeler Aligner) 占位符
    未来将实现完整的安装和配置功能
    """
    
    METADATA = {
        'name': 'BWA',
        'version': '0.7.17',
        'category': 'sequence',
        'description': 'Burrows-Wheeler变换比对器，用于将短DNA序列比对到大型参考基因组。高效处理Illumina测序数据。',
        'size': '约 5 MB',
        'requires': [],
        'status': 'available',
        'homepage': 'http://bio-bwa.sourceforge.net/',
        'documentation': 'http://bio-bwa.sourceforge.net/bwa.shtml',
        'license': 'GPL-3.0'
    }
