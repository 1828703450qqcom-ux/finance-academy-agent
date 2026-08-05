import { useState, useEffect, useMemo } from 'react'
import { Card, Input, Button, Select, Space, Typography, Tabs, message, Tag, Row, Col, Alert, Table, Statistic, Descriptions, Tooltip, Empty, Skeleton } from 'antd'
import {
  FileTextOutlined,
  RiseOutlined,
  SafetyOutlined,
  DownloadOutlined,
  BankOutlined,
  StockOutlined,
  FundOutlined,
  SearchOutlined,
  ArrowUpOutlined,
  ArrowDownOutlined,
  CopyOutlined,
  BarChartOutlined,
  PieChartOutlined,
  CheckCircleOutlined,
  ThunderboltOutlined,
  HistoryOutlined,
  DeleteOutlined,
} from '@ant-design/icons'
import ReactMarkdown from 'react-markdown'
import axios from 'axios'

const { Text, Paragraph } = Typography
const { TabPane } = Tabs
const { Option } = Select

interface KeyMetrics {
  '营业总收入(万元)'?: number
  '归母净利润(万元)'?: number
  'ROE(%)'?: number
  'ROA(%)'?: number
  '资产负债率(%)'?: number
  '流动比率'?: number
  '毛利率(%)'?: number
  '净利率(%)'?: number
  '营收同比增长率(%)'?: number
  '归母净利润同比增长率(%)'?: number
  '经营现金流/净利润(%)'?: number
  '毛利率趋势'?: string
  '毛利率变化(百分点)'?: number
  '最新报告期'?: string
}

interface ReportResult {
  success: boolean
  report_id: string
  content: string
  company_name: string
  generated_at: string
  key_metrics?: KeyMetrics
}

interface RecentReport {
  id: string
  code: string
  name: string
  type: string
  date: string
}

const RECENT_KEY = 'finance_recent_reports'

function getRecentReports(): RecentReport[] {
  try { return JSON.parse(localStorage.getItem(RECENT_KEY) || '[]') } catch { return [] }
}

function addRecentReport(code: string, name: string, type: string) {
  const list = getRecentReports().filter(r => r.code !== code).slice(0, 9)
  list.unshift({ id: `${code}_${Date.now()}`, code, name, type, date: new Date().toLocaleDateString() })
  localStorage.setItem(RECENT_KEY, JSON.stringify(list))
}

function getROEColor(val?: number) {
  if (val === undefined || val === null) return '#999'
  if (val > 15) return '#52c41a'
  if (val > 8) return '#faad14'
  return '#ff4d4f'
}

function getDebtLevel(val?: number) {
  if (val === undefined || val === null) return { color: '#999', text: '未知', level: 'default' as const }
  if (val < 40) return { color: '#52c41a', text: '低风险', level: 'success' as const }
  if (val < 60) return { color: '#faad14', text: '中等', level: 'warning' as const }
  return { color: '#ff4d4f', text: '高风险', level: 'error' as const }
}

function getGrowthIcon(val?: number) {
  if (val === undefined || val === null) return null
  return val > 0 ? <ArrowUpOutlined style={{ color: '#52c41a' }} /> : val < 0 ? <ArrowDownOutlined style={{ color: '#ff4d4f' }} /> : null
}

function getGrowthColor(val?: number) {
  if (val === undefined || val === null) return '#999'
  return val >= 0 ? '#52c41a' : '#ff4d4f'
}

