import { useState, useEffect } from 'react'
import { Row, Col, Card, Typography, Spin, Button, Space, Table, Tag, message, Tooltip, Statistic } from 'antd'
import { DownloadOutlined, BarChartOutlined, ArrowUpOutlined, ArrowDownOutlined, InfoCircleOutlined, SyncOutlined } from '@ant-design/icons'
import ReactECharts from 'echarts-for-react'
import { macroOverview, macroChart, macroCrawlerAll } from '../api'

const { Title, Text, Paragraph } = Typography

const INDICATORS = [
  { key: 'shanghai', name: '上证指数', icon: '📈', color: '#ff4d4f' },
  { key: 'cpi', name: 'CPI同比', icon: '📊', color: '#fa8c16' },
  { key: 'pmi', name: 'PMI制造业', icon: '🏭', color: '#1677ff' },
  { key: 'm2', name: 'M2同比增速', icon: '💰', color: '#722ed1' },
]

const CRAWLER_INDICATORS = [
  { key: 'gdp', name: 'GDP', icon: '🏛️', source: '国家统计局', tip: '国内生产总值，衡量经济总量' },
  { key: 'cpi', name: 'CPI', icon: '📈', source: '国家统计局', tip: '居民消费价格指数，反映通胀水平' },
  { key: 'ppi', name: 'PPI', icon: '📊', source: '国家统计局', tip: '工业生产者出厂价格指数' },
  { key: 'pmi', name: 'PMI', icon: '🏭', source: '国家统计局', tip: '采购经理指数，>50为扩张' },
  { key: 'm2', name: 'M2同比', icon: '💰', source: '中国人民银行', tip: '广义货币供应量增速' },
  { key: 'lpr', name: 'LPR利率', icon: '🏦', source: '中国人民银行', tip: '贷款市场报价利率' },
  { key: 'social_financing', name: '社会融资规模', icon: '💹', source: '中国人民银行', tip: '实体经济从金融体系获得的资金' },
  { key: 'trade', name: '进出口数据', icon: '🚢', source: '海关总署', tip: '反映外贸状况' },
]

function getValueColor(key: string, value: string) {
  const num = parseFloat(value)
  if (isNaN(num)) return '#333'
  if (key === 'pmi') return num >= 50 ? '#52c41a' : '#ff4d4f'
  if (key === 'cpi' || key === 'ppi') return num > 3 ? '#ff4d4f' : num < 0 ? '#52c41a' : '#faad14'
  return '#1677ff'
}

function getStatusTag(key: string, value: string) {
  const num = parseFloat(value)
  if (isNaN(num)) return null
  if (key === 'pmi') return num >= 50
    ? <Tag color="success">扩张</Tag>
    : <Tag color="error">收缩</Tag>
  if (key === 'cpi') return num > 3
    ? <Tag color="warning">偏高</Tag>
    : num < 0
    ? <Tag color="error">通缩</Tag>
    : <Tag color="success">温和</Tag>
  return null
}

