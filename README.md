# Grouper

随机将学生分配给老师的工具，支持Windows 10+桌面版、Docker/Web 版。

## 桌面版

> 建议在Windows 10+系统中的PowerShell或者CMD里运行。 Windows 7系统将不支持。

+ 构建Python环境（比如，将环境托管在`D:\\python_environment`中）

```shell
cd D:\\python_environment
python -m venv .venv
D:\\python_environment\\.venv\\Scripts\\activate
pip install PySide6 openpyxl
```

+ 运行环境

```shell
D:\\python_environment\\.venv\\Scripts\\activate
cd E:\\PythonCloud\\Package\\Grouper
x86_64\\build_windows.bat
```

+ 可执行文件：软件保存为`dist\\Grouper.exe`。

## Web / Docker 版

- 本地运行：`grouper-web`（默认监听 `http://0.0.0.0:8000`）。
- Docker 构建：`docker build -t grouper-web -f docker/Dockerfile .`
- Docker 运行：`docker run -it --rm -p 8000:8000 grouper-web`

更多 Docker 说明见 `docker/README.md`。
