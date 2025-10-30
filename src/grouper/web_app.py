from __future__ import annotations

import datetime as _dt
import os
import tempfile
from io import BytesIO
from pathlib import Path
from typing import Dict, List

from flask import (
    Flask,
    abort,
    flash,
    redirect,
    render_template_string,
    request,
    send_file,
    url_for,
)

from grouper.logic import (
    compute_seed_from_timestamp,
    group_students,
    parse_names_block,
    parse_teachers_with_counts,
)


DEFAULT_TEACHERS_TEXT = (
    "# 这是一个示例\n"
    "老师1:3\n"
    "老师2:1\n"
    "老师3:2"
)

DEFAULT_STUDENTS_TEXT = (
    "# 这是一个示例\n"
    "学生1\n"
    "学生2\n"
    "学生3\n"
    "学生4\n"
    "学生5\n"
    "学生6"
)


EXPORT_ROOT = Path(os.environ.get("GROUPER_EXPORT_DIR", tempfile.gettempdir())) / "grouper-exports"
EXPORT_ROOT.mkdir(parents=True, exist_ok=True)


def _build_workbook(groups: Dict[str, List[str]], seed: int) -> BytesIO:
    try:
        from openpyxl import Workbook
    except Exception as exc:  # pragma: no cover - runtime dependency import guard
        raise RuntimeError("缺少 openpyxl，请先安装：pip install openpyxl") from exc

    wb = Workbook()
    ws = wb.active
    ws.title = "Groups"
    ws.append(["Teacher", "Students"])
    for teacher, students in groups.items():
        ws.append([teacher, ", ".join(students)])

    ws_summary = wb.create_sheet("Summary")
    total_students = sum(len(v) for v in groups.values())
    ws_summary.append(["Seed", seed])
    ws_summary.append(["Teachers", len(groups)])
    ws_summary.append(["Assigned Students", total_students])

    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer


