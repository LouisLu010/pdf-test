#pragma once

#include "MainWindow.g.h"

namespace winrt::PdfAnnotator::implementation
{
    struct MainWindow : MainWindowT<MainWindow>
    {
        MainWindow();

        void OpenPdf_Click(winrt::Windows::Foundation::IInspectable const& sender, winrt::Microsoft::UI::Xaml::RoutedEventArgs const& args);
        void InkColorChanged(winrt::Microsoft::UI::Xaml::Controls::ColorPicker const& sender, winrt::Microsoft::UI::Xaml::Controls::ColorChangedEventArgs const& args);
        void PenSizeChanged(winrt::Windows::Foundation::IInspectable const& sender, winrt::Microsoft::UI::Xaml::Controls::Primitives::RangeBaseValueChangedEventArgs const& args);
        void EraserSizeChanged(winrt::Windows::Foundation::IInspectable const& sender, winrt::Microsoft::UI::Xaml::Controls::Primitives::RangeBaseValueChangedEventArgs const& args);
        void EraserToggle_Checked(winrt::Windows::Foundation::IInspectable const& sender, winrt::Microsoft::UI::Xaml::RoutedEventArgs const& args);
        void EraserToggle_Unchecked(winrt::Windows::Foundation::IInspectable const& sender, winrt::Microsoft::UI::Xaml::RoutedEventArgs const& args);

    private:
        winrt::Windows::UI::Color m_penColor{ winrt::Windows::UI::Colors::Red() };
        float m_penSize{ 3.0f };
        float m_eraserSize{ 12.0f };
        bool m_erasing{ false };
        std::vector<winrt::Microsoft::UI::Xaml::Controls::InkCanvas> m_canvases;

        winrt::Windows::Foundation::IAsyncAction LoadPdfAsync(winrt::Windows::Storage::StorageFile const& file);
        winrt::Windows::Foundation::IAsyncAction RenderPageAsync(winrt::Windows::Data::Pdf::PdfDocument const& document, uint32_t pageIndex);
        void ConfigureInkCanvas(winrt::Microsoft::UI::Xaml::Controls::InkCanvas const& canvas);
        void ApplyPenAttributes();
        void ApplyEraserAttributes();
        void SetModeForAll();
        void ClearDocument();
    };
}

namespace winrt::PdfAnnotator::factory_implementation
{
    struct MainWindow : MainWindowT<MainWindow, implementation::MainWindow>
    {
    };
}
