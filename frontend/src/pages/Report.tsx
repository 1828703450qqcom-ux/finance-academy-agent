import { useState, useCallback } from 'react'
import { Row, Col, Card, Button, Upload, Typography, Checkbox, Space, Divider, Spin, message, List } from 'antd'
import { UploadOutlined, FileTextOutlined, DownloadOutlined, InboxOutlined } from '@ant-design/icons'
import ReactECharts from 'echarts-for-react'
import { uploadReport, analyzeReport, listReports } from '../api'

const { Title, Text, Paragraph } = Typography
const { Dragger } = Upload

const ANALYSIS_DIMENSIONS = [
  { label: '杜邦分析', value: 'dupont' },
  { label: '营收增速', value: 'revenue_growth' },
  { label: '盈利能力', value: 'profitability' },
  { label: '偿债能力', value: 'solvency' },
  { label: '现金流', value: 'cashflow' },
  { label: '营运能力', value: 'operation' },
]

export default function Report() {
  const [reports, setReports] = useState<any[]>([])
  const [selectedReport, setSelectedReport] = useState<any>(null)
  const [dimensions, setDimensions] = useState<string[]>(['dupont', 'revenue_growth', 'profitability', 'solvency'])
  const [analysisResult, setAnalysisResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [uploading, setUploading] = useState(false)

  const handleUpload = async (file: File) => {
    setUploading(true)
    try {
      const res = await uploadReport(file)
      message.success('上传成功')
      setSelectedReport(res.data)
      loadReports()
    } catch {
      message.error('上传失败')
    }
    setUploading(false)
    return false
  }

  const loadReports = async () => {
    try {
      const res = await listReports()
      setReports(res.data.reports || [])
    } catch { message.error('加载记录失败') }
  }

  const handleAnalyze = async () => {
    if (!selectedReport) {
      message.warning('请先上传财报')
      return
    }
    setLoading(true)
    try {
      const res = await analyzeReport(selectedReport.report_id, dimensions)
      setAnalysisResult(res.data)
      message.success('分析完成')
    } catch {
      message.error('分析失败')
    }
    setLoading(false)
  }

  const dupontChartOption = analysisResult?.dupont
    ? {
        tooltip: { trigger: 'item' },
        series: [
          {
            type: 'tree',
            data: [
              {
                name: `ROE ${analysisResult.dupont.roe || '--'}%`,
                children: [
                  { name: `净利率 ${analysisResult.dupont.net_margin || '--'}%` },
                  { name: `周转率 ${analysisResult.dupont.asset_turnover || '--'}` },
                  { name: `权益乘数 ${analysisResult.dupont.equity_multiplier || '--'}` },
                ],
              },
            ],
            orient: 'TB',
            label: { fontSize: 14, color: '#333' },
            lineStyle: { width: 2, color: '#1677ff' },
            expandAndCollapse: false,
          },
        ],
      }
    : null

  return (
    <div>
      <div className="page-header">
        <Title level={3}>📄 财报/研报解析</Title>
        <Text type="secondary">上传PDF财报，自动提取关键财务数据</Text>
      </div>

      <Row gutter={24}>
        {/* 左侧 */}
        <Col xs={24} lg={8}>
          <Card title="📂 上传记录" size="small" style={{ marginBottom: 16 }}>
            <List
              size="small"
              dataSource={reports}
              renderItem={(item: any) => (
                <List.Item
                  style={{ cursor: 'pointer' }}
                  onClick={() => setSelectedReport(item)}
                >
                  <Text style={{ fontSize: 13 }}>{item.filename}</Text>
                </List.Item>
              )}
              locale={{ emptyText: '暂无记录' }}
            />
          </Card>

          <Card title="📋 分析模板" size="small">
            <Space direction="vertical" style={{ width: '100%' }}>
              {['杜邦分析', '横向对比', '纵向趋势', '财务预警'].map((t) => (
                <div key={t} style={{ padding: '8px 0', borderBottom: '1px solid #f0f0f0', fontSize: 13 }}>
                  {t}
                </div>
              ))}
            </Space>
          </Card>
        </Col>

        {/* 右侧 */}
        <Col xs={24} lg={16}>
          {/* 上传区域 */}
          <Card style={{ marginBottom: 16 }}>
            <Dragger
              accept=".pdf"
              showUploadList={false}
              beforeUpload={(file) => {
                handleUpload(file as File)
                return false
              }}
              style={{ padding: '20px 0' }}
            >
              <p className="ant-upload-drag-icon">
                <InboxOutlined />
              </p>
              <p className="ant-upload-text">拖拽财报PDF到此处，或点击上传</p>
              <p className="ant-upload-hint">支持 .pdf 格式</p>
            </Dragger>
            {selectedReport && (
              <div style={{ marginTop: 8 }}>
                <Text type="success">已上传: {selectedReport.filename} ✓</Text>
              </div>
            )}
          </Card>

          {/* 分析维度 */}
          <Card title="📊 分析维度" style={{ marginBottom: 16 }}>
            <Checkbox.Group
              value={dimensions}
              onChange={(v) => setDimensions(v as string[])}
              options={ANALYSIS_DIMENSIONS}
            />
            <Button
              type="primary"
              onClick={handleAnalyze}
              loading={loading}
              style={{ marginTop: 12 }}
            >
              开始分析
            </Button>
          </Card>

          {/* 分析结果 */}
          {analysisResult && (
            <>
              {/* 杜邦分析树 */}
              {dupontChartOption && (
                <Card title="🌳 杜邦分析树状图" style={{ marginBottom: 16 }}>
                  <ReactECharts option={dupontChartOption} style={{ height: 250 }} />
                </Card>
              )}

              {/* 关键数据 */}
              <Card title="📊 关键财务数据" style={{ marginBottom: 16 }}>
                <Row gutter={[16, 16]}>
                  {analysisResult.extracted_data &&
                    Object.entries(analysisResult.extracted_data).map(([key, value]: [string, any]) => (
                      <Col span={8} key={key}>
                        <div style={{ textAlign: 'center' }}>
                          <Text type="secondary" style={{ fontSize: 12 }}>{key}</Text>
                          <br />
                          <Text strong style={{ fontSize: 18 }}>{value}</Text>
                        </div>
                      </Col>
                    ))}
                </Row>
              </Card>

              {/* 摘要 */}
              <Card title="📝 分析摘要" size="small">
                <Paragraph>{analysisResult.summary}</Paragraph>
              </Card>

              {/* 导出按钮 */}
              <Space style={{ marginTop: 16 }}>
                <Button icon={<DownloadOutlined />} onClick={() => {
                  const content = `# 财报分析报告\n\n## 公司: ${analysisResult.company_name || '--'}\n## 年份: ${analysisResult.year || '--'}\n\n## 关键财务数据\n${Object.entries(analysisResult.extracted_data || {}).map(([k, v]) => `- ${k}: ${v}`).join('\n')}\n\n## 分析摘要\n${analysisResult.summary || ''}\n`
                  const blob = new Blob([content], { type: 'text/markdown' })
                  const url = URL.createObjectURL(blob)
                  const a = document.createElement('a'); a.href = url; a.download = `财报分析_${analysisResult.company_name || 'report'}.md`; a.click(); URL.revokeObjectURL(url)
                  message.success('已导出Markdown报告')
                }}>导出报告</Button>
                <Button icon={<DownloadOutlined />} onClick={() => {
                  const data = analysisResult.extracted_data || {}
                  const csv = ['指标,值'].concat(Object.entries(data).map(([k, v]) => `${k},${v}`)).join('\n')
                  const blob = new Blob([csv], { type: 'text/csv' })
                  const url = URL.createObjectURL(blob)
                  const a = document.createElement('a'); a.href = url; a.download = `财务数据_${analysisResult.company_name || 'data'}.csv`; a.click(); URL.revokeObjectURL(url)
                  message.success('已导出CSV')
                }}>导出Excel</Button>
              </Space>
            </>
          )}
        </Col>
      </Row>
    </div>
  )
}
