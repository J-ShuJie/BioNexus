"""
HISAT2工具占位符实现
⚠️ 注意：这是一个占位符，仅用于UI展示，不具备实际功能
"""
from .placeholder_base import PlaceholderTool


class HISAT2(PlaceholderTool):
    """
    HISAT2 (Hierarchical Indexing for Spliced Alignment of Transcripts 2) 占位符
    未来将实现完整的安装和配置功能
    """
    
    METADATA = {
        'name': 'HISAT2',
        'version': '2.2.1',
        'category': 'rnaseq',
        'description': '快速且内存高效的RNA-seq读段比对工具，支持可变剪接位点检测。适用于转录组数据分析。',
        'size': '约 20 MB',
        'requires': [],
        'status': 'available',
        'homepage': 'http://daehwankimlab.github.io/hisat2/',
        'documentation': 'http://daehwankimlab.github.io/hisat2/manual/',
        'license': 'GPL-3.0'
    }