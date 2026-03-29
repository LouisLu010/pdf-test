#include "pch.h"
#include "MainWindow.xaml.h"

#include <winrt/Microsoft.UI.Xaml.Media.Imaging.h>
#include <winrt/Windows.Data.Pdf.h>
#include <winrt/Windows.Foundation.Collections.h>
#include <winrt/Windows.Storage.h>
#include <winrt/Windows.Storage.Pickers.h>
#include <winrt/Windows.Storage.Streams.h>
#include <winrt/Microsoft.UI.h>
#include <winrt/Microsoft.UI.Dispatching.h>
#include <winrt/Microsoft.UI.Windowing.h>
#include <winrt/Microsoft.UI.Interop.h>
#include <winrt/Microsoft.UI.Xaml.Input.h>
#include <winrt/Microsoft.UI.Xaml.Media.h>
#include <winrt/Microsoft.UI.Xaml.Media.Imaging.h>
#include <winrt/Microsoft.UI.Xaml.Shapes.h>
#include <winrt/Windows.UI.Core.h>
#include <microsoft.ui.xaml.window.h>

using namespace winrt;
using namespace Microsoft::UI::Xaml;
using namespace Microsoft::UI::Xaml::Controls;
using namespace Microsoft::UI::Xaml::Media;
using namespace Microsoft::UI::Xaml::Controls::Primitives;
using namespace Windows::Foundation;
using namespace Windows::Data::Pdf;
using namespace Windows::Storage;
using namespace Windows::Storage::Pickers;
using namespace Windows::Storage::Streams;
using namespace Microsoft::UI;
using namespace Microsoft::UI::Input::Inking;

namespace winrt::PdfAnnotator::implementation
{
    MainWindow::MainWindow()
    {
        InitializeComponent();
        InkColorPicker().Color(m_penColor);
        ApplyPenAttributes();
        ApplyEraserAttributes();
        SetModeForAll();
    }

    void MainWindow::OpenPdf_Click(IInspectable const&, RoutedEventArgs const&)
    {
        auto weak = get_weak();
        fire_and_forget
        {
            if (auto self = weak.get())
            {
                FileOpenPicker picker;
                picker.SuggestedStartLocation(PickerLocationId::DocumentsLibrary);
                picker.FileTypeFilter().Append(L".pdf");
                HWND hwnd{};
                if (auto windowNative = self->try_as<::IWindowNative>())
                {
                    winrt::check_hresult(windowNative->get_WindowHandle(&hwnd));
                    Microsoft::UI::Win32Interop::InitializeWithWindow(picker, hwnd);
                }

                StorageFile file = co_await picker.PickSingleFileAsync();
                if (file)
                {
                    co_await self->LoadPdfAsync(file);
                }
            }
        };
    }

    void MainWindow::InkColorChanged(ColorPicker const& sender, Controls::ColorChangedEventArgs const&)
    {
        m_penColor = sender.Color();
        ApplyPenAttributes();
    }

    void MainWindow::PenSizeChanged(IInspectable const&, RangeBaseValueChangedEventArgs const& args)
    {
        m_penSize = static_cast<float>(args.NewValue());
        ApplyPenAttributes();
    }

    void MainWindow::EraserSizeChanged(IInspectable const&, RangeBaseValueChangedEventArgs const& args)
    {
        m_eraserSize = static_cast<float>(args.NewValue());
        ApplyEraserAttributes();
    }

    void MainWindow::EraserToggle_Checked(IInspectable const&, RoutedEventArgs const&)
    {
        m_erasing = true;
        SetModeForAll();
    }

    void MainWindow::EraserToggle_Unchecked(IInspectable const&, RoutedEventArgs const&)
    {
        m_erasing = false;
        SetModeForAll();
    }

    void MainWindow::ApplyPenAttributes()
    {
        InkDrawingAttributes attributes;
        attributes.Color(m_penColor);
        attributes.Size({ m_penSize, m_penSize });
        attributes.IgnorePressure(false);
        attributes.PenTip(InkPenTipShape::Circle);

        for (auto const& canvas : m_canvases)
        {
            canvas.InkPresenter().UpdateDefaultDrawingAttributes(attributes);
        }
    }

