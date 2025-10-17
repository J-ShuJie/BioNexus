"""
IQ-TREE工具占位符实现
⚠️ 注意：这是一个占位符，仅用于UI展示，不具备实际功能
"""
from .placeholder_base import PlaceholderTool


class IQTREE(PlaceholderTool):
    """
    IQ-TREE 占位符
    未来将实现完整的安装和配置功能
    """
    
    METADATA = {
        'name': 'IQ-TREE',
        'version': '2.2.0',
        'category': 'phylogeny',
        'description': '高效的系统发育分析软件，使用最大似然法构建进化树。支持多种模型选择和Bootstrap分析。',
        'size': '约 30 MB',
        'requires': [],
        'status': 'available',
        'homepage': 'http://www.iqtree.org/',
        'documentation': 'http://www.iqtree.org/doc/',
        'license': 'GPL-2.0'
    }