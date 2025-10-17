# BioNexus 存储管理系统使用指南

## 📋 概述

BioNexus 存储管理系统是一个智能的生物信息学工具存储管理解决方案，提供了全面的磁盘空间管理、工具删除、依赖环境清理和空间预警功能。

## 🚀 主要功能

### 1. 存储概览
- **磁盘空间监控**: 实时显示系统总空间、已用空间、剩余空间
- **BioNexus占用**: 显示整个BioNexus项目占用的磁盘空间
- **工具统计**: 显示已安装工具数量和总占用空间
- **环境统计**: 显示共享运行环境（Java、Python等）的占用空间

### 2. 工具存储管理
- **详细列表**: 显示所有已安装工具及其占用空间
- **排序功能**: 按大小、名称、安装日期排序
- **批量选择**: 支持多选工具进行批量操作
- **快速搜索**: 根据工具名称快速定位

### 3. 智能删除系统
- **依赖分析**: 自动分析工具间的依赖关系
- **环境清理**: 智能检测可清理的运行环境
- **二次确认**: 防误删的确认对话框
- **批量删除**: 支持一次删除多个工具

### 4. 空间预警
- **安装前检查**: 安装工具前检查可用空间
- **低空间警告**: 磁盘剩余空间 < 10GB 时显示警告
- **智能建议**: 提供存储空间优化建议

## 🛠️ 技术架构

### 核心模块

#### 1. 依赖管理器 (`utils/dependency_manager.py`)
```python
from utils.dependency_manager import get_dependency_manager

dep_manager = get_dependency_manager()

# 获取工具依赖
dependencies = dep_manager.get_tool_dependencies("FastQC")

# 检查清理候选
cleanup_candidates = dep_manager.check_cleanup_candidates(["FastQC", "BLAST"])
```

**主要功能**:
- 管理工具与运行环境的依赖关系
- 检测可安全删除的环境
- 提供依赖关系统计和分析

#### 2. 存储计算器 (`utils/storage_calculator.py`)
```python
from utils.storage_calculator import get_storage_calculator

calc = get_storage_calculator()

# 获取系统磁盘信息
disk_info = calc.get_system_disk_info()

# 检查空间是否足够
sufficient, free_space = calc.check_sufficient_space(1024*1024*100)  # 100MB

# 获取所有工具存储信息
tools_info = calc.get_all_tools_storage_info()
```

**主要功能**:
- 精确计算文件和目录大小
- 系统磁盘空间检查
- 工具存储信息收集和分析
- 删除操作的空间节省预估

#### 3. UI组件

##### 存储管理器组件 (`ui/storage_manager_widget.py`)
- **StorageManagerWidget**: 主存储管理界面（适配设置面板卡片）
- **StorageOverviewWidget**: 紧凑式存储概览显示
- **ToolsTableWidget**: 响应式工具列表表格

##### 删除确认对话框 (`ui/deletion_confirmation_dialog.py`)
- **DeletionConfirmationDialog**: 完整的删除确认对话框
- **QuickDeleteDialog**: 快速删除确认对话框

## 📱 使用方法

### 访问存储管理
1. 打开 BioNexus 主界面
2. 点击左侧导航栏的 "设置" 
3. 滚动到 "存储管理" 部分

### 查看存储状态
- **存储概览**: 聚焦核心信息显示，如"剩余: 21.8GB | 工具占用: 1个/12MB"
- **工具列表**: 下方表格显示所有已安装工具的详细信息
- **操作按钮**: 右侧提供紧凑排列的[全选][取消][刷新][删除]操作按钮
- **排序**: 点击表格标题进行排序（默认按大小降序）

### 删除工具
1. **选择工具**: 勾选要删除的工具，支持多选
2. **批量操作**: 使用 "全选" / "取消" 按钮快速选择
3. **确认删除**: 点击 "删除选中" 按钮
4. **详细确认**: 在弹出的对话框中查看删除详情和环境清理建议
5. **最终确认**: 确认后执行删除操作

### 环境清理
当删除工具时，系统会自动检测以下情况：
- 某个运行环境（如java-11）不再被任何工具使用
- 系统会提示是否同时清理这些环境
- 用户可以选择保留或清理环境

### 安装空间检查
系统会在以下情况下自动检查空间：
- 安装新工具时
- 剩余空间 < 10GB 时显示警告对话框
- 提供 "继续安装" 或 "取消安装" 选项

