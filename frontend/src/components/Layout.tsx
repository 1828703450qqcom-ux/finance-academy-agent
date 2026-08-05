import { useState, useEffect } from 'react'
import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import { Layout, Menu, Button, Space, Typography, Switch, Drawer } from 'antd'
import {
  DashboardOutlined,
  ExperimentOutlined,
  LineChartOutlined,
  FileTextOutlined,
  SearchOutlined,
  GlobalOutlined,
  MessageOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  BulbOutlined,
  BulbFilled,
  ReadOutlined,
  StockOutlined,
} from '@ant-design/icons'

const { Header, Sider, Content } = Layout
const { Title } = Typography

const menuItems = [
  { key: '/', icon: <DashboardOutlined />, label: '门户仪表盘' },
  { key: '/empirical', icon: <ExperimentOutlined />, label: '实证研究' },
  { key: '/research-guide', icon: <ReadOutlined />, label: '科研助手' },
  { key: '/quant', icon: <LineChartOutlined />, label: '量化回测' },
  { key: '/finance-report', icon: <StockOutlined />, label: 'AI财报研报' },
  { key: '/report', icon: <FileTextOutlined />, label: '财报解析' },
  { key: '/paper', icon: <SearchOutlined />, label: '论文检索' },
  { key: '/macro', icon: <GlobalOutlined />, label: '宏观数据' },
  { key: '/chat', icon: <MessageOutlined />, label: '智能问答' },
]

function useIsMobile() {
  const [isMobile, setIsMobile] = useState(window.innerWidth < 768)
  useEffect(() => {
    const handler = () => setIsMobile(window.innerWidth < 768)
    window.addEventListener('resize', handler)
    return () => window.removeEventListener('resize', handler)
  }, [])
  return isMobile
}

export default function AppLayout() {
  const [collapsed, setCollapsed] = useState(false)
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [darkMode, setDarkMode] = useState(false)
  const navigate = useNavigate()
  const location = useLocation()
  const isMobile = useIsMobile()

  useEffect(() => {
    if (isMobile) setCollapsed(true)
  }, [isMobile])

  useEffect(() => {
    setDrawerOpen(false)
  }, [location.pathname])

  const handleMenuClick = ({ key }: { key: string }) => {
    navigate(key)
    if (isMobile) setDrawerOpen(false)
  }

  const siderStyle = {
    background: darkMode ? '#141414' : '#fff',
    borderRight: '1px solid #f0f0f0',
    boxShadow: '2px 0 8px rgba(0,0,0,0.04)',
  }

  const menuContent = (
    <Menu
      mode="inline"
      selectedKeys={[location.pathname]}
      items={menuItems}
      onClick={handleMenuClick}
      style={{ border: 'none', background: 'transparent' }}
    />
  )

  return (
    <Layout style={{ minHeight: '100vh' }}>
      {/* Desktop sidebar */}
      {!isMobile && (
        <Sider
          collapsible
          collapsed={collapsed}
          trigger={null}
          theme={darkMode ? 'dark' : 'light'}
          style={siderStyle}
          width={220}
          collapsedWidth={60}
        >
          <div style={{
            padding: collapsed ? '16px 8px' : '16px 20px',
            borderBottom: '1px solid #f0f0f0',
            textAlign: 'center',
          }}>
            {!collapsed && <Title level={4} style={{ margin: 0, color: '#1677ff' }}>金融学院</Title>}
            {collapsed && <span style={{ fontSize: 24 }}>🎓</span>}
          </div>
          {menuContent}
        </Sider>
      )}

      {/* Mobile drawer */}
      {isMobile && (
        <Drawer
          placement="left"
          open={drawerOpen}
          onClose={() => setDrawerOpen(false)}
          width={260}
          styles={{ body: { padding: 0 } }}
          title="金融学院"
        >
          {menuContent}
        </Drawer>
      )}

      <Layout>
        <Header style={{
          padding: isMobile ? '0 12px' : '0 24px',
          background: darkMode ? '#141414' : '#fff',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          borderBottom: '1px solid #f0f0f0',
          boxShadow: '0 1px 4px rgba(0,0,0,0.04)',
          height: isMobile ? 48 : 64,
          lineHeight: isMobile ? '48px' : '64px',
        }}>
          <Space>
            <Button
              type="text"
              icon={isMobile ? <MenuUnfoldOutlined /> : (collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />)}
              onClick={() => isMobile ? setDrawerOpen(true) : setCollapsed(!collapsed)}
            />
            <Title level={5} style={{ margin: 0, fontSize: isMobile ? 14 : 16 }}>
              {menuItems.find(m => m.key === location.pathname)?.label || '金融学院AI助手'}
            </Title>
          </Space>
          <Space size={4}>
            <BulbOutlined style={{ fontSize: 14 }} />
            <Switch
              size="small"
              checked={darkMode}
              onChange={setDarkMode}
              checkedChildren={<BulbFilled />}
              unCheckedChildren={<BulbOutlined />}
            />
          </Space>
        </Header>

        <Content style={{
          margin: isMobile ? 8 : 24,
          padding: isMobile ? 12 : 24,
          background: darkMode ? '#1a1a1a' : '#f5f5f5',
          minHeight: 280,
          borderRadius: isMobile ? 8 : 12,
        }}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  )
}
