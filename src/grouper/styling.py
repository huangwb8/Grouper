from __future__ import annotations

from pathlib import Path

from .config import ASSETS_DIR


def styles_path() -> Path:
    return ASSETS_DIR / "styles.css"


def load_styles() -> str:
    css_file = styles_path()
    if css_file.exists():
        try:
            return css_file.read_text(encoding="utf-8")
        except Exception:
            pass
    # Fallback minimal frosted style with semi-transparent panels
    return (
        """
        QMainWindow { background-color: #1b1f2333; }
        QWidget#GlassPanel {
            background: rgba(255, 255, 255, 0.65);
            border-radius: 12px;
            border: 1px solid rgba(255,255,255,0.35);
        }
        QLineEdit, QTextEdit, QSpinBox {
            background: rgba(255,255,255,0.85);
            border: 1px solid #d0d7de;
            border-radius: 6px;
            padding: 6px;
        }
        QPushButton {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                       stop:0 #6cb2ff, stop:1 #367af6);
            border: none; color: white; padding: 8px 12px; border-radius: 8px;
        }
        QPushButton:hover { filter: brightness(1.05); }
        QPushButton:disabled { background: #a0a0a0; }
        QLabel#SeedLabel { color: #0f172a; font-weight: 600; }
        """
    )

