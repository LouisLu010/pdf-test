# PDF 阅读与绘图工具

一款 Windows 桌面软件，可以打开 PDF 文件、在页面上自由绘图，并将注释保存回新的 PDF。

## 功能

- 📂 **打开 PDF**：支持多页 PDF 文件
- ✏️ **画笔工具**：在 PDF 页面上自由绘图
- 🎨 **颜色选择**：通过颜色对话框自由选择画笔颜色
- 🔢 **画笔大小**：通过滑块调整画笔粗细（1–50px）
- 🧹 **橡皮擦工具**：擦除已绘制的线条
- 🔢 **橡皮大小**：通过滑块调整橡皮擦大小（5–100px）
- 🔍 **缩放**：25%–300% 缩放比例
- ◀▶ **翻页**：支持多页 PDF 导航
- 💾 **保存**：将注释平铺到 PDF 并保存为新文件
- 🗑 **清除**：一键清除当前页的全部绘图

## 安装

需要 Python 3.8+。

```bash
pip install -r requirements.txt
```

## 运行

```bash
python main.py
```

## 快捷键

| 快捷键 | 功能 |
|--------|------|
| `Ctrl+O` | 打开 PDF |
| `Ctrl+S` | 保存注释 PDF |
| `←` | 上一页 |
| `→` | 下一页 |

## 依赖

- [PyMuPDF](https://pymupdf.readthedocs.io/)（PDF 渲染）
- [PyQt5](https://www.riverbankcomputing.com/software/pyqt/)（GUI 框架）