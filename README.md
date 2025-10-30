# Grouper

随机将学生分配给老师的工具，支持桌面版与 Docker/Web 版。

## 桌面版

- 安装依赖：`pip install -e .`
- 运行：`grouper`

## Web / Docker 版

- 本地运行：`grouper-web`（默认监听 `http://0.0.0.0:8000`）。
- Docker 构建：`docker build -t grouper-web -f docker/Dockerfile .`
- Docker 运行：`docker run -it --rm -p 8000:8000 grouper-web`

更多 Docker 说明见 `docker/README.md`。