PAGE_TEMPLATE = """
<!doctype html>
<html lang="zh">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Grouper 分组器 - Bensz</title>
  <style>
    body {
      font-family: "Microsoft YaHei", "PingFang SC", "Noto Sans CJK SC", sans-serif;
      margin: 0;
      background: linear-gradient(135deg, rgba(90, 114, 255, 0.3), rgba(55, 200, 154, 0.3));
      min-height: 100vh;
      color: #121212;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 24px;
    }
    .panel {
      width: min(1100px, 95vw);
      background: rgba(255, 255, 255, 0.78);
      border-radius: 18px;
      backdrop-filter: blur(16px);
      box-shadow: 0 20px 45px rgba(15, 20, 40, 0.18);
      padding: 32px;
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: 24px;
    }
    h1 {
      grid-column: 1 / -1;
      margin: 0 0 8px;
      font-size: 28px;
      letter-spacing: 0.5px;
      text-align: center;
    }
    form {
      grid-column: 1 / -1;
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
      gap: 20px;
    }
    label {
      font-weight: 600;
      margin-bottom: 8px;
      display: block;
    }
    textarea, input[type="number"], input[type="text"] {
      width: 100%;
      border-radius: 10px;
      border: 1px solid rgba(0, 0, 0, 0.1);
      padding: 12px;
      font-size: 15px;
      resize: vertical;
      background: rgba(255, 255, 255, 0.9);
    }
    textarea { min-height: 180px; }
    .actions {
      grid-column: 1 / -1;
      display: flex;
      gap: 12px;
      flex-wrap: wrap;
      align-items: center;
    }
    button {
      border: none;
      padding: 12px 24px;
      border-radius: 999px;
      background: linear-gradient(135deg, #5a72ff, #37c89a);
      color: white;
      font-size: 16px;
      cursor: pointer;
      box-shadow: 0 10px 20px rgba(90, 114, 255, 0.24);
      transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    button:hover {
      transform: translateY(-2px);
      box-shadow: 0 14px 28px rgba(90, 114, 255, 0.28);
    }
    .summary, .results {
      grid-column: 1 / -1;
      background: rgba(255, 255, 255, 0.82);
      border-radius: 14px;
      padding: 20px;
      border: 1px solid rgba(255, 255, 255, 0.5);
    }
    table {
      width: 100%;
      border-collapse: collapse;
      margin-top: 12px;
    }
    th, td {
      border: 1px solid rgba(0, 0, 0, 0.08);
      padding: 10px 12px;
      text-align: left;
    }
    th { background: rgba(90, 114, 255, 0.1); }
    .flash {
      grid-column: 1 / -1;
      padding: 12px 16px;
      border-radius: 12px;
      background: rgba(244, 67, 54, 0.12);
      color: #b71c1c;
      border: 1px solid rgba(244, 67, 54, 0.22);
    }
    .download-link a {
      color: #304ffe;
      font-weight: 600;
      text-decoration: none;
    }
    .download-link a:hover {
      text-decoration: underline;
    }
  </style>
</head>
<body>
  <div class="panel">
    <h1>Grouper 分组器 by Bensz</h1>
    {% with messages = get_flashed_messages() %}
      {% if messages %}
        {% for msg in messages %}
          <div class="flash">{{ msg }}</div>
        {% endfor %}
      {% endif %}
    {% endwith %}

    <form method="post">
      <div>
        <label for="teachers">老师配置</label>
        <textarea id="teachers" name="teachers">{{ teachers_text }}</textarea>
      </div>
      <div>
        <label for="students">学生名单</label>
        <textarea id="students" name="students">{{ students_text }}</textarea>
      </div>
      <div>
        <label for="per_teacher">默认每位老师的学生数</label>
        <input id="per_teacher" name="per_teacher" type="number" min="0" value="{{ per_teacher }}" />
      </div>
      <div>
        <label for="export_dir">文件保存目录（容器内路径）</label>
        <input id="export_dir" name="export_dir" type="text" value="{{ export_dir }}" />
      </div>
      <div class="actions">
        <button type="submit">立即分组！</button>
      </div>
    </form>

    {% if summary %}
      <div class="summary">
        <h2>汇总信息</h2>
        <p>随机种子：<strong>{{ summary.seed }}</strong></p>
        <p>教师数：{{ summary.teacher_count }} ｜ 学生数：{{ summary.student_count }} ｜ 已分配：{{ summary.assigned_students }}</p>
        <p>生成文件：<code>{{ summary.filename }}</code></p>
        <p class="download-link"><a href="{{ url_for('download_file', filename=summary.filename, export_dir=summary.export_dir) }}" target="_blank">下载 Excel 文件</a></p>
        {% if summary.unassigned %}
          <p>未分配学生：{{ summary.unassigned|join(', ') }}</p>
        {% endif %}
      </div>
    {% endif %}

    {% if results %}
      <div class="results">
        <h2>分组结果</h2>
        <table>
          <thead>
            <tr><th>老师</th><th>学生</th></tr>
          </thead>
          <tbody>
            {% for teacher, students in results.items() %}
              <tr>
                <td>{{ teacher }}</td>
                <td>{{ students|join(', ') }}</td>
              </tr>
            {% endfor %}
          </tbody>
        </table>
      </div>
    {% endif %}
  </div>
</body>
</html>
"""


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("GROUPER_SECRET_KEY", "replace-me")

    @app.route("/", methods=["GET", "POST"])
    def index():
        teachers_text = DEFAULT_TEACHERS_TEXT
        students_text = DEFAULT_STUDENTS_TEXT
        per_teacher = 1
        export_dir = str(EXPORT_ROOT)
        results: Dict[str, List[str]] | None = None
        summary_payload = None

        def _render():
            return render_template_string(
                PAGE_TEMPLATE,
                teachers_text=teachers_text,
                students_text=students_text,
                per_teacher=per_teacher,
                export_dir=export_dir,
                results=results,
                summary=summary_payload,
            )

        if request.method == "POST":
            teachers_text = request.form.get("teachers", DEFAULT_TEACHERS_TEXT)
            students_text = request.form.get("students", DEFAULT_STUDENTS_TEXT)
            export_dir = request.form.get("export_dir", str(EXPORT_ROOT)).strip() or str(EXPORT_ROOT)
            try:
                per_teacher = int(request.form.get("per_teacher", "1"))
                if per_teacher < 0:
                    raise ValueError
            except (TypeError, ValueError):
                flash("每位老师的学生数必须是非负整数。")
                return _render()

            teachers, counts = parse_teachers_with_counts(teachers_text)
            students = parse_names_block(students_text)

            if not teachers:
                flash("请至少输入一位老师。")
                return _render()
            if not students:
                flash("请至少输入一位学生。")
                return _render()

            desired_total = sum(counts.get(t, per_teacher) for t in teachers)
            if desired_total > len(students):
                flash("老师期望的学生数超过学生总数，请检查输入。")
                return _render()

            seed = compute_seed_from_timestamp()
            groups = group_students(students, teachers, per_teacher, seed, counts)

            results = groups
            assigned = sum(len(v) for v in groups.values())
            assigned_set = {item for sub in groups.values() for item in sub}
            unassigned = [s for s in students if s not in assigned_set]

            timestamp = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"Grouper_{timestamp}_{seed}.xlsx"

            target_dir = Path(export_dir)
            try:
                target_dir.mkdir(parents=True, exist_ok=True)
            except OSError:
                flash("无法创建保存目录，请检查权限或路径。")
                return _render()

            workbook = _build_workbook(groups, seed)
            target_path = target_dir / filename
            with target_path.open("wb") as fh:
                fh.write(workbook.getvalue())

            summary_payload = {
                "seed": seed,
                "teacher_count": len(teachers),
                "student_count": len(students),
                "assigned_students": assigned,
                "filename": filename,
                "unassigned": unassigned,
                "export_dir": str(target_dir),
            }

        return _render()

    @app.route("/download/<path:filename>")
    def download_file(filename: str):
        safe_name = Path(filename).name
        export_dir_arg = request.args.get("export_dir")
        base_dir = Path(export_dir_arg) if export_dir_arg else EXPORT_ROOT
        target = Path(base_dir) / safe_name
        if not target.exists():
            abort(404)
        return send_file(target, as_attachment=True, download_name=safe_name)

    return app


def main() -> None:
    app = create_app()
    host = os.environ.get("GROUPER_WEB_HOST", "0.0.0.0")
    port = int(os.environ.get("GROUPER_WEB_PORT", "8000"))
    app.run(host=host, port=port)


if __name__ == "__main__":
    main()
