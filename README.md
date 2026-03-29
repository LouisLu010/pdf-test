# WinUI 3 PDF Annotator (C++/WinRT)

本仓库包含一款使用 WinUI 3（C++/WinRT）的 PDF 阅读与批注示例，支持：
- 打开本地 PDF，逐页渲染。
- 叠加墨迹批注（鼠标/触控/手写笔）。
- 画笔颜色、粗细可调。
- 橡皮擦模式可切换，粗细可调。

## 目录结构
- `PdfAnnotator.sln`：Visual Studio 解决方案。
- `PdfAnnotator/`：WinUI 3 C++ 项目源码（App/MainWindow、XAML、项目文件）。

## 主要实现
- `MainWindow.xaml`：工具栏（打开 PDF、ColorPicker、粗细滑块、橡皮擦切换）与滚动显示区域。
- `MainWindow.xaml.cpp`：使用 `Windows.Data.Pdf` 渲染每页为位图，叠加 `InkCanvas` 完成批注；统一调整画笔与橡皮擦属性。
- `App.xaml.*`：应用入口，创建主窗口。

## 构建与运行（Windows 11 + Visual Studio 2022）
1) 安装前置：
   - Visual Studio 2022（含“使用 C++ 的桌面开发”与“适用于 Windows 的 C++ CMake 工具集”或 MSBuild 工具）。
   - Windows 11 SDK（22621 或更新）。
   - Windows App SDK 1.5 及 C++/WinRT（VS 会通过 NuGet 自动还原）。
2) 克隆本仓库后双击 `PdfAnnotator.sln` 打开。
3) 首次打开时执行 NuGet 还原（VS 会自动提示）；确保 `Microsoft.WindowsAppSDK` 与 `Microsoft.Windows.CppWinRT` 包被恢复。
4) 选择 `x64` + `Debug` 或 `Release`，按 F5 运行。

### 运行时使用
1) 点击“打开 PDF”选择任意 PDF。应用会将每一页渲染成图片并纵向排列。
2) 在图片上直接书写批注。ColorPicker 和“画笔粗细”滑块实时影响新笔迹。
3) 勾选“橡皮擦”进入擦除模式，“橡皮粗细”滑块调整擦除半径；取消勾选返回书写模式。

## 备注
- 工程按 WinUI 3 非打包（WindowsPackageType=None）方式配置，运行时需要已安装的 Windows App SDK 运行时（默认随包恢复）。
- 如果使用自定义 SDK 版本，可在 `PdfAnnotator/PdfAnnotator.vcxproj` 的 `PackageReference` 版本号中调整。
