"""
PDF Viewer with Drawing Tools
A Windows application for reading PDFs and drawing on them.
"""

import sys
import os
import fitz  # PyMuPDF
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QScrollArea,
    QToolBar, QAction, QSlider, QLabel, QPushButton,
    QFileDialog, QColorDialog, QMessageBox, QStatusBar
)
from PyQt5.QtGui import (
    QPixmap, QImage, QPainter, QPen, QColor
)
from PyQt5.QtCore import Qt, QPoint, QSize


class DrawingCanvas(QWidget):
    """
    A widget that displays a single PDF page and allows freehand drawing on top.
    Supports pen drawing and erasing with adjustable sizes and colors.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._page_pixmap = None        # The rendered PDF page
        self._drawing_pixmap = None     # Transparent layer for annotations
        self._scaled_page = None        # Cached scaled version for display
        self._scaled_drawing = None     # Cached scaled drawing overlay

        self._zoom = 1.0
        self._tool = "pen"              # "pen" or "eraser"
        self._pen_color = QColor(Qt.red)
        self._pen_size = 3
        self._eraser_size = 20

        self._last_point = None
        self._drawing = False

        self.setMouseTracking(True)
        self.setCursor(Qt.CrossCursor)

    # ------------------------------------------------------------------
    # Page management
    # ------------------------------------------------------------------

    def set_page_pixmap(self, pixmap: QPixmap):
        """Load a rendered PDF page and reset the drawing layer."""
        self._page_pixmap = pixmap
        # Create a transparent drawing layer the same size as the page
        self._drawing_pixmap = QPixmap(pixmap.size())
        self._drawing_pixmap.fill(Qt.transparent)
        self._update_cache()
        self.adjustSize()
        self.update()

    def get_drawing_pixmap(self) -> QPixmap:
        return self._drawing_pixmap

    # ------------------------------------------------------------------
    # Tool / style setters
    # ------------------------------------------------------------------

    def set_tool(self, tool: str):
        self._tool = tool
        if tool == "eraser":
            self.setCursor(Qt.BlankCursor)
        else:
            self.setCursor(Qt.CrossCursor)

    def set_pen_color(self, color: QColor):
        self._pen_color = color

    def set_pen_size(self, size: int):
        self._pen_size = size

    def set_eraser_size(self, size: int):
        self._eraser_size = size

    def clear_drawing(self):
        """Erase all annotations on the current page."""
        if self._drawing_pixmap:
            self._drawing_pixmap.fill(Qt.transparent)
            self._update_cache()
            self.update()

    def set_zoom(self, zoom: float):
        self._zoom = zoom
        self._update_cache()
        self.adjustSize()
        self.update()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _update_cache(self):
        if self._page_pixmap is None:
            return
        w = int(self._page_pixmap.width() * self._zoom)
        h = int(self._page_pixmap.height() * self._zoom)
        self._scaled_page = self._page_pixmap.scaled(
            w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        if self._drawing_pixmap:
            self._scaled_drawing = self._drawing_pixmap.scaled(
                w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )

    def _canvas_to_page(self, point: QPoint) -> QPoint:
        """Convert a canvas coordinate to the native page coordinate."""
        if self._zoom == 0 or self._page_pixmap is None:
            return point
        return QPoint(
            int(point.x() / self._zoom),
            int(point.y() / self._zoom)
        )

    # ------------------------------------------------------------------
    # Qt overrides
    # ------------------------------------------------------------------

    def sizeHint(self) -> QSize:
        if self._scaled_page:
            return self._scaled_page.size()
        return QSize(800, 600)

    def paintEvent(self, event):
        painter = QPainter(self)
        if self._scaled_page:
            painter.drawPixmap(0, 0, self._scaled_page)
        if self._scaled_drawing:
            painter.drawPixmap(0, 0, self._scaled_drawing)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self._drawing_pixmap:
            self._drawing = True
            self._last_point = self._canvas_to_page(event.pos())

    def mouseMoveEvent(self, event):
        if self._drawing and (event.buttons() & Qt.LeftButton) and self._drawing_pixmap:
            current = self._canvas_to_page(event.pos())
            self._draw_line(self._last_point, current)
            self._last_point = current
            # Refresh scaled drawing cache
            if self._page_pixmap:
                w = int(self._page_pixmap.width() * self._zoom)
                h = int(self._page_pixmap.height() * self._zoom)
                self._scaled_drawing = self._drawing_pixmap.scaled(
                    w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drawing = False
            self._last_point = None

    def _draw_line(self, p1: QPoint, p2: QPoint):
        """Paint a stroke onto the native-resolution drawing layer."""
        painter = QPainter(self._drawing_pixmap)
        painter.setRenderHint(QPainter.Antialiasing, True)

        if self._tool == "eraser":
            painter.setCompositionMode(QPainter.CompositionMode_Clear)
            pen = QPen(Qt.transparent, self._eraser_size, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        else:
            painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
            pen = QPen(self._pen_color, self._pen_size, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)

        painter.setPen(pen)
        painter.drawLine(p1, p2)
        painter.end()


class PDFViewerWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self._doc = None
        self._current_page = 0
        self._total_pages = 0
        self._zoom = 1.0
        self._pen_color = QColor(Qt.red)
        self._pen_size = 3
        self._eraser_size = 20

        self._canvases = []   # One DrawingCanvas per page
        self._current_canvas: DrawingCanvas = None

        self._init_ui()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _init_ui(self):
        self.setWindowTitle("PDF 阅读与绘图工具")
        self.resize(1100, 800)

        # ---- Toolbar ------------------------------------------------
        toolbar = QToolBar("工具栏", self)
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(24, 24))
        self.addToolBar(toolbar)

        # Open file
        act_open = QAction("📂 打开 PDF", self)
        act_open.setShortcut("Ctrl+O")
        act_open.triggered.connect(self._open_pdf)
        toolbar.addAction(act_open)

        # Save annotated PDF
        act_save = QAction("💾 保存", self)
        act_save.setShortcut("Ctrl+S")
        act_save.triggered.connect(self._save_pdf)
        toolbar.addAction(act_save)

        toolbar.addSeparator()

        # Pen tool
        act_pen = QAction("✏️ 画笔", self)
        act_pen.setCheckable(True)
        act_pen.setChecked(True)
        act_pen.triggered.connect(lambda: self._set_tool("pen"))
        self._act_pen = act_pen
        toolbar.addAction(act_pen)

        # Eraser tool
        act_eraser = QAction("🧹 橡皮擦", self)
        act_eraser.setCheckable(True)
        act_eraser.triggered.connect(lambda: self._set_tool("eraser"))
        self._act_eraser = act_eraser
        toolbar.addAction(act_eraser)

        toolbar.addSeparator()

        # Color picker
        self._color_btn = QPushButton()
        self._color_btn.setFixedSize(32, 32)
        self._color_btn.setToolTip("选择画笔颜色")
        self._update_color_button()
        self._color_btn.clicked.connect(self._pick_color)
        toolbar.addWidget(self._color_btn)

        toolbar.addSeparator()

        # Pen size
        toolbar.addWidget(QLabel(" 画笔大小: "))
        self._pen_slider = QSlider(Qt.Horizontal)
        self._pen_slider.setRange(1, 50)
        self._pen_slider.setValue(self._pen_size)
        self._pen_slider.setFixedWidth(100)
        self._pen_slider.setToolTip("画笔大小")
        self._pen_slider.valueChanged.connect(self._on_pen_size_changed)
        toolbar.addWidget(self._pen_slider)
        self._pen_size_label = QLabel(str(self._pen_size))
        self._pen_size_label.setFixedWidth(24)
        toolbar.addWidget(self._pen_size_label)

        toolbar.addSeparator()

        # Eraser size
        toolbar.addWidget(QLabel(" 橡皮大小: "))
        self._eraser_slider = QSlider(Qt.Horizontal)
        self._eraser_slider.setRange(5, 100)
        self._eraser_slider.setValue(self._eraser_size)
        self._eraser_slider.setFixedWidth(100)
        self._eraser_slider.setToolTip("橡皮擦大小")
        self._eraser_slider.valueChanged.connect(self._on_eraser_size_changed)
        toolbar.addWidget(self._eraser_slider)
        self._eraser_size_label = QLabel(str(self._eraser_size))
        self._eraser_size_label.setFixedWidth(24)
        toolbar.addWidget(self._eraser_size_label)

        toolbar.addSeparator()

        # Zoom
        toolbar.addWidget(QLabel(" 缩放: "))
        self._zoom_slider = QSlider(Qt.Horizontal)
        self._zoom_slider.setRange(25, 300)
        self._zoom_slider.setValue(100)
        self._zoom_slider.setFixedWidth(120)
        self._zoom_slider.setToolTip("缩放比例")
        self._zoom_slider.valueChanged.connect(self._on_zoom_changed)
        toolbar.addWidget(self._zoom_slider)
        self._zoom_label = QLabel("100%")
        self._zoom_label.setFixedWidth(40)
        toolbar.addWidget(self._zoom_label)

        toolbar.addSeparator()

        # Page navigation
        act_prev = QAction("◀ 上一页", self)
        act_prev.setShortcut("Left")
        act_prev.triggered.connect(self._prev_page)
        toolbar.addAction(act_prev)

        self._page_label = QLabel("  第 0 / 0 页  ")
        toolbar.addWidget(self._page_label)

        act_next = QAction("▶ 下一页", self)
        act_next.setShortcut("Right")
        act_next.triggered.connect(self._next_page)
        toolbar.addAction(act_next)

        toolbar.addSeparator()

        # Clear current page drawing
        act_clear = QAction("🗑 清除本页", self)
        act_clear.triggered.connect(self._clear_page)
        toolbar.addAction(act_clear)

        # ---- Scroll area for the canvas ----------------------------
        self._scroll = QScrollArea()
        self._scroll.setAlignment(Qt.AlignCenter)
        self._scroll.setWidgetResizable(False)
        self.setCentralWidget(self._scroll)

        # ---- Status bar --------------------------------------------
        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("请打开一个 PDF 文件（Ctrl+O）")

    # ------------------------------------------------------------------
    # File operations
    # ------------------------------------------------------------------

    def _open_pdf(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "打开 PDF 文件", "", "PDF 文件 (*.pdf)"
        )
        if not path:
            return
        try:
            self._doc = fitz.open(path)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法打开文件：{e}")
            return

        self._total_pages = len(self._doc)
        self._current_page = 0
        # Build one canvas per page (they are rendered lazily via _load_page)
        self._canvases = [None] * self._total_pages
        self._load_page(0)
        self.setWindowTitle(f"PDF 阅读与绘图工具 — {os.path.basename(path)}")
        self.statusBar().showMessage(f"已打开：{path}（共 {self._total_pages} 页）")

    def _save_pdf(self):
        if self._doc is None:
            QMessageBox.information(self, "提示", "请先打开一个 PDF 文件。")
            return

        path, _ = QFileDialog.getSaveFileName(
            self, "保存注释 PDF", "", "PDF 文件 (*.pdf)"
        )
        if not path:
            return

        try:
            self._save_annotations_to_pdf(path)
            QMessageBox.information(self, "成功", f"已保存到：{path}")
            self.statusBar().showMessage(f"已保存：{path}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存失败：{e}")

    def _save_annotations_to_pdf(self, out_path: str):
        """
        Flatten the drawing layer onto each PDF page and write a new PDF.
        """
        import tempfile

        # Work on a copy so we don't corrupt the opened document
        doc_copy = fitz.open()
        doc_copy.insert_pdf(self._doc)

        for i, page in enumerate(doc_copy):
            canvas = self._canvases[i]
            if canvas is None:
                continue
            drawing_pm = canvas.get_drawing_pixmap()
            if drawing_pm is None or drawing_pm.isNull():
                continue

            # Save to a temp PNG file, then insert as annotation
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                tmp_path = tmp.name
            drawing_pm.save(tmp_path, "PNG")

            rect = page.rect
            page.insert_image(rect, filename=tmp_path, overlay=True)
            os.unlink(tmp_path)

        doc_copy.save(out_path)
        doc_copy.close()

    # ------------------------------------------------------------------
    # Page loading & navigation
    # ------------------------------------------------------------------

    def _load_page(self, index: int):
        if self._doc is None or index < 0 or index >= self._total_pages:
            return

        self._current_page = index

        # Render page if not already cached
        if self._canvases[index] is None:
            canvas = DrawingCanvas()
            canvas.set_pen_color(self._pen_color)
            canvas.set_pen_size(self._pen_size)
            canvas.set_eraser_size(self._eraser_size)
            canvas.set_zoom(self._zoom)
            canvas.set_tool("pen" if self._act_pen.isChecked() else "eraser")

            page = self._doc[index]
            mat = fitz.Matrix(2.0, 2.0)  # render at 2× for sharpness
            clip = page.get_pixmap(matrix=mat, alpha=False)
            img = QImage(
                clip.samples, clip.width, clip.height,
                clip.stride, QImage.Format_RGB888
            )
            canvas.set_page_pixmap(QPixmap.fromImage(img))
            self._canvases[index] = canvas
        else:
            canvas = self._canvases[index]
            # Propagate any tool/style changes
            canvas.set_pen_color(self._pen_color)
            canvas.set_pen_size(self._pen_size)
            canvas.set_eraser_size(self._eraser_size)
            canvas.set_zoom(self._zoom)

        self._current_canvas = canvas
        self._scroll.setWidget(canvas)
        self._page_label.setText(
            f"  第 {index + 1} / {self._total_pages} 页  "
        )

    def _prev_page(self):
        if self._current_page > 0:
            self._load_page(self._current_page - 1)

    def _next_page(self):
        if self._current_page < self._total_pages - 1:
            self._load_page(self._current_page + 1)

    # ------------------------------------------------------------------
    # Tool / style changes
    # ------------------------------------------------------------------

    def _set_tool(self, tool: str):
        self._act_pen.setChecked(tool == "pen")
        self._act_eraser.setChecked(tool == "eraser")
        if self._current_canvas:
            self._current_canvas.set_tool(tool)

    def _pick_color(self):
        color = QColorDialog.getColor(self._pen_color, self, "选择画笔颜色")
        if color.isValid():
            self._pen_color = color
            self._update_color_button()
            if self._current_canvas:
                self._current_canvas.set_pen_color(color)
            # Propagate to already-created canvases
            for c in self._canvases:
                if c:
                    c.set_pen_color(color)

    def _update_color_button(self):
        self._color_btn.setStyleSheet(
            f"background-color: {self._pen_color.name()}; border: 1px solid #888;"
        )

    def _on_pen_size_changed(self, value: int):
        self._pen_size = value
        self._pen_size_label.setText(str(value))
        if self._current_canvas:
            self._current_canvas.set_pen_size(value)

    def _on_eraser_size_changed(self, value: int):
        self._eraser_size = value
        self._eraser_size_label.setText(str(value))
        if self._current_canvas:
            self._current_canvas.set_eraser_size(value)

    def _on_zoom_changed(self, value: int):
        self._zoom = value / 100.0
        self._zoom_label.setText(f"{value}%")
        if self._current_canvas:
            self._current_canvas.set_zoom(self._zoom)

    def _clear_page(self):
        if self._current_canvas:
            self._current_canvas.clear_drawing()


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = PDFViewerWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
