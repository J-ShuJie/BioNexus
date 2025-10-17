"""
工具包
包含所有生物信息学工具的实现

✅ 已实现实际功能：
- FastQC - 完整的下载、安装、启动功能

🚧 占位符工具（仅UI展示）：
- BLAST - 序列比对
- BWA - 基因组比对
- SAMtools - SAM/BAM处理
- HISAT2 - RNA-seq比对
- IQ-TREE - 系统发育分析
"""
from .base import ToolInterface
from .placeholder_base import PlaceholderTool

__all__ = ['ToolInterface', 'PlaceholderTool']