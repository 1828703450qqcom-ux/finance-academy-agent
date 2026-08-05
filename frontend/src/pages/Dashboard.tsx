import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Row, Col, Typography, Spin, Tag, message } from 'antd'
import ReactECharts from 'echarts-for-react'
import { macroOverview } from '../api'

const { Title, Text } = Typography

const features = [
  { key: '/empirical', icon: '📊', title: '实证研究', desc: 'OLS/固定效应/GMM回归分析', color: '#1677ff' },
  { key: '/quant', icon: '📈', title: '量化回测', desc: '动量/均值回归/多因子策略', color: '#52c41a' },
  { key: '/report', icon: '📄', title: '财报解析', desc: '杜邦分析/财务指标提取', color: '#fa8c16' },
  { key: '/paper', icon: '📚', title: '论文检索', desc: 'OpenAlex/arXiv文献搜索', color: '#722ed1' },
  { key: '/macro', icon: '🌐', title: '宏观数据', desc: 'GDP/CPI/PMI实时数据', color: '#13c2c2' },
  { key: '/chat', icon: '💬', title: '智能问答', desc: '金融问题随时咨询', color: '#eb2f96' },
]

const hotTopics = [
  { text: 'ESG与融资成本', tag: '热点' },
  { text: '动量因子回测', tag: '量化' },
  { text: '茅台财报分析', tag: '财报' },
  { text: '中美利差走势', tag: '宏观' },
  { text: '机器学习资产定价', tag: '前沿' },
]

export default function Dashboard() {
  const navigate = useNavigate()
  const [overview, setOverview] = useState<any>({})
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    macroOverview()
      .then((res) => setOverview(res.data))
      .catch(() => message.error('加载宏观数据失败'))
      .finally(() => setLoading(false))
  }, [])

  const statCards = [
    { label: '上证指数', value: overview.shanghai_index || '--', sub: overview.shanghai_change ? `${overview.shanghai_change > 0 ? '+' : ''}${overview.shanghai_change}%` : '', color: '' },
    { label: 'CPI同比', value: overview.cpi ? `${overview.cpi}%` : '--', color: 'green' },
    { label: 'PMI', value: overview.pmi || '--', color: 'blue' },
    { label: 'M2增速', value: overview.m2_growth ? `${overview.m2_growth}%` : '--', color: 'orange' },
  ]

  return (
    <div>
      <div className="page-header">
        <Title level={3}>🎓 金融学院AI助手</Title>
        <Text type="secondary">一站式金融研究与分析平台</Text>
      </div>

      {/* 功能入口 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        {features.map((f) => (
          <Col xs={12} sm={8} key={f.key}>
            <div className="feature-card" onClick={() => navigate(f.key)}>
              <span className="icon">{f.icon}</span>
              <div className="title">{f.title}</div>
              <div className="desc">{f.desc}</div>
            </div>
          </Col>
        ))}
      </Row>

      {/* 宏观数据速览 */}
      <div className="notion-card" style={{ marginBottom: 24 }}>
        <Title level={5} style={{ marginBottom: 16 }}>📊 宏观数据速览</Title>
        {loading ? (
          <Spin />
        ) : (
          <Row gutter={[16, 16]}>
            {statCards.map((s, i) => (
              <Col xs={12} sm={6} key={i}>
                <div className={`stat-card ${s.color}`}>
                  <div className="label">{s.label}</div>
                  <div className="value">{s.value}</div>
                  {s.sub && <div style={{ fontSize: 12, opacity: 0.8 }}>{s.sub}</div>}
                </div>
              </Col>
            ))}
          </Row>
        )}
      </div>

      {/* 热门研究话题 */}
      <div className="notion-card">
        <Title level={5} style={{ marginBottom: 12 }}>🔥 热门研究话题</Title>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          {hotTopics.map((t, i) => (
            <Tag
              key={i}
              color={['blue', 'green', 'orange', 'cyan', 'purple'][i % 5]}
              style={{ cursor: 'pointer', padding: '4px 12px', fontSize: 14 }}
              onClick={() => navigate('/chat')}
            >
              {t.text}
            </Tag>
          ))}
        </div>
      </div>
    </div>
  )
}
