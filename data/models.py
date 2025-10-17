"""
数据模型定义
包含工具的完整信息结构，便于Python应用使用
每个工具对象包含：基本信息、状态、路径、使用统计等
"""
from dataclasses import dataclass
from typing import Optional
from datetime import datetime
from enum import Enum


class ToolStatus(Enum):
    """工具安装状态枚举"""
    INSTALLED = "installed"      # 已安装
    AVAILABLE = "available"      # 可安装
    UPDATE = "update"           # 需要更新


class ToolCategory(Enum):
    """工具功能分类枚举"""
    QUALITY = "quality"         # 质量控制
    SEQUENCE = "sequence"       # 序列分析  
    GENOMICS = "genomics"       # 基因组学
    RNASEQ = "rnaseq"          # RNA-seq
    PHYLOGENY = "phylogeny"     # 系统发育
    VISUALIZATION = "visualization"  # 可视化


class DownloadStatus(Enum):
    """下载任务状态枚举"""
    DOWNLOADING = "downloading"  # 下载中
    COMPLETED = "completed"     # 已完成
    FAILED = "failed"          # 下载失败


@dataclass
class Tool:
    """
    工具数据结构
    对应JavaScript中的toolsData数组元素
    """
    name: str                           # 工具名称
    category: ToolCategory              # 功能分类，用于筛选
    status: ToolStatus                  # 安装状态
    description: str                    # 工具描述
    version: str                       # 当前版本
    install_source: str                # 安装来源 (bioconda, pip等)
    executable_path: Optional[str] = None    # 可执行文件路径，未安装时为None
    disk_usage: Optional[str] = None         # 磁盘占用，如 "25.6 MB"
    last_used: Optional[datetime] = None     # 最后使用时间
    total_runtime: int = 0                   # 总运行时长（秒）


@dataclass
class DownloadTask:
    """
    下载任务数据结构
    对应JavaScript中的downloadTasks数组元素
    """
    tool_name: str              # 工具名称
    progress: int              # 下载进度百分比 (0-100)
    status: DownloadStatus     # 下载状态


@dataclass
class AppState:
    """
    应用程序状态管理
    集中管理应用的当前状态，便于状态同步和调试
    对应JavaScript中的appState对象
    """
    current_view: str = "all-tools"     # 当前显示的视图
    search_term: str = ""               # 当前搜索关键词
    filter_categories: list = None      # 选中的分类筛选
    filter_statuses: list = None        # 选中的状态筛选
    download_tasks: list = None         # 当前下载任务列表
    
    def __post_init__(self):
        """初始化默认值"""
        if self.filter_categories is None:
            self.filter_categories = []
        if self.filter_statuses is None:
            self.filter_statuses = []
        if self.download_tasks is None:
            self.download_tasks = []


# 预定义的工具数据，对应JavaScript中的toolsData数组
DEFAULT_TOOLS = [
    Tool(
        name="FastQC",
        category=ToolCategory.QUALITY,
        status=ToolStatus.INSTALLED,
        description="高通量测序数据质量控制工具，提供详细的质量报告和可视化图表。",
        version="0.11.9",
        install_source="bioconda",
        executable_path="C:\\Users\\User\\miniconda3\\envs\\biotools\\bin\\fastqc.exe",
        disk_usage="25.6 MB",
        last_used=datetime.fromisoformat("2025-01-15T10:30:00"),
        total_runtime=3600
    ),
    Tool(
        name="BLAST",
        category=ToolCategory.SEQUENCE,
        status=ToolStatus.AVAILABLE,
        description="基本局部比对搜索工具，用于寻找序列相似性的标准工具。",
        version="2.13.0",
        install_source="bioconda"
    ),
    Tool(
        name="BWA",
        category=ToolCategory.SEQUENCE,
        status=ToolStatus.AVAILABLE,
        description="Burrows-Wheeler变换比对器，用于将短DNA序列比对到大型参考基因组。",
        version="0.7.17",
        install_source="bioconda"
    ),
    Tool(
        name="SAMtools",
        category=ToolCategory.GENOMICS,
        status=ToolStatus.INSTALLED,
        description="处理高通量测序比对数据的工具集，支持SAM/BAM/CRAM格式。",
        version="1.16.1",
        install_source="bioconda",
        executable_path="C:\\Users\\User\\miniconda3\\envs\\biotools\\bin\\samtools.exe",
        disk_usage="12.3 MB",
        last_used=datetime.fromisoformat("2025-01-14T16:45:00"),
        total_runtime=7200
    ),
    Tool(
        name="HISAT2",
        category=ToolCategory.RNASEQ,
        status=ToolStatus.AVAILABLE,
        description="快速且内存高效的RNA-seq读段比对工具，支持可变剪接位点检测。",
        version="2.2.1",
        install_source="bioconda"
    ),
    Tool(
        name="IQ-TREE",
        category=ToolCategory.PHYLOGENY,
        status=ToolStatus.AVAILABLE,
        description="高效的系统发育分析软件，使用最大似然法构建进化树。",
        version="2.2.0",
        install_source="bioconda"
    ),
    Tool(
        name="IGV",
        category=ToolCategory.VISUALIZATION,
        status=ToolStatus.AVAILABLE,
        description="强大的基因组数据可视化工具，支持BAM、VCF、BED等多种格式。",
        version="2.17.0",
        install_source="official"
    )
]

# 默认下载任务，对应JavaScript中的downloadTasks数组
DEFAULT_DOWNLOAD_TASKS = [
    DownloadTask(
        tool_name="BLAST",
        progress=65,
        status=DownloadStatus.DOWNLOADING
    ),
    DownloadTask(
        tool_name="BWA",
        progress=100,
        status=DownloadStatus.COMPLETED
    )
]