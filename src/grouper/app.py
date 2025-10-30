from __future__ import annotations

import datetime as _dt
import os
import sys
from pathlib import Path
from typing import Dict, List

from grouper.config import Settings, ensure_runtime_dirs, ASSETS_DIR
from grouper.logic import (
    compute_seed_from_timestamp,
    group_students,
    parse_names_block,
    parse_teachers_with_counts,
)
from grouper.styling import load_styles


def _try_open_directory(path: str) -> None:
    p = Path(path).resolve()
    if sys.platform.startswith("win"):
        os.startfile(str(p))  # type: ignore[attr-defined]
    elif sys.platform == "darwin":
        os.system(f'open "{p}"')
    else:
        os.system(f'xdg-open "{p}"')


def _export_xlsx(output_path: Path, groups: Dict[str, List[str]], seed: int) -> None:
    try:
        from openpyxl import Workbook
    except Exception as e:  # pragma: no cover - runtime dependency
        raise RuntimeError("缺少 openpyxl，请先安装：pip install openpyxl") from e

    wb = Workbook()
    ws = wb.active
    ws.title = "Groups"
    ws.append(["Teacher", "Students"])
    for teacher, students in groups.items():
        ws.append([teacher, ", ".join(students)])

    ws2 = wb.create_sheet("Summary")
    total_students = sum(len(v) for v in groups.values())
    ws2.append(["Seed", seed])
    ws2.append(["Teachers", len(groups)])
    ws2.append(["Assigned Students", total_students])
    wb.save(str(output_path))