## ⚙️ 配置选项

### 依赖关系配置 (`data/dependencies.json`)
```json
{
  "tool_dependencies": {
    "FastQC": ["java-11"],
    "BLAST": ["python-3.8"], 
    "BWA": ["gcc-runtime"],
    "SAMtools": ["python-3.8"],
    "HISAT2": ["python-3.8", "gcc-runtime"],
    "IQ-TREE": ["gcc-runtime"]
  },
  "last_updated": "2025-01-15",
  "version": "1.0"
}
```

### 环境描述配置
系统内置常见环境的描述信息：
- `java-11`: Java 11 运行时环境
- `python-3.8`: Python 3.8 运行环境  
- `gcc-runtime`: GCC 运行时库

## 🔧 高级功能

### 1. 自定义依赖关系
```python
from utils.dependency_manager import get_dependency_manager

dep_manager = get_dependency_manager()

# 添加新的工具依赖
dep_manager.add_tool_dependency("MyTool", "java-11")

# 移除工具的所有依赖
dep_manager.remove_tool_dependencies("OldTool")
```

### 2. 存储分析
```python
from utils.storage_calculator import get_storage_calculator

calc = get_storage_calculator()

# 获取详细的存储摘要
summary = calc.get_storage_summary()

# 分析删除操作的影响
deletion_info = calc.calculate_deletion_savings(["FastQC", "BLAST"])
```

### 3. 空间监控
```python
# 在安装前检查空间
if settings_panel.check_disk_space_before_install(required_size):
    # 继续安装
    install_tool()
else:
    # 取消安装
    cancel_installation()
```

## 📊 性能优化

### 1. 缓存机制
- 目录大小计算结果缓存，避免重复计算
- 后台线程进行耗时操作，保持界面响应

### 2. 批量操作
- 支持批量删除多个工具
- 一次性清理多个环境
- 减少文件系统操作次数

### 3. 智能检测
- 只在必要时触发空间检查
- 动态更新界面数据
- 最小化系统资源占用

## 🛡️ 安全特性

### 1. 数据保护
- 删除操作需要明确确认
- 批量删除显示详细预览
- 支持误操作保护机制

### 2. 依赖检查
- 删除前检查工具间依赖
- 防止意外删除共享环境
- 智能建议清理策略

### 3. 空间预警
- 低磁盘空间及时警告
- 安装前容量验证
- 避免系统空间耗尽

## 🐛 故障排除

### 常见问题

#### 1. 计算大小不准确
**原因**: 文件权限或符号链接问题
**解决**: 检查文件访问权限，清空计算缓存

#### 2. 删除失败
**原因**: 文件被占用或权限不足
**解决**: 关闭相关程序，使用管理员权限运行

#### 3. 界面显示异常
**原因**: PyQt5 环境问题
**解决**: 确保PyQt5正确安装，检查Python环境

#### 4. 依赖关系错误
**原因**: dependencies.json 文件损坏
**解决**: 删除文件让系统重建默认依赖关系

### 调试方法

#### 启用调试日志
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

#### 运行测试脚本
```bash
python3 test_storage_management.py
```

#### 手动验证依赖
```python
from utils.dependency_manager import get_dependency_manager
dep_manager = get_dependency_manager()
print(dep_manager.get_dependency_summary())
```

## 📈 未来扩展

### 计划功能
1. **存储趋势分析**: 显示磁盘使用随时间的变化
2. **自动清理**: 定期清理临时文件和旧版本工具
3. **云存储集成**: 支持云端备份和同步
4. **压缩存储**: 自动压缩不常用工具
5. **使用统计**: 分析工具使用频率，建议删除策略

### 扩展接口
系统设计了灵活的扩展接口，支持：
- 自定义存储后端
- 插件式环境管理器
- 第三方工具集成
- REST API 支持

## 📞 技术支持

如果您在使用过程中遇到问题：

1. **查看日志**: 检查 `logs/` 目录下的日志文件
2. **运行测试**: 使用 `test_storage_management.py` 验证功能
3. **重置配置**: 删除 `data/dependencies.json` 重建依赖关系
4. **更新软件**: 确保使用最新版本的 BioNexus

---

*本指南随 BioNexus v1.2.3 发布，包含最新的存储管理功能。*