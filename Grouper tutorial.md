# CodeX

```shell
# 开启Windows子Linux系统
wsl

# 进入工作目录
cd /mnt/e/PythonCloud/Package/Grouper

# 开启codex
codex
```

# 日志

+ 02

```
 已根据 repairs.txt 的“bug 01”完成三项针对性优化：中文显示、按老师定制人数、Windows 打包可用性。

  修复与改进

  - 中文字体乱码
      - 在应用启动时全局设置中文友好字体优先级，按平台优先选择可用字体，避免打包后中文缺字形导致的乱码渲染。
      - 变更位置：src/grouper/app.py:33、src/grouper/app.py:44
  - 每位老师自定义分配数量
      - 新增解析函数，支持在老师名字后标注人数，例如“张三:3”“张三（3）”“张三 x3”“张三 = 3”。未标注的老师使用上方的默认值。
      - 分配逻辑支持 per-teacher 覆盖值，按洗牌后的学生顺序分配，最多分配到“总人数或总需求”中的较小值。
      - 变更位置：src/grouper/logic.py:1、src/grouper/logic.py:29、src/grouper/logic.py:53
      - UI 提示更新（占位文本说明了可用格式）：src/grouper/app.py:83
  - Windows 打包无法生成 exe
      - 改用绝对包导入（避免脚本入口相对导入在打包时失败）。
      - PyInstaller 增加搜索路径 --paths src，确保能解析包名 grouper。
      - 打包脚本更新：x86_64/build_windows.bat:14
      - 运行时设置文件写入位置在打包环境改为用户可写目录（避免写入 _MEIPASS 导致失败）。Windows 使用 %APPDATA%/Grouper/x86_64/
        settings.json，macOS 使用 ~/Library/Application Support/Grouper/x86_64/settings.json，Linux 使用 ~/.config/grouper/x86_64/
        settings.json。
      - 变更位置：src/grouper/config.py:1、src/grouper/config.py:22、src/grouper/config.py:44、src/grouper/config.py:62、src/
        grouper/config.py:76

  附带更新

  - 文档与提示
      - 在中文说明与教程中补充“老师后写人数”的可用格式：说明.md:3、Grouper tutorial.md:16
  - 基础测试
      - 新增解析与分配逻辑的单测：tests/test_logic.py:1

  如何使用（验证修复）

  - 运行应用
      - 安装：python -m venv .venv && source .venv/bin/activate && pip install -e .
      - 启动：python3 -m grouper.app 或执行脚本入口 grouper
  - 老师自定义人数
      - 在“老师名单”里使用如“张三:3”“李四（2）”“王五 x1”；未写人数则使用“每位老师分配学生数”的默认值
  - 打包 Windows EXE
      - 将素材放在 x86_64/assets/（背景 backgroud-picture.jpg、欢迎 welcome-picture.jpg、样式 styles.css）
      - 运行：x86_64\build_windows.bat
      - 生成：dist\Grouper\Grouper.exe

  建议的下一步

  - 要不要我运行本地测试（pytest -q）并尝试一次打包以验证？
  - 如需内置字体文件（确保在无中文字体的机器也不乱码），可将字体放到 assets 并在启动时加载，它会稍微增大体积。
```

+ 01

```
主要功能

  - 粘贴老师/学生名单，多种分隔符自动解析。
  - 老师可在姓名后指定人数，如“张三:3”“张三（3）”“张三 x3”，未写则采用默认数量。
  - 指定“每位老师分配学生数”，基于时间戳生成整数随机种子并显示。
  - 一键“立即分组！”，导出 Excel 文件：Grouper_{年月日时分秒}_{整型随机种子}.xlsx。
  - 可设置“文件保存地址”，支持“打开目录”。
  - 欢迎界面支持 welcome-picture.jpg；背景支持 backgroud-picture.jpg（按提示名拼写）。
  - 样式通过 QSS（类 CSS）控制，默认半透明“毛玻璃”风格。
  - 设置（保存目录、分配数量、窗口尺寸、最近输入）自动持久化。

  如何运行

  - 安装依赖并运行
      - python -m venv .venv && source .venv/bin/activate
      - pip install -e .
      - python -m grouper.app  或运行脚本入口 grouper
  - 放置素材（可选）
      - 背景图：x86_64/assets/backgroud-picture.jpg
      - 欢迎图：x86_64/assets/welcome-picture.jpg
      - 样式：x86_64/assets/styles.css 可自定义

  打包 Windows 64 位 .exe

  - 执行 x86_64/build_windows.bat，会在 dist/Grouper/Grouper.exe 生成可执行文件。

  文件位置

  - 入口与界面：src/grouper/app.py:1
  - 分组与随机算法：src/grouper/logic.py:1
  - 配置与持久化、运行时路径：src/grouper/config.py:1
  - 样式加载（QSS）：src/grouper/styling.py:1
  - 资源与打包脚本：x86_64/assets/styles.css:1, x86_64/build_windows.bat:1
  - 项目元数据：pyproject.toml:1

  备注

  - 导出 .xlsx 依赖 openpyxl；若未安装会提示安装。
  - 初始窗口为 16:9，支持自由拖拽调整。若未提供图片，仍可正常使用（欢迎信息会以弹窗形式显示）。
    如需我帮你打包或微调样式/布局，请告诉我你的偏好。
```