def main() -> None:
    # In some Linux headless environments (no X11/Wayland), Qt cannot
    # initialize the default xcb/wayland platform plugin and aborts.
    # Detect that situation early and default to an offscreen platform
    # so the process does not crash during QApplication creation.
    try:
        if sys.platform.startswith("linux"):
            has_display = bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))
            if not has_display and not os.environ.get("QT_QPA_PLATFORM"):
                os.environ["QT_QPA_PLATFORM"] = "offscreen"
    except Exception:
        # If detection fails for any reason, continue with defaults.
        pass

    # Lazy import Qt to avoid import costs during tooling
    from PySide6.QtCore import Qt, QSize, QUrl
    from PySide6.QtGui import (
        QPixmap,
        QFont,
        QFontDatabase,
        QIcon,
        QPalette,
        QBrush,
        QDesktopServices,
        QPainter,
    )
    from PySide6.QtWidgets import (
        QApplication,
        QFileDialog,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QMainWindow,
        QMessageBox,
        QPushButton,
        QSpinBox,
        QSplashScreen,
        QTextEdit,
        QVBoxLayout,
        QWidget,
        QFrame,
    )

    ensure_runtime_dirs()

    app = QApplication(sys.argv)
    app.setApplicationName("Grouper")

    app_icon: QIcon | None = None
    logo_path = ASSETS_DIR / "logo.jpg"
    if logo_path.exists():
        icon = QIcon(str(logo_path))
        if not icon.isNull():
            app.setWindowIcon(icon)
            app_icon = icon

    # Prefer system fonts that have robust CJK glyph coverage to avoid garbled text
    try:
        families_win = ["Microsoft YaHei", "微软雅黑", "SimHei", "SimSun", "Segoe UI"]
        families_mac = ["PingFang SC", "Heiti SC", "Hiragino Sans GB", "Songti SC"]
        families_lin = ["Noto Sans CJK SC", "WenQuanYi Micro Hei", "Source Han Sans CN", "DejaVu Sans"]
        fams = families_lin
        if sys.platform.startswith("win"):
            fams = families_win
        elif sys.platform == "darwin":
            fams = families_mac
        db = QFontDatabase()
        chosen = None
        for f in fams:
            if f in db.families():
                chosen = f
                break
        if chosen:
            app.setFont(QFont(chosen, 10))
    except Exception:
        pass

    # Splash / Welcome
    welcome_image = ASSETS_DIR / "welcome-picture.jpg"  # prompt's specified name
    splash: QSplashScreen | None = None
    if welcome_image.exists():
        pm = QPixmap(str(welcome_image))
        if not pm.isNull():
            target_size = QSize(1280, 720)
            scaled = pm.scaled(target_size, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
            splash = QSplashScreen(scaled)
            splash.setFixedSize(target_size)
            splash.showMessage(
                "开发者：黄伟斌\n版本：v20251030",
                alignment=Qt.AlignBottom | Qt.AlignHCenter,
            )
            splash.show()
    else:
        QMessageBox.information(None, "欢迎", "开发者：黄伟斌\n版本：v20251030")

    TEACHERS_SAMPLE = (
        "# 这是一个示例\n"
        "老师1:3\n"
        "老师2:1\n"
        "老师3:2"
    )

    STUDENTS_SAMPLE = (
        "# 这是一个示例\n"
        "学生1\n"
        "学生2\n"
        "学生3\n"
        "学生4\n"
        "学生5\n"
        "学生6"
    )

    class Main(QMainWindow):
        def __init__(self) -> None:
            super().__init__()
            self.setWindowTitle("Grouper 分组器")
            self.resize(1280, 720)  # 16:9 default
            if app_icon is not None:
                self.setWindowIcon(app_icon)

            self.settings = Settings.load()
            self._app = app
            base_font = self._app.font()
            initial_size = self.settings.font_size or base_font.pointSize() or 10
            self._current_font_size = int(initial_size)
            self._apply_font_size(self._current_font_size)

            # Central frosted panel
            central = QWidget()
            layout = QVBoxLayout(central)

            panel = QFrame(objectName="GlassPanel")
            panel_layout = QVBoxLayout(panel)
            panel_layout.setSpacing(10)

            font_row = QHBoxLayout()
            font_row.addWidget(QLabel("字体大小："))
            btn_zoom_in = QPushButton("放大")
            btn_zoom_out = QPushButton("缩小")
            font_row.addWidget(btn_zoom_in)
            font_row.addWidget(btn_zoom_out)
            font_row.addStretch(1)
            panel_layout.addLayout(font_row)

            # Seed label
            self.seed_val = compute_seed_from_timestamp()
            self.seed_label = QLabel(f"当前随机种子：{self.seed_val}", objectName="SeedLabel")
            panel_layout.addWidget(self.seed_label)

            # Save directory chooser
            row1 = QHBoxLayout()
            self.save_dir_edit = QLineEdit(self.settings.save_dir or os.getcwd())
            btn_browse = QPushButton("浏览…")
            btn_open = QPushButton("打开目录")
            row1.addWidget(QLabel("文件保存地址："))
            row1.addWidget(self.save_dir_edit, 1)
            row1.addWidget(btn_browse)
            row1.addWidget(btn_open)
            panel_layout.addLayout(row1)

            # Teachers
            self.teachers_edit = QTextEdit()
            self.teachers_edit.setPlaceholderText(
                "在此粘贴老师姓名，每行一个或用逗号分隔…\n"
                "可在老师后写数量，如：张三:3、张三（3）、张三 x3；未写则采用默认。"
            )
            teacher_text = self.settings.teachers_text or TEACHERS_SAMPLE
            self.teachers_edit.setText(teacher_text)
            panel_layout.addWidget(QLabel("老师名单："))
            panel_layout.addWidget(self.teachers_edit)

            # Students
            self.students_edit = QTextEdit()
            self.students_edit.setPlaceholderText("在此粘贴学生姓名，每行一个或用逗号分隔…")
            student_text = self.settings.students_text or STUDENTS_SAMPLE
            self.students_edit.setText(student_text)
            panel_layout.addWidget(QLabel("学生名单："))
            panel_layout.addWidget(self.students_edit)

            # per teacher count
            row2 = QHBoxLayout()
            row2.addWidget(QLabel("每位老师分配学生数："))
            self.per_spin = QSpinBox()
            self.per_spin.setRange(0, 999)
            self.per_spin.setValue(int(self.settings.per_teacher))
            row2.addWidget(self.per_spin)
            row2.addStretch(1)
            panel_layout.addLayout(row2)

            # Action button
            self.btn_go = QPushButton("立即分组！")
            panel_layout.addWidget(self.btn_go)

            layout.addStretch(1)
            layout.addWidget(panel)
            layout.addStretch(1)
            self.setCentralWidget(central)
            self._central_widget = central

            self._bg_pixmap: QPixmap | None = None
            bg_path = ASSETS_DIR / "backgroud-picture.jpg"
            if bg_path.exists():
                bg_pm = QPixmap(str(bg_path))
                if not bg_pm.isNull():
                    self._bg_pixmap = bg_pm

            # Apply stylesheet and background
            app.setStyleSheet(load_styles())
            self._update_background()

            # Signals
            btn_open.clicked.connect(self._open_dir)
            btn_browse.clicked.connect(self._browse_dir)
            self.btn_go.clicked.connect(self._run_grouping)
            btn_zoom_in.clicked.connect(lambda: self._change_font_size(1))
            btn_zoom_out.clicked.connect(lambda: self._change_font_size(-1))

            # Restore geometry
            if self.settings.geometry:
                try:
                    self.restoreGeometry(bytes.fromhex(self.settings.geometry))
                except Exception:
                    pass

        def _update_background(self) -> None:
            if self._bg_pixmap is None:
                return
            size = self.size()
            if size.width() <= 0 or size.height() <= 0:
                return

            scaled = self._bg_pixmap.scaled(
                size,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
            canvas = QPixmap(size)
            canvas.fill(Qt.transparent)

            painter = QPainter(canvas)
            x = (size.width() - scaled.width()) // 2
            y = (size.height() - scaled.height()) // 2
            painter.drawPixmap(x, y, scaled)
            painter.end()

            brush = QBrush(canvas)
            palette = self.palette()
            palette.setBrush(QPalette.Window, brush)
            self.setAutoFillBackground(True)
            self.setPalette(palette)

            central = getattr(self, "_central_widget", None)
            if central is not None:
                cpal = central.palette()
                cpal.setBrush(QPalette.Window, brush)
                central.setAutoFillBackground(True)
                central.setPalette(cpal)

        def resizeEvent(self, event):  # type: ignore[override]
            super().resizeEvent(event)
            self._update_background()

        def _open_dir(self) -> None:
            _try_open_directory(self.save_dir_edit.text().strip() or ".")

        def _browse_dir(self) -> None:
            path = QFileDialog.getExistingDirectory(self, "选择保存目录", self.save_dir_edit.text() or os.getcwd())
            if path:
                self.save_dir_edit.setText(path)

        def closeEvent(self, event):  # type: ignore[override]
            # Persist settings
            s = Settings(
                save_dir=self.save_dir_edit.text().strip() or os.getcwd(),
                per_teacher=int(self.per_spin.value()),
                students_text=self.students_edit.toPlainText(),
                teachers_text=self.teachers_edit.toPlainText(),
                geometry=self.saveGeometry().hex(),
                font_size=self._current_font_size,
            )
            try:
                s.save()
            except Exception:
                pass
            super().closeEvent(event)

        def _change_font_size(self, delta: int) -> None:
            self._apply_font_size(self._current_font_size + delta)

        def _apply_font_size(self, size: int) -> None:
            try:
                size_int = max(8, min(32, int(size)))
            except (TypeError, ValueError):
                size_int = 10
            font = self._app.font()
            font.setPointSize(size_int)
            self._app.setFont(font)
            self.setFont(font)
            for widget in self.findChildren(QWidget):
                widget.setFont(font)
            self._current_font_size = size_int

        def _run_grouping(self) -> None:
            # compute fresh seed based on timestamp
            seed = compute_seed_from_timestamp()
            self.seed_val = seed
            self.seed_label.setText(f"当前随机种子：{seed}")

            students = parse_names_block(self.students_edit.toPlainText())
            teachers, counts = parse_teachers_with_counts(self.teachers_edit.toPlainText())
            per = int(self.per_spin.value())

            if not teachers:
                QMessageBox.warning(self, "提示", "请录入至少1位老师。")
                return
            if per <= 0:
                QMessageBox.warning(self, "提示", "每位老师分配学生数应大于0。")
                return
            if not students:
                QMessageBox.warning(self, "提示", "请录入学生名单。")
                return

            groups = group_students(students, teachers, per, seed, counts)

            # Export
            stamp = _dt.datetime.now().strftime("%Y%m%d%H%M%S")
            filename = f"Grouper_{stamp}_{seed}.xlsx"
            save_dir = Path(self.save_dir_edit.text().strip() or ".").resolve()
            save_dir.mkdir(parents=True, exist_ok=True)
            out = save_dir / filename
            try:
                _export_xlsx(out, groups, seed)
            except Exception as e:
                QMessageBox.critical(self, "导出失败", str(e))
                return

            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Information)
            msg.setWindowTitle("分组完成！")
            msg.setText(f"已保存到：\n{out}")
            open_btn = msg.addButton("打开文件", QMessageBox.ActionRole)
            msg.addButton("确定", QMessageBox.AcceptRole)
            msg.exec()
            if msg.clickedButton() == open_btn:
                QDesktopServices.openUrl(QUrl.fromLocalFile(str(out)))

    win = Main()
    if splash is not None:
        splash.finish(win)
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
