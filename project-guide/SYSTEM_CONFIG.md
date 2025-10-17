# BioNexus 系统配置要求

## ⚠️ 关键提醒 ⚠️

**BioNexus 是纯Windows软件，专为Windows 10/11用户设计**

### 系统要求：
- **目标系统**: Windows 10/11 **ONLY**
- **不支持**: Linux, macOS, 或任何其他操作系统
- **架构**: x64
- **Python**: Windows版本的Python 3.13.2
- **Java**: Windows版本的Java 11+

### 开发和测试注意事项：
1. 所有代码必须考虑Windows环境
2. 所有路径使用Windows路径分隔符 (`\`)
3. 所有下载的环境（Java、Python等）必须是Windows版本
4. GUI组件基于PyQt5 for Windows
5. 进程管理使用Windows特定的创建标志

### 文件路径格式：
- ✅ `C:\Users\username\Desktop\...`
- ✅ `installed_tools\FastQC\run_fastqc.bat`
- ❌ `/mnt/c/Users/...` (WSL路径)
- ❌ `java` (Unix可执行文件)
- ✅ `java.exe` (Windows可执行文件)

### 环境管理：
- Java运行时：必须下载Windows版本的JRE/JDK
- Python环境：Windows版本
- 工具可执行文件：.exe, .bat, .cmd

## 如果你在修改代码时忘记了这些要求，请立即停止并重新审视！