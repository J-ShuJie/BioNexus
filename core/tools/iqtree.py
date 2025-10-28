"""
W-IQ-TREE Web启动器
打开IQ-TREE官方在线版，用于系统发育树构建和分析
"""
from .web_launcher_base import WebLauncherTool


class IQTREE(WebLauncherTool):
    """
    W-IQ-TREE (在线版)

    功能：
    - 打开IQ-TREE官方网页服务器
    - 使用最大似然法构建系统发育树
    - 支持多种进化模型选择和超快自举分析
    - 无需本地安装，通过网页上传数据即可分析
    - 只记录启动次数（无法记录使用时长）

    引用：
    J. Trifinopoulos, L.-T. Nguyen, A. von Haeseler, B.Q. Minh (2016)
    W-IQ-TREE: a fast online phylogenetic tool for maximum likelihood analysis.
    Nucleic Acids Res., 44:W232-W235.
    """

    METADATA = {
        'name': 'IQ-TREE Web',
        'version': 'Online',
        'category': 'phylogeny',
        'description': 'IQ-TREE官方在线服务器，用于最大似然法系统发育分析。支持自动模型选择、超快自举等功能。',
        'url': 'http://iqtree.cibiv.univie.ac.at/',
        'size': 'N/A',
        'requires': [],
        'status': 'available',
        'homepage': 'http://www.iqtree.org/',
        'documentation': 'https://iqtree.github.io/doc/Web-Server-Tutorial',
        'license': 'GPL-2.0',
        'tool_type': 'web_launcher'
    }
