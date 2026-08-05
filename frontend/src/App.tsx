import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { ConfigProvider, theme } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import AppLayout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Empirical from './pages/Empirical'
import Quant from './pages/Quant'
import Report from './pages/Report'
import Paper from './pages/Paper'
import Macro from './pages/Macro'
import Chat from './pages/Chat'
import ResearchGuide from './pages/ResearchGuide'
import FinanceReport from './pages/FinanceReport'

function App() {
  return (
    <ConfigProvider
      locale={zhCN}
      theme={{
        algorithm: theme.defaultAlgorithm,
        token: {
          colorPrimary: '#1677ff',
          borderRadius: 8,
          fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "PingFang SC", "Microsoft YaHei", sans-serif',
        },
      }}
    >
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<AppLayout />}>
            <Route index element={<Dashboard />} />
            <Route path="empirical" element={<Empirical />} />
            <Route path="quant" element={<Quant />} />
            <Route path="report" element={<Report />} />
            <Route path="paper" element={<Paper />} />
            <Route path="macro" element={<Macro />} />
            <Route path="chat" element={<Chat />} />
            <Route path="research-guide" element={<ResearchGuide />} />
            <Route path="finance-report" element={<FinanceReport />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </ConfigProvider>
  )
}

export default App