    void MainWindow::ApplyEraserAttributes()
    {
        InkDrawingAttributes eraserAttributes;
        eraserAttributes.Size({ m_eraserSize, m_eraserSize });
        eraserAttributes.PenTip(InkPenTipShape::Circle);

        for (auto const& canvas : m_canvases)
        {
            canvas.InkPresenter().SetDefaultEraserAttributes(eraserAttributes);
        }
    }

    void MainWindow::SetModeForAll()
    {
        auto mode = m_erasing ? InkInputProcessingMode::Erasing : InkInputProcessingMode::Inking;
        for (auto const& canvas : m_canvases)
        {
            canvas.InkPresenter().InputProcessingConfiguration().Mode(mode);
        }
    }

    void MainWindow::ConfigureInkCanvas(InkCanvas const& canvas)
    {
        canvas.InkPresenter().InputDeviceTypes(
            Windows::UI::Core::CoreInputDeviceTypes::Mouse |
            Windows::UI::Core::CoreInputDeviceTypes::Pen |
            Windows::UI::Core::CoreInputDeviceTypes::Touch);

        canvas.InkPresenter().IsInputEnabled(true);
        canvas.InkPresenter().StrokeContainer().Clear();
        m_canvases.push_back(canvas);
    }

    void MainWindow::ClearDocument()
    {
        m_canvases.clear();
        PageHost().Children().Clear();
    }

    IAsyncAction MainWindow::LoadPdfAsync(StorageFile const& file)
    {
        ClearDocument();

        IRandomAccessStream stream = co_await file.OpenAsync(FileAccessMode::Read);
        PdfDocument document = co_await PdfDocument::LoadFromStreamAsync(stream);
        uint32_t pageCount = document.PageCount();
        for (uint32_t i = 0; i < pageCount; ++i)
        {
            co_await RenderPageAsync(document, i);
        }
    }

    IAsyncAction MainWindow::RenderPageAsync(PdfDocument const& document, uint32_t pageIndex)
    {
        PdfPage page = document.GetPage(pageIndex);

        Windows::Foundation::Size size = page.Size();
        InMemoryRandomAccessStream imageStream;
        PdfPageRenderOptions options;
        options.DestinationHeight(static_cast<uint32_t>(size.Height));
        options.DestinationWidth(static_cast<uint32_t>(size.Width));
        co_await page.RenderToStreamAsync(imageStream, options);
        page.Close();

        imageStream.Seek(0);

        Media::Imaging::BitmapImage bitmap;
        co_await bitmap.SetSourceAsync(imageStream);

        Image pdfImage;
        pdfImage.Source(bitmap);
        pdfImage.Stretch(Media::Stretch::Uniform);
        pdfImage.HorizontalAlignment(HorizontalAlignment::Left);

        InkCanvas inkCanvas;
        inkCanvas.Background(Media::SolidColorBrush{ Windows::UI::Colors::Transparent() });
        inkCanvas.VerticalAlignment(VerticalAlignment::Stretch);
        inkCanvas.HorizontalAlignment(HorizontalAlignment::Stretch);
        ConfigureInkCanvas(inkCanvas);

        ApplyPenAttributes();
        ApplyEraserAttributes();
        SetModeForAll();

        Grid container;
        container.HorizontalAlignment(HorizontalAlignment::Left);
        container.RowDefinitions().Append(RowDefinition{});
        container.ColumnDefinitions().Append(ColumnDefinition{});
        container.Children().Append(pdfImage);
        container.Children().Append(inkCanvas);

        Border border;
        border.BorderBrush(Media::SolidColorBrush{ Windows::UI::Colors::LightGray() });
        border.BorderThickness({ 1 });
        border.Child(container);

        PageHost().Children().Append(border);
        co_return;
    }
}