export default function FinanceReport() {
  const [activeTab, setActiveTab] = useState('generate')
  const [stockCode, setStockCode] = useState('')
  const [market, setMarket] = useState('A')
  const [reportType, setReportType] = useState('comprehensive')
  const [analysisDepth, setAnalysisDepth] = useState('standard')
  const [loading, setLoading] = useState(false)
  const [reportResult, setReportResult] = useState<ReportResult | null>(null)
  const [financialData, setFinancialData] = useState<any>(null)
  const [companyInfo, setCompanyInfo] = useState<any>(null)

  const [compareCodes, setCompareCodes] = useState('')
  const [compareLoading, setCompareLoading] = useState(false)
  const [compareReport, setCompareReport] = useState<string | null>(null)

  const [riskCode, setRiskCode] = useState('')
  const [riskLoading, setRiskLoading] = useState(false)
  const [riskReport, setRiskReport] = useState<string | null>(null)

  const [recentReports, setRecentReports] = useState<RecentReport[]>([])

  useEffect(() => { setRecentReports(getRecentReports()) }, [])

  const keyMetrics: KeyMetrics | undefined = useMemo(() => {
    return reportResult?.key_metrics || (financialData ? extractMetricsFromData(financialData) : undefined)
  }, [reportResult, financialData])

  function extractMetricsFromData(data: any): KeyMetrics | undefined {
    if (!data) return undefined
    const income = data.income_statement?.[0]
    const balance = data.balance_sheet?.[0]
    if (!income && !balance) return undefined
    return {
      '营业总收入(万元)': income?.['营业总收入(万元)'],
      '归母净利润(万元)': income?.['归母净利润(万元)'],
      '毛利率(%)': income?.['毛利率'],
      '净利率(%)': income?.['净利率'],
      '资产负债率(%)': balance && balance['总负债(万元)'] && balance['总资产(万元)']
        ? (balance['总负债(万元)'] / balance['总资产(万元)'] * 100) : undefined,
    }
  }

  const handleGenerateReport = async () => {
    if (!stockCode.trim()) { message.warning('请输入股票代码'); return }
    setLoading(true)
    try {
      const res = await axios.post('/api/finance-report/generate', {
        stock_code: stockCode.trim(), market, report_type: reportType,
        analysis_depth: analysisDepth, include_charts: true,
      }, { timeout: 180000 })
      if (res.data.success) {
        setReportResult(res.data)
        addRecentReport(stockCode.trim(), res.data.company_name, reportType)
        setRecentReports(getRecentReports())
        message.success('研报生成成功！')
      } else {
        message.error('生成失败：' + (res.data.error || '未知错误'))
      }
    } catch (error: any) {
      message.error(error.response?.data?.detail || error.message || '生成失败，请稍后重试')
    }
    setLoading(false)
  }

  const handleFetchAll = async () => {
    if (!stockCode.trim()) { message.warning('请输入股票代码'); return }
    setLoading(true)
    try {
      const [finRes, infoRes] = await Promise.all([
        axios.get(`/api/finance-report/financial-data/${stockCode.trim()}?market=${market}`),
        axios.get(`/api/finance-report/company-info/${stockCode.trim()}?market=${market}`),
      ])
      if (finRes.data.success) setFinancialData(finRes.data.data)
      if (infoRes.data.success) setCompanyInfo(infoRes.data.data)
      message.success('数据获取成功！')
    } catch { message.error('获取数据失败') }
    setLoading(false)
  }

  const handleCompare = async () => {
    const codes = compareCodes.split(',').map(c => c.trim()).filter(c => c)
    if (codes.length < 2) { message.warning('请输入至少2个股票代码（逗号分隔）'); return }
    setCompareLoading(true)
    try {
      const res = await axios.post('/api/finance-report/compare', { stock_codes: codes, market }, { timeout: 180000 })
      if (res.data.success) { setCompareReport(res.data.report); message.success('对比分析完成！') }
    } catch { message.error('对比分析失败') }
    setCompareLoading(false)
  }

  const handleRiskAnalysis = async () => {
    if (!riskCode.trim()) { message.warning('请输入股票代码'); return }
    setRiskLoading(true)
    try {
      const res = await axios.post('/api/finance-report/generate', {
        stock_code: riskCode.trim(), market, report_type: 'risk',
        analysis_depth: 'detailed', include_charts: true,
      }, { timeout: 180000 })
      if (res.data.success) { setRiskReport(res.data.content); message.success('风险分析完成！') }
      else { message.error('分析失败') }
    } catch { message.error('风险分析失败') }
    setRiskLoading(false)
  }

  const handleDownloadReport = () => {
    if (!reportResult) return
    const blob = new Blob([reportResult.content], { type: 'text/markdown' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `金融研报_${reportResult.company_name}_${new Date().toISOString().slice(0, 10)}.md`
    document.body.appendChild(a); a.click(); document.body.removeChild(a); URL.revokeObjectURL(url)
  }

  const handleCopyReport = () => {
    if (!reportResult) return
    navigator.clipboard.writeText(reportResult.content).then(() => message.success('已复制到剪贴板'))
  }

  const renderTable = (data: any[]) => {
    if (!data || data.length === 0) return <Empty description="暂无数据" image={Empty.PRESENTED_IMAGE_SIMPLE} />
    const keys = Object.keys(data[0])
    const columns = keys.map(k => ({
      title: k, dataIndex: k, key: k,
      render: (val: any) => typeof val === 'number' ? val.toLocaleString() : String(val ?? '-'),
    }))
    return <Table dataSource={data.map((d, i) => ({ ...d, key: i }))} columns={columns} pagination={false} scroll={{ x: 'max-content' }} size="small" />
  }

  const renderKeyMetrics = () => {
    if (!keyMetrics) return null
    const debt = getDebtLevel(keyMetrics['资产负债率(%)'])
    return (
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={12} sm={6}>
          <Card size="small" hoverable>
            <Statistic title="营业总收入" value={keyMetrics['营业总收入(万元)']} suffix="万" precision={0}
              valueStyle={{ fontSize: 20 }} prefix={<FundOutlined style={{ color: '#1677ff' }} />} />
            {keyMetrics['营收同比增长率(%)'] !== undefined && (
              <div style={{ marginTop: 4 }}>
                {getGrowthIcon(keyMetrics['营收同比增长率(%)'])}
                <Text style={{ color: getGrowthColor(keyMetrics['营收同比增长率(%)']), marginLeft: 4, fontSize: 12 }}>
                  同比 {keyMetrics['营收同比增长率(%)']! > 0 ? '+' : ''}{keyMetrics['营收同比增长率(%)']}%
                </Text>
              </div>
            )}
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card size="small" hoverable>
            <Statistic title="归母净利润" value={keyMetrics['归母净利润(万元)']} suffix="万" precision={0}
              valueStyle={{ fontSize: 20 }} prefix={<RiseOutlined style={{ color: '#52c41a' }} />} />
            {keyMetrics['归母净利润同比增长率(%)'] !== undefined && (
              <div style={{ marginTop: 4 }}>
                {getGrowthIcon(keyMetrics['归母净利润同比增长率(%)'])}
                <Text style={{ color: getGrowthColor(keyMetrics['归母净利润同比增长率(%)']), marginLeft: 4, fontSize: 12 }}>
                  同比 {keyMetrics['归母净利润同比增长率(%)']! > 0 ? '+' : ''}{keyMetrics['归母净利润同比增长率(%)']}%
                </Text>
              </div>
            )}
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card size="small" hoverable>
            <Statistic title="ROE (净资产收益率)" value={keyMetrics['ROE(%)']} suffix="%" precision={2}
              valueStyle={{ fontSize: 20, color: getROEColor(keyMetrics['ROE(%)']) }}
              prefix={<ThunderboltOutlined style={{ color: getROEColor(keyMetrics['ROE(%)']) }} />} />
            <div style={{ marginTop: 4 }}>
              <Tag color={keyMetrics['ROE(%)'] !== undefined ? (keyMetrics['ROE(%)']! > 15 ? 'success' : keyMetrics['ROE(%)']! > 8 ? 'warning' : 'error') : 'default'} style={{ fontSize: 11 }}>
                {keyMetrics['ROE(%)'] !== undefined ? (keyMetrics['ROE(%)']! > 15 ? '优秀' : keyMetrics['ROE(%)']! > 8 ? '良好' : '偏低') : '未知'}
              </Tag>
            </div>
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card size="small" hoverable>
            <Statistic title="资产负债率" value={keyMetrics['资产负债率(%)']} suffix="%" precision={2}
              valueStyle={{ fontSize: 20, color: debt.color }} prefix={<SafetyOutlined style={{ color: debt.color }} />} />
            <div style={{ marginTop: 4 }}>
              <Tag color={debt.level} style={{ fontSize: 11 }}>{debt.text}</Tag>
            </div>
          </Card>
        </Col>
      </Row>
    )
  }

  const renderReportHighlights = () => {
    if (!reportResult?.content) return null
    const content = reportResult.content
    const ratingMatch = content.match(/投资评级[：:]\s*(买入|增持|中性|减持|卖出)/)
    const coreMatch = content.match(/核心逻辑[：:]\s*(.+?)[\n\r]/)
    if (!ratingMatch && !coreMatch) return null
    const ratingColor: Record<string, string> = { '买入': '#ff4d4f', '增持': '#fa8c16', '中性': '#faad14', '减持': '#52c41a', '卖出': '#52c41a' }
    return (
      <Alert type="info" showIcon icon={<CheckCircleOutlined />} style={{ marginBottom: 16 }}
        message={
          <Space direction="vertical" size={4}>
            {ratingMatch && <Space><Text strong>投资评级：</Text><Tag color={ratingColor[ratingMatch[1]] || '#1677ff'} style={{ fontSize: 14 }}>{ratingMatch[1]}</Tag></Space>}
            {coreMatch && <Text type="secondary">{coreMatch[1]}</Text>}
          </Space>
        }
      />
    )
  }

  const renderRecentReports = () => {
    if (recentReports.length === 0) return null
    return (
      <Card size="small" title={<Space><HistoryOutlined /> 最近生成的研报</Space>} style={{ marginBottom: 16 }}
        extra={<Button type="link" size="small" icon={<DeleteOutlined />} onClick={() => { localStorage.removeItem(RECENT_KEY); setRecentReports([]) }}>清空</Button>}>
        <Space wrap>
          {recentReports.map(r => (
            <Tag key={r.id} style={{ cursor: 'pointer' }} onClick={() => { setStockCode(r.code); setReportType(r.type) }}>
              {r.name || r.code} ({r.date})
            </Tag>
          ))}
        </Space>
      </Card>
    )
  }

  return (
    <div style={{ maxWidth: 1200, margin: '0 auto' }}>
      <Card
        title={<Space><FundOutlined style={{ color: '#1677ff', fontSize: 20 }} /><span style={{ fontSize: 18, fontWeight: 600 }}>AI金融研报生成系统</span></Space>}
        extra={<Tag color="blue">基于AI大模型</Tag>}
      >
        <Alert message="智能金融研报生成" description="输入股票代码，AI将自动获取财务数据并生成专业的金融研究报告。支持综合分析、估值分析、风险分析。"
          type="info" showIcon style={{ marginBottom: 24 }} />

        {renderRecentReports()}

        <Tabs activeKey={activeTab} onChange={setActiveTab}>
          <TabPane tab={<span><FileTextOutlined /> 研报生成</span>} key="generate">
            <Card size="small" title="输入参数" style={{ marginBottom: 16 }}>
              <Row gutter={[16, 16]}>
                <Col xs={24} sm={8}>
                  <Text strong>股票代码 *</Text>
                  <Input placeholder="例如：600519" value={stockCode} onChange={e => setStockCode(e.target.value)} prefix={<StockOutlined />} allowClear style={{ marginTop: 4 }} />
                </Col>
                <Col xs={24} sm={4}>
                  <Text strong>市场</Text>
                  <Select value={market} onChange={setMarket} style={{ width: '100%', marginTop: 4 }}>
                    <Option value="A">A股</Option><Option value="HK">港股</Option>
                  </Select>
                </Col>
                <Col xs={24} sm={4}>
                  <Text strong>报告类型</Text>
                  <Select value={reportType} onChange={setReportType} style={{ width: '100%', marginTop: 4 }}>
                    <Option value="comprehensive">综合分析</Option>
                    <Option value="valuation">估值分析</Option>
                    <Option value="risk">风险分析</Option>
                  </Select>
                </Col>
                <Col xs={24} sm={4}>
                  <Text strong>分析深度</Text>
                  <Select value={analysisDepth} onChange={setAnalysisDepth} style={{ width: '100%', marginTop: 4 }}>
                    <Option value="standard">标准分析</Option>
                    <Option value="detailed">深度分析</Option>
                  </Select>
                </Col>
                <Col xs={24} sm={4}>
                  <Text strong>&nbsp;</Text>
                  <div style={{ marginTop: 4 }}>
                    <Space>
                      <Button type="primary" icon={<FileTextOutlined />} onClick={handleGenerateReport} loading={loading}>生成研报</Button>
                      <Button icon={<SearchOutlined />} onClick={handleFetchAll} loading={loading}>获取数据</Button>
                    </Space>
                  </div>
                </Col>
              </Row>
            </Card>

            {loading && <Card><Skeleton active paragraph={{ rows: 8 }} /></Card>}
            {!loading && keyMetrics && renderKeyMetrics()}

            {companyInfo && (
              <Card size="small" title="公司信息" style={{ marginBottom: 16 }}>
                <Row gutter={16}>
                  <Col span={6}>
                    <div style={{ textAlign: 'center' }}>
                      <BankOutlined style={{ fontSize: 36, color: '#1677ff' }} />
                      <div style={{ fontSize: 18, fontWeight: 600, marginTop: 8 }}>{companyInfo.name || stockCode}</div>
                      <div style={{ color: '#666', marginTop: 4 }}>{companyInfo.code} | {companyInfo.market === 'A' ? 'A股' : '港股'}</div>
                    </div>
                  </Col>
                  <Col span={18}>
                    <Descriptions column={2} size="small">
                      <Descriptions.Item label="所属行业"><Tag color="blue">{companyInfo.industry || '未知'}</Tag></Descriptions.Item>
                      <Descriptions.Item label="股票代码">{companyInfo.code}</Descriptions.Item>
                    </Descriptions>
                    {companyInfo.description && <Paragraph type="secondary" style={{ marginTop: 8 }}>{companyInfo.description}</Paragraph>}
                  </Col>
                </Row>
              </Card>
            )}

            {!loading && keyMetrics && (
              <Card size="small" title="财务健康度速览" style={{ marginBottom: 16 }}>
                <Row gutter={[16, 12]}>
                  <Col span={6}>
                    <Tooltip title="毛利率变化趋势反映盈利能力稳定性">
                      <div>
                        <Text type="secondary" style={{ fontSize: 12 }}>毛利率趋势</Text>
                        <div>
                          <Tag color={keyMetrics['毛利率趋势'] === '上升' ? 'success' : keyMetrics['毛利率趋势'] === '下降' ? 'error' : 'default'}>
                            {keyMetrics['毛利率趋势'] || '未知'}
                            {keyMetrics['毛利率变化(百分点)'] !== undefined && ` (${keyMetrics['毛利率变化(百分点)']! > 0 ? '+' : ''}${keyMetrics['毛利率变化(百分点)']}pp)`}
                          </Tag>
                        </div>
                      </div>
                    </Tooltip>
                  </Col>
                  <Col span={6}>
                    <Tooltip title="经营现金流/净利润，>80%说明盈利质量高">
                      <div>
                        <Text type="secondary" style={{ fontSize: 12 }}>现金流质量</Text>
                        <div>
                          <Tag color={keyMetrics['经营现金流/净利润(%)'] !== undefined ? (keyMetrics['经营现金流/净利润(%)']! > 80 ? 'success' : keyMetrics['经营现金流/净利润(%)']! > 50 ? 'warning' : 'error') : 'default'}>
                            {keyMetrics['经营现金流/净利润(%)'] !== undefined ? `${keyMetrics['经营现金流/净利润(%)']}%` : '未知'}
                          </Tag>
                        </div>
                      </div>
                    </Tooltip>
                  </Col>
                  <Col span={6}>
                    <Tooltip title="流动比率 > 1 表示短期偿债能力良好">
                      <div>
                        <Text type="secondary" style={{ fontSize: 12 }}>流动比率</Text>
                        <div>
                          <Tag color={keyMetrics['流动比率'] !== undefined ? (keyMetrics['流动比率']! > 1.5 ? 'success' : keyMetrics['流动比率']! > 1 ? 'warning' : 'error') : 'default'}>
                            {keyMetrics['流动比率'] !== undefined ? String(keyMetrics['流动比率']) : '未知'}
                          </Tag>
                        </div>
                      </div>
                    </Tooltip>
                  </Col>
                  <Col span={6}>
                    <Tooltip title="ROA > 5%说明资产利用效率高">
                      <div>
                        <Text type="secondary" style={{ fontSize: 12 }}>ROA</Text>
                        <div>
                          <Tag color={keyMetrics['ROA(%)'] !== undefined ? (keyMetrics['ROA(%)']! > 5 ? 'success' : keyMetrics['ROA(%)']! > 2 ? 'warning' : 'error') : 'default'}>
                            {keyMetrics['ROA(%)'] !== undefined ? `${keyMetrics['ROA(%)']}%` : '未知'}
                          </Tag>
                        </div>
                      </div>
                    </Tooltip>
                  </Col>
                </Row>
              </Card>
            )}

            {financialData && (
              <Card size="small" title="财务数据" style={{ marginBottom: 16 }}>
                <Tabs defaultActiveKey="income">
                  <TabPane tab={<span><RiseOutlined /> 利润表</span>} key="income">{renderTable(financialData.income_statement)}</TabPane>
                  <TabPane tab={<span><BarChartOutlined /> 资产负债表</span>} key="balance">{renderTable(financialData.balance_sheet)}</TabPane>
                  <TabPane tab={<span><PieChartOutlined /> 现金流量表</span>} key="cashflow">{renderTable(financialData.cash_flow)}</TabPane>
                </Tabs>
              </Card>
            )}

            {reportResult && (
              <Card size="small"
                title={<Space><FileTextOutlined /> AI生成的研报 <Tag color="green">{reportResult.company_name}</Tag></Space>}
                extra={<Space>
                  <Button icon={<CopyOutlined />} onClick={handleCopyReport}>复制</Button>
                  <Button icon={<DownloadOutlined />} onClick={handleDownloadReport}>下载</Button>
                </Space>}>
                {renderReportHighlights()}
                <div style={{ background: '#fafafa', padding: 24, borderRadius: 8, maxHeight: 600, overflow: 'auto' }}>
                  <ReactMarkdown>{reportResult.content}</ReactMarkdown>
                </div>
                <div style={{ marginTop: 16, color: '#999', fontSize: 12 }}>生成时间：{new Date(reportResult.generated_at).toLocaleString()}</div>
              </Card>
            )}
          </TabPane>

          <TabPane tab={<span><BarChartOutlined /> 同业对比</span>} key="compare">
            <Card size="small" title="公司对比分析">
              <Text type="secondary">输入多个股票代码（逗号分隔），AI将自动进行横向对比分析，包含评分和投资建议</Text>
              <Row gutter={16} style={{ marginTop: 16 }}>
                <Col span={16}><Input placeholder="例如：600519,000858,000568" value={compareCodes} onChange={e => setCompareCodes(e.target.value)} prefix={<StockOutlined />} size="large" /></Col>
                <Col span={8}><Button type="primary" icon={<BarChartOutlined />} onClick={handleCompare} loading={compareLoading} size="large" block>开始对比分析</Button></Col>
              </Row>
              {compareLoading && <div style={{ marginTop: 24 }}><Skeleton active paragraph={{ rows: 6 }} /></div>}
              {compareReport && (
                <div style={{ marginTop: 24 }}>
                  <div style={{ background: '#fafafa', padding: 24, borderRadius: 8, maxHeight: 600, overflow: 'auto' }}>
                    <ReactMarkdown>{compareReport}</ReactMarkdown>
                  </div>
                </div>
              )}
            </Card>
          </TabPane>

          <TabPane tab={<span><SafetyOutlined /> 风险分析</span>} key="risk">
            <Card size="small" title="风险分析工具">
              <Alert message="AI风险分析" description="输入股票代码，AI将从财务风险、经营风险、行业风险和市场风险四个维度进行深度分析，输出风险评级和应对建议。"
                type="warning" showIcon style={{ marginBottom: 16 }} />
              <Row gutter={16}>
                <Col span={12}><Input placeholder="输入股票代码，如 600519" value={riskCode} onChange={e => setRiskCode(e.target.value)} prefix={<StockOutlined />} size="large" /></Col>
                <Col span={12}><Button type="primary" danger icon={<SafetyOutlined />} size="large" block loading={riskLoading} onClick={handleRiskAnalysis}>生成风险报告</Button></Col>
              </Row>
              {riskLoading && <div style={{ marginTop: 24 }}><Skeleton active paragraph={{ rows: 6 }} /></div>}
              {riskReport && (
                <div style={{ marginTop: 24 }}>
                  <div style={{ background: '#fff7e6', padding: 24, borderRadius: 8, maxHeight: 600, overflow: 'auto', border: '1px solid #ffd591' }}>
                    <ReactMarkdown>{riskReport}</ReactMarkdown>
                  </div>
                </div>
              )}
            </Card>
          </TabPane>
        </Tabs>
      </Card>
    </div>
  )
}
