import { useState } from 'react'
import { Row, Col, Card, Button, Select, Input, Typography, Table, Tag, Space, Divider, message, Alert, Tabs, Collapse, Spin } from 'antd'
import { ExperimentOutlined, BookOutlined, BulbOutlined, CopyOutlined } from '@ant-design/icons'
import { getResearchDesign, getEmpiricalGuide, getPaperSection } from '../api'

const { Text } = Typography

const copyToClipboard = (text: string) => {
  navigator.clipboard.writeText(text).then(() => message.success('已复制到剪贴板'))
}

const CodeBlock = ({ code, label }: { code: string; label?: string }) => (
  <div style={{ position: 'relative', marginTop: 8 }}>
    {label && <Text type="secondary" style={{ fontSize: 12 }}>{label}</Text>}
    <pre style={{ background: '#1e1e1e', color: '#d4d4d4', padding: 12, borderRadius: 6, fontSize: 12, overflow: 'auto', maxHeight: 250, margin: 0 }}>{code}</pre>
    <Button size="small" icon={<CopyOutlined />} style={{ position: 'absolute', top: 4, right: 4 }} onClick={() => copyToClipboard(code)} />
  </div>
)

export default function ResearchGuide() {
  // 研究设计
  const [rdQuestion, setRdQuestion] = useState('')
  const [rdDataType, setRdDataType] = useState('panel')
  const [rdUnit, setRdUnit] = useState('enterprise')
  const [rdTimeSpan, setRdTimeSpan] = useState('')
  const [rdResult, setRdResult] = useState<any>(null)
  const [rdLoading, setRdLoading] = useState(false)

  // 实证操作
  const [guideTask, setGuideTask] = useState('回归代码')
  const [guideOutcome, setGuideOutcome] = useState('')
  const [guideTreatment, setGuideTreatment] = useState('')
  const [guideControls, setGuideControls] = useState('')
  const [guideDesign, setGuideDesign] = useState('DID')
  const [guideResult, setGuideResult] = useState<any>(null)
  const [guideLoading, setGuideLoading] = useState(false)

  // 论文写作
  const [paperSection, setPaperSection] = useState('引言')
  const [paperInfo, setPaperInfo] = useState('')
  const [paperFindings, setPaperFindings] = useState('')
  const [paperContributions, setPaperContributions] = useState('')
  const [paperResult, setPaperResult] = useState<any>(null)
  const [paperLoading, setPaperLoading] = useState(false)

  const handleResearchDesign = async () => {
    if (!rdQuestion.trim()) { message.warning('请输入研究问题'); return }
    setRdLoading(true)
    try {
      const res = await getResearchDesign({ research_question: rdQuestion, data_type: rdDataType, unit: rdUnit, time_span: rdTimeSpan })
      setRdResult(res.data)
    } catch { message.error('获取研究设计建议失败') }
    setRdLoading(false)
  }

  const handleEmpiricalGuide = async () => {
    setGuideLoading(true)
    try {
      const res = await getEmpiricalGuide({ task: guideTask, outcome: guideOutcome, treatment: guideTreatment, controls: guideControls, design: guideDesign })
      setGuideResult(res.data)
    } catch { message.error('获取实证指南失败') }
    setGuideLoading(false)
  }

  const handlePaperSection = async () => {
    if (!paperInfo.trim()) { message.warning('请输入研究信息'); return }
    setPaperLoading(true)
    try {
      const res = await getPaperSection({ section: paperSection, research_info: paperInfo, findings: paperFindings, contributions: paperContributions })
      setPaperResult(res.data)
    } catch { message.error('获取写作模板失败') }
    setPaperLoading(false)
  }

  return (
    <div>
      <Tabs defaultActiveKey="design" items={[
        {
          key: 'design', label: '🔬 研究设计',
          children: (
            <Card size="small">
              <Text type="secondary" style={{ display: 'block', marginBottom: 12 }}>
                输入研究问题，自动推荐因果识别策略（DID/IV/RDD/合成控制等），包含完整回归方程、检验设计和Stata/Python代码
              </Text>
              <Row gutter={12} style={{ marginBottom: 12 }}>
                <Col span={24}>
                  <Input.TextArea value={rdQuestion} onChange={e => setRdQuestion(e.target.value)}
                    placeholder="例如：数字普惠金融发展对县域经济增长的影响研究"
                    autoSize={{ minRows: 2, maxRows: 4 }} />
                </Col>
              </Row>
              <Row gutter={12} style={{ marginBottom: 12 }}>
                <Col span={8}>
                  <Text type="secondary" style={{ fontSize: 12 }}>数据类型</Text>
                  <Select value={rdDataType} onChange={setRdDataType} size="small" style={{ width: '100%' }}
                    options={[{ value: 'panel', label: '面板数据' }, { value: 'cross_section', label: '截面数据' }, { value: 'time_series', label: '时间序列' }]} />
                </Col>
                <Col span={8}>
                  <Text type="secondary" style={{ fontSize: 12 }}>个体单位</Text>
                  <Select value={rdUnit} onChange={setRdUnit} size="small" style={{ width: '100%' }}
                    options={[{ value: 'enterprise', label: '企业' }, { value: 'individual', label: '个人' }, { value: 'county', label: '县级' }, { value: 'province', label: '省级' }]} />
                </Col>
                <Col span={8}>
                  <Text type="secondary" style={{ fontSize: 12 }}>时间跨度</Text>
                  <Input value={rdTimeSpan} onChange={e => setRdTimeSpan(e.target.value)} size="small" placeholder="如 2010-2023" />
                </Col>
              </Row>
              <Button type="primary" icon={<ExperimentOutlined />} loading={rdLoading} onClick={handleResearchDesign}>生成识别方案</Button>

              {rdResult && (
                <div style={{ marginTop: 16 }}>
                  {rdResult.recommendations?.map((rec: any, idx: number) => (
                    <Card key={idx} size="small" style={{ marginBottom: 12, border: idx === 0 ? '2px solid #1677ff' : '1px solid #f0f0f0' }}
                      title={<Space>{idx === 0 && <Tag color="blue">推荐</Tag>}<Text strong>{rec.name}</Text></Space>}>
                      <Text type="secondary"><BulbOutlined /> 适用场景：</Text><br />
                      <Text>{rec.when}</Text>
                      <Divider style={{ margin: '8px 0' }} />
                      <Text type="secondary">回归方程：</Text>
                      <pre style={{ background: '#f5f5f5', padding: 8, borderRadius: 6, fontSize: 12, whiteSpace: 'pre-wrap' }}>{rec.model}</pre>
                      {rec.fixed_effects && <><Text type="secondary">固定效应：</Text><Text>{rec.fixed_effects}</Text><br /></>}
                      <Text type="secondary">关键检验：</Text>
                      <ul style={{ margin: '4px 0', paddingLeft: 20 }}>
                        {rec.tests?.map((t: string, i: number) => <li key={i} style={{ fontSize: 12 }}>{t}</li>)}
                      </ul>
                      <Divider style={{ margin: '8px 0' }} />
                      <CodeBlock code={rec.stata_code} label="Stata代码：" />
                      <CodeBlock code={rec.python_code} label="Python代码：" />
                      {rec.references?.length > 0 && (
                        <><Divider style={{ margin: '8px 0' }} /><Text type="secondary">参考文献：</Text><br />
                        {rec.references.map((ref: string, i: number) => <Text key={i} style={{ fontSize: 12, display: 'block' }}>· {ref}</Text>)}</>
                      )}
                    </Card>
                  ))}
                </div>
              )}
            </Card>
          ),
        },
        {
          key: 'empirical', label: '📈 实证操作',
          children: (
            <Card size="small">
              <Row gutter={12} style={{ marginBottom: 12 }}>
                <Col span={8}>
                  <Text type="secondary" style={{ fontSize: 12 }}>任务类型</Text>
                  <Select value={guideTask} onChange={setGuideTask} size="small" style={{ width: '100%' }}
                    options={[
                      { value: '回归代码', label: '回归代码' },
                      { value: '描述统计', label: '描述统计' },
                      { value: '变量构造', label: '变量构造' },
                      { value: '数据推荐', label: '数据推荐' },
                    ]} />
                </Col>
                {guideTask === '回归代码' && (
                  <>
                    <Col span={5}>
                      <Text type="secondary" style={{ fontSize: 12 }}>被解释变量</Text>
                      <Input size="small" value={guideOutcome} onChange={e => setGuideOutcome(e.target.value)} placeholder="如 Y" />
                    </Col>
                    <Col span={5}>
                      <Text type="secondary" style={{ fontSize: 12 }}>处理变量</Text>
                      <Input size="small" value={guideTreatment} onChange={e => setGuideTreatment(e.target.value)} placeholder="如 treat_post" />
                    </Col>
                    <Col span={5}>
                      <Text type="secondary" style={{ fontSize: 12 }}>控制变量</Text>
                      <Input size="small" value={guideControls} onChange={e => setGuideControls(e.target.value)} placeholder="如 x1, x2, x3" />
                    </Col>
                    <Col span={1}>
                      <Text type="secondary" style={{ fontSize: 12 }}>策略</Text>
                      <Select value={guideDesign} onChange={setGuideDesign} size="small" style={{ width: '100%' }}
                        options={[{ value: 'DID', label: 'DID' }, { value: 'IV', label: 'IV' }, { value: 'RDD', label: 'RDD' }, { value: 'OLS', label: 'OLS' }]} />
                    </Col>
                  </>
                )}
                {guideTask === '变量构造' && (
                  <Col span={16}>
                    <Text type="secondary" style={{ fontSize: 12 }}>变量列表（逗号分隔）</Text>
                    <Input size="small" value={guideOutcome} onChange={e => setGuideOutcome(e.target.value)} placeholder="如 企业规模, ROE, 资产负债率, 托宾Q" />
                  </Col>
                )}
              </Row>
              <Button type="primary" icon={<BookOutlined />} loading={guideLoading} onClick={handleEmpiricalGuide}>生成指南</Button>

              {guideResult && (
                <div style={{ marginTop: 16 }}>
                  {guideResult.templates && Object.entries(guideResult.templates).map(([key, tmpl]: [string, any]) => (
                    <Card key={key} size="small" style={{ marginBottom: 12 }} title={<Text strong style={{ fontSize: 13 }}>{key}</Text>}>
                      {tmpl.stata && <CodeBlock code={tmpl.stata} label="Stata：" />}
                      {tmpl.python && <CodeBlock code={tmpl.python} label="Python：" />}
                    </Card>
                  ))}
                  {guideResult.variables && Object.entries(guideResult.variables).map(([varName, info]: [string, any]) => (
                    <Card key={varName} size="small" style={{ marginBottom: 8 }} title={<Text strong style={{ fontSize: 13 }}>{varName}</Text>}>
                      <Row gutter={8}>
                        <Col span={6}><Text type="secondary" style={{ fontSize: 11 }}>概念</Text><br /><Text style={{ fontSize: 12 }}>{info.concept}</Text></Col>
                        <Col span={6}><Text type="secondary" style={{ fontSize: 11 }}>度量口径</Text><br /><Text style={{ fontSize: 12 }}>{info.measure}</Text></Col>
                        <Col span={6}><Text type="secondary" style={{ fontSize: 11 }}>计算公式</Text><br /><Text style={{ fontSize: 12, fontFamily: 'monospace' }}>{info.formula}</Text></Col>
                        <Col span={6}><Text type="secondary" style={{ fontSize: 11 }}>数据源</Text><br /><Text style={{ fontSize: 12 }}>{info.source}</Text></Col>
                      </Row>
                      {info.pitfalls && (
                        <><Text type="secondary" style={{ fontSize: 11, marginTop: 4, display: 'block' }}>⚠️ 常见坑：</Text>
                        {info.pitfalls.map((p: string, i: number) => <Text key={i} style={{ fontSize: 11, display: 'block' }}>· {p}</Text>)}</>
                      )}
                      {info.stata && (
                        <Space style={{ marginTop: 4 }}>
                          <Button size="small" icon={<CopyOutlined />} onClick={() => copyToClipboard(info.stata)}>复制Stata代码</Button>
                          {info.python && <Button size="small" icon={<CopyOutlined />} onClick={() => copyToClipboard(info.python)}>复制Python代码</Button>}
                        </Space>
                      )}
                    </Card>
                  ))}
                </div>
              )}
            </Card>
          ),
        },
        {
          key: 'writing', label: '✍️ 论文写作',
          children: (
            <Card size="small">
              <Text type="secondary" style={{ display: 'block', marginBottom: 12 }}>
                选择论文章节类型，填写研究信息，生成符合学术规范的段落模板和写作指引
              </Text>
              <Row gutter={12} style={{ marginBottom: 12 }}>
                <Col span={6}>
                  <Text type="secondary" style={{ fontSize: 12 }}>章节类型</Text>
                  <Select value={paperSection} onChange={setPaperSection} size="small" style={{ width: '100%' }}
                    options={[
                      { value: '引言', label: '引言' },
                      { value: '摘要', label: '摘要' },
                      { value: '文献综述', label: '文献综述' },
                      { value: '结论', label: '结论' },
                    ]} />
                </Col>
                <Col span={18}>
                  <Text type="secondary" style={{ fontSize: 12 }}>研究信息（课题背景/研究发现/贡献）</Text>
                  <Input.TextArea value={paperInfo} onChange={e => setPaperInfo(e.target.value)}
                    placeholder="例如：研究数字普惠金融对县域经济增长的影响，发现数字金融显著促进增长，机制是缓解信贷约束"
                    autoSize={{ minRows: 2, maxRows: 4 }} />
                </Col>
              </Row>
              <Row gutter={12} style={{ marginBottom: 12 }}>
                <Col span={12}>
                  <Text type="secondary" style={{ fontSize: 12 }}>主要发现（可选）</Text>
                  <Input.TextArea value={paperFindings} onChange={e => setPaperFindings(e.target.value)}
                    placeholder="1. 数字金融显著促进县域GDP增长；2. 在信贷约束更严重的地区效应更大"
                    autoSize={{ minRows: 2 }} />
                </Col>
                <Col span={12}>
                  <Text type="secondary" style={{ fontSize: 12 }}>边际贡献（可选）</Text>
                  <Input.TextArea value={paperContributions} onChange={e => setPaperContributions(e.target.value)}
                    placeholder="1. 丰富了数字金融与经济增长的文献；2. 揭示了信贷约束的机制"
                    autoSize={{ minRows: 2 }} />
                </Col>
              </Row>
              <Button type="primary" icon={<BookOutlined />} loading={paperLoading} onClick={handlePaperSection}>生成模板</Button>

              {paperResult && (
                <div style={{ marginTop: 16 }}>
                  <Card size="small" style={{ marginBottom: 12 }}>
                    <Text type="secondary">结构：</Text><Text>{paperResult.structure}</Text>
                  </Card>
                  <Card size="small" title="📝 段落模板" style={{ marginBottom: 12 }}>
                    <pre style={{ background: '#f5f5f5', padding: 12, borderRadius: 6, fontSize: 12, whiteSpace: 'pre-wrap', lineHeight: 1.8 }}>{paperResult.template}</pre>
                    <Button size="small" icon={<CopyOutlined />} onClick={() => copyToClipboard(paperResult.template || '')} style={{ marginTop: 8 }}>复制模板</Button>
                  </Card>
                  {paperResult.tips && (
                    <Card size="small" title="💡 写作要点">
                      {paperResult.tips.map((tip: string, i: number) => (
                        <div key={i} style={{ padding: '4px 0', fontSize: 12, borderBottom: '1px solid #f0f0f0' }}>✅ {tip}</div>
                      ))}
                    </Card>
                  )}
                </div>
              )}
            </Card>
          ),
        },
      ]} />
    </div>
  )
}