export default function Macro() {
  const [overview, setOverview] = useState<any>({})
  const [activeChart, setActiveChart] = useState('shanghai')
  const [chartData, setChartData] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [chartLoading, setChartLoading] = useState(false)
  const [crawlerData, setCrawlerData] = useState<any>({})
  const [crawlerLoading, setCrawlerLoading] = useState(false)

  useEffect(() => {
    macroOverview().then(res => setOverview(res.data)).catch(() => message.error('加载宏观数据失败')).finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    setChartLoading(true)
    macroChart(activeChart).then(res => setChartData(res.data)).catch(() => message.error('加载图表数据失败')).finally(() => setChartLoading(false))
  }, [activeChart])

  const handleRefreshCrawler = () => {
    setCrawlerLoading(true)
    macroCrawlerAll().then(res => setCrawlerData(res.data)).catch(() => message.error('加载爬虫数据失败')).finally(() => setCrawlerLoading(false))
  }

  useEffect(() => { handleRefreshCrawler() }, [])

  const chartOption = chartData?.dates?.length
    ? {
        tooltip: { trigger: 'axis', backgroundColor: 'rgba(255,255,255,0.95)', borderColor: '#f0f0f0', textStyle: { fontSize: 13 } },
        grid: { left: '3%', right: '5%', bottom: '3%', top: '10%', containLabel: true },
        xAxis: { type: 'category', data: chartData.dates, axisLabel: { fontSize: 11 }, axisLine: { lineStyle: { color: '#d9d9d9' } } },
        yAxis: { type: 'value', axisLabel: { fontSize: 11 }, splitLine: { lineStyle: { type: 'dashed', color: '#f0f0f0' } } },
        series: [{
          name: chartData.indicator,
          type: 'line',
          data: chartData.values,
          smooth: true,
          symbol: 'circle',
          symbolSize: 4,
          lineStyle: { color: '#1677ff', width: 2.5 },
          itemStyle: { color: '#1677ff' },
          areaStyle: {
            color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
              colorStops: [{ offset: 0, color: 'rgba(22,119,255,0.2)' }, { offset: 1, color: 'rgba(22,119,255,0.01)' }],
            },
          },
          markLine: activeChart === 'pmi'
            ? { data: [{ yAxis: 50, name: '荣枯线', lineStyle: { color: '#ff4d4f', type: 'dashed', width: 1.5 }, label: { formatter: '荣枯线 50', fontSize: 11 } }] }
            : undefined,
        }],
      }
    : null

  const statCards = [
    { label: 'GDP增速', value: overview.gdp_growth, suffix: '%', icon: '🏛️', gradient: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', tip: '国内生产总值同比增长' },
    { label: 'CPI同比', value: overview.cpi, suffix: '%', icon: '📈', gradient: 'linear-gradient(135deg, #11998e 0%, #38ef7d 100%)', tip: '居民消费价格指数' },
    { label: 'PMI', value: overview.pmi, suffix: '', icon: '🏭', gradient: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)', tip: '>50为经济扩张' },
    { label: 'M2增速', value: overview.m2_growth, suffix: '%', icon: '💰', gradient: 'linear-gradient(135deg, #a18cd1 0%, #fbc2eb 100%)', tip: '广义货币供应量同比' },
    { label: 'LPR', value: overview.lpr, suffix: '%', icon: '🏦', gradient: 'linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%)', tip: '1年期贷款市场报价利率' },
  ]

  // 上证指数迷你趋势图
  const shanghaiTrendOption = chartData?.dates?.length && activeChart === 'shanghai'
    ? {
        grid: { left: 0, right: 0, top: 4, bottom: 4 },
        xAxis: { type: 'category', show: false, data: chartData.dates },
        yAxis: { type: 'value', show: false, min: 'dataMin', max: 'dataMax' },
        series: [{
          type: 'line',
          data: chartData.values,
          smooth: true,
          symbol: 'none',
          lineStyle: { color: overview.shanghai_change >= 0 ? '#ff4d4f' : '#52c41a', width: 2 },
          areaStyle: {
            color: {
              type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
              colorStops: [
                { offset: 0, color: overview.shanghai_change >= 0 ? 'rgba(255,77,79,0.3)' : 'rgba(82,196,26,0.3)' },
                { offset: 1, color: overview.shanghai_change >= 0 ? 'rgba(255,77,79,0.02)' : 'rgba(82,196,26,0.02)' },
              ],
            },
          },
        }],
        tooltip: { trigger: 'axis', formatter: '{b}: {c}' },
      }
    : null

  const exportCSV = () => {
    if (!chartData?.dates?.length) { message.warning('暂无数据可导出'); return }
    const csv = ['日期,值'].concat(chartData.dates.map((d: string, i: number) => `${d},${chartData.values[i]}`)).join('\n')
    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a'); a.href = url; a.download = `${chartData.indicator}_data.csv`; a.click(); URL.revokeObjectURL(url)
    message.success('已导出CSV')
  }

  return (
    <div>
      <div className="page-header">
        <Title level={3} style={{ fontSize: window.innerWidth < 768 ? 20 : 24 }}>宏观经济数据</Title>
        <Text type="secondary">实时宏观经济指标与走势图</Text>
      </div>

      {/* 上证指数突出展示 */}
      {loading ? <Spin /> : (
        <Card style={{ marginBottom: 16, background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%)', border: 'none' }}>
          <Row gutter={[16, 16]} align="middle">
            <Col xs={24} sm={8} md={6}>
              <div style={{ color: '#fff' }}>
                <div style={{ fontSize: 13, opacity: 0.7, marginBottom: 4 }}>📈 上证综合指数</div>
                <div style={{ fontSize: window.innerWidth < 768 ? 28 : 36, fontWeight: 700, lineHeight: 1.1 }}>
                  {overview.shanghai_index != null ? overview.shanghai_index.toLocaleString() : '--'}
                </div>
                {overview.shanghai_change != null && (
                  <div style={{ marginTop: 8, fontSize: 15, fontWeight: 600, color: overview.shanghai_change >= 0 ? '#ff4d4f' : '#52c41a' }}>
                    {overview.shanghai_change >= 0 ? '▲' : '▼'} {overview.shanghai_change >= 0 ? '+' : ''}{overview.shanghai_change}%
                    <span style={{ fontSize: 12, fontWeight: 400, marginLeft: 8, opacity: 0.7 }}>
                      {overview.shanghai_change >= 0 ? '今日上涨' : '今日下跌'}
                    </span>
                  </div>
                )}
              </div>
            </Col>
            <Col xs={24} sm={16} md={18}>
              {shanghaiTrendOption ? (
                <ReactECharts option={shanghaiTrendOption} style={{ height: 80 }} />
              ) : (
                <div style={{ height: 80, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'rgba(255,255,255,0.3)' }}>
                  <BarChartOutlined style={{ fontSize: 24 }} /> 加载趋势数据中...
                </div>
              )}
            </Col>
          </Row>
        </Card>
      )}

      {/* 其他核心指标卡片 */}
      {loading ? null : (
        <Row gutter={[12, 12]} style={{ marginBottom: 20 }}>
          {statCards.map((s, i) => (
            <Col xs={12} sm={8} md={4} lg={Math.floor(24 / statCards.length)} key={i}>
              <Tooltip title={s.tip}>
                <div style={{ background: s.gradient, borderRadius: 10, padding: '14px 10px', color: '#fff', textAlign: 'center', cursor: 'default' }}>
                  <div style={{ fontSize: 11, opacity: 0.9 }}>{s.icon} {s.label}</div>
                  <div style={{ fontSize: window.innerWidth < 768 ? 18 : 24, fontWeight: 700, margin: '4px 0' }}>
                    {s.value != null ? `${s.value}${s.suffix}` : '--'}
                  </div>
                </div>
              </Tooltip>
            </Col>
          ))}
        </Row>
      )}

      {/* 图表区域 */}
      <Card style={{ marginBottom: 16 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16, flexWrap: 'wrap', gap: 8 }}>
          <Space wrap>
            {INDICATORS.map(ind => (
              <Button key={ind.key} type={activeChart === ind.key ? 'primary' : 'default'}
                onClick={() => setActiveChart(ind.key)} style={{ borderRadius: 6 }}>
                {ind.icon} {ind.name}
              </Button>
            ))}
          </Space>
          <Button icon={<DownloadOutlined />} onClick={exportCSV} size="small">下载CSV</Button>
        </div>
        {chartLoading ? (
          <div style={{ textAlign: 'center', padding: 60 }}><Spin /></div>
        ) : chartOption ? (
          <ReactECharts option={chartOption} style={{ height: window.innerWidth < 768 ? 250 : 400 }} />
        ) : (
          <div style={{ textAlign: 'center', padding: 60, color: '#ccc' }}><BarChartOutlined style={{ fontSize: 48 }} /><p>暂无数据</p></div>
        )}
      </Card>

      {/* 权威数据源 */}
      <Card
        title={<Space>🏛️ 权威数据源<Tooltip title="数据来自国家统计局、中国人民银行、海关总署等官方机构"><InfoCircleOutlined style={{ color: '#999' }} /></Tooltip></Space>}
        style={{ marginTop: 16 }}
        extra={<Space><Tag color="green">实时</Tag><Button icon={<SyncOutlined />} size="small" loading={crawlerLoading} onClick={handleRefreshCrawler}>刷新</Button></Space>}
      >
        <Row gutter={[12, 12]}>
          {CRAWLER_INDICATORS.map(ind => {
            const data = crawlerData[ind.key] || {}
            const hasError = data.error
            const val = data.value || data.period || '--'
            const valueColor = getValueColor(ind.key, String(val))
            return (
              <Col xs={12} sm={8} md={6} key={ind.key}>
                <Tooltip title={ind.tip}>
                  <div style={{
                    padding: 14, borderRadius: 10, border: hasError ? '1px solid #f0f0f0' : '1px solid #e6f4ff',
                    background: hasError ? '#fafafa' : '#f6ffed', minHeight: 90,
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                      <Text strong style={{ fontSize: 13 }}>{ind.icon} {ind.name}</Text>
                      <Tag style={{ fontSize: 9, padding: '0 4px' }}>{ind.source}</Tag>
                    </div>
                    {hasError ? (
                      <Text type="secondary" style={{ fontSize: 12 }}>暂无数据</Text>
                    ) : (
                      <>
                        <div style={{ fontSize: 20, fontWeight: 700, color: valueColor, lineHeight: 1.2 }}>{val}</div>
                        {data.unit && <Text type="secondary" style={{ fontSize: 11 }}>{data.unit}</Text>}
                        {data.period && <Text type="secondary" style={{ fontSize: 10, display: 'block', marginTop: 2 }}>{data.period}</Text>}
                        {getStatusTag(ind.key, String(val))}
                      </>
                    )}
                  </div>
                </Tooltip>
              </Col>
            )
          })}
        </Row>
      </Card>
    </div>
  )
}
