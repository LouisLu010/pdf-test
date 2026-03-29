#include "pch.h"
#include "App.xaml.h"
#include "MainWindow.xaml.h"

using namespace winrt;
using namespace Microsoft::UI::Xaml;
using namespace Microsoft::UI::Xaml::Controls;

namespace winrt::PdfAnnotator::implementation
{
    App::App()
    {
        InitializeComponent();
    }

    void App::OnLaunched(LaunchActivatedEventArgs const&)
    {
        if (m_window == nullptr)
        {
            m_window = make<MainWindow>();
        }

        m_window.ExtendsContentIntoTitleBar(true);
        m_window.Title(L"WinUI3 PDF Annotator");
        m_window.Activate();
    }
}
