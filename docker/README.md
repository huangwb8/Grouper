# Docker 部署指南

## 构建镜像

```bash
docker build -t grouper-web -f docker/Dockerfile .
```

## 运行容器

```bash
docker run -d \
  -p 8000:8000 \
  -v $(pwd)/exports:/app/exports \
  --name grouper-web \
  grouper-web
```

访问 `http://localhost:8000` 即可使用浏览器版本的 Grouper。

### 环境变量

- `GROUPER_WEB_HOST`：监听的主机名，默认 `0.0.0.0`
- `GROUPER_WEB_PORT`：监听端口，默认 `8000`
- `GROUPER_EXPORT_DIR`：Excel 文件的保存目录，默认 `/app/exports`
- `GROUPER_SECRET_KEY`：Flask 应用的会话密钥，请在生产环境中设置为安全随机值。
