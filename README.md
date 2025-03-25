# Package Manager

Package Manager 是一个 Python3 包版本管理器，允许在同一项目中同时管理和使用同名但不同版本的包。

## 特性

- 支持主版本（通过 pip 安装）的管理
- 注册和加载其他自定义版本
- 版本切换（活动版本）
- 基于上下文的临时版本使用
- 缓存机制
- 配置持久化
- 线程安全

## 安装

```bash
pip install package_manager
```

## 快速开始

### 基本用法

```python
from package_manager import setup_package_manager

# 设置包管理器
numpy_manager = setup_package_manager(
    name="numpy",
    register_main=True,  # 注册 pip 安装的主版本
    versions={
        "custom": "/path/to/custom_numpy",
    },
    default_version="main"
)

# 使用当前活动版本
np = numpy_manager()
result = np.array([1, 2, 3]).mean()

# 切换版本
np_custom = numpy_manager.use_version("custom")
result = np_custom.array([1, 2, 3]).mean()

# 临时使用特定版本
with numpy_manager.temporary_version("main") as np_main:
    result = np_main.array([1, 2, 3]).mean()
```

### 导入特定版本

```python
from package_manager import import_version

# 导入特定版本但不改变当前活动版本
np_main = import_version("numpy", "main")
```

### 版本装饰器

```python
from package_manager import create_decorator

# 创建装饰器
with_numpy_legacy = create_decorator("numpy", "legacy")

@with_numpy_legacy
def process_data(data):
    """这个函数将使用 legacy 版本的 numpy"""
    np = import_version("numpy")  # 在这个函数内会获取 legacy 版本
    return np.mean(data)
```

## 高级用法

### 列出所有版本

```python
versions = numpy_manager.list_versions()
for ver in versions:
    print(f"- {ver['version']} {'(active)' if ver['active'] else ''}")
    print(f"  Path: {ver['path']}")
```

### 动态注册版本

```python
# 获取现有或创建新管理器
from package_manager import get_package_manager
mylib_manager = get_package_manager("mylib")

# 动态注册版本
import os
versions_dir = "/path/to/mylib_versions"
for item in os.listdir(versions_dir):
    version_path = os.path.join(versions_dir, item)
    if os.path.isdir(version_path):
        try:
            version_name = item.replace("mylib-", "")
            mylib_manager.register_version(version_name, version_path)
        except ValueError as e:
            print(f"Failed to register {item}: {e}")
```

## 许可

本项目采用 Apache License 2.0