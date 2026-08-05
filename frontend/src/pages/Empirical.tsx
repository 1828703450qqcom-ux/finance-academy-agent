import { useState } from 'react'
import { Row, Col, Card, Button, Select, Input, Typography, Table, Tag, Space, Divider, message, Alert, Steps, Collapse, Tooltip, Upload, Descriptions, Statistic, Spin, Tabs, Checkbox } from 'antd'
import { PlayCircleOutlined, ExportOutlined, PlusOutlined, SearchOutlined, ThunderboltOutlined, UploadOutlined, BarChartOutlined, ExperimentOutlined, BookOutlined, BulbOutlined, CopyOutlined, CheckCircleOutlined, DatabaseOutlined, CodeOutlined, FileTextOutlined, TeamOutlined, ReloadOutlined } from '@ant-design/icons'
import ReactECharts from 'echarts-for-react'
import { runEmpirical, exportLatex, autoDetectVariables, searchStockData, fetchResearchData, uploadResearchData, getResearchDesign, getEmpiricalGuide, getPaperSection } from '../api'

const { Title, Text, Paragraph } = Typography
const { Panel } = Collapse

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

const MODEL_OPTIONS = [
  { value: 'ols', label: 'OLS回归', desc: '普通最小二乘法', when: '变量间无内生性，数据为截面或时间序列', color: '#1677ff', icon: '📊', difficulty: '入门' },
  { value: 'fixed', label: '固定效应', desc: '控制不可观测的个体/时间效应', when: '面板数据，存在不随时间变化的遗漏变量', color: '#52c41a', icon: '📋', difficulty: '进阶' },
  { value: 'random', label: '随机效应', desc: '假设个体效应与解释变量不相关', when: '面板数据，个体效应与变量无关（Hausman检验支持）', color: '#faad14', icon: '🎲', difficulty: '进阶' },
  { value: 'gmm', label: '2SLS/GMM', desc: '工具变量法，处理内生性', when: '存在反向因果、遗漏变量或测量误差', color: '#ff4d4f', icon: '🔧', difficulty: '高级' },
]

const SUGGESTED_TOPICS = [
  { name: 'ESG评级对企业融资成本的影响', dependent: '融资成本', independent: ['ESG评级'], tags: ['ESG', '公司金融'] },
  { name: '数字化转型对企业价值的影响', dependent: '企业价值', independent: ['数字化转型'], tags: ['数字经济', '公司治理'] },
  { name: '机构投资者持股与企业创新', dependent: 'ROE', independent: ['机构投资者持股'], tags: ['机构投资', '创新'] },
  { name: '股权集中度与公司绩效', dependent: 'ROE', independent: ['股权集中度'], tags: ['股权结构', '绩效'] },
  { name: '独立董事比例与盈余管理', dependent: 'ROE', independent: ['独立董事比例'], tags: ['公司治理', '会计'] },
  { name: '绿色创新对企业价值的影响', dependent: '企业价值', independent: ['绿色创新'], tags: ['绿色金融', '创新'] },
]

function InterpretPValue(p: number) {
  if (p < 0.01) return { text: '高度显著 (***)', color: '#ff4d4f', level: 3 }
  if (p < 0.05) return { text: '显著 (**)', color: '#fa8c16', level: 2 }
  if (p < 0.1) return { text: '边缘显著 (*)', color: '#faad14', level: 1 }
  return { text: '不显著', color: '#999', level: 0 }
}

export default function Empirical() {
  const [currentStep, setCurrentStep] = useState(0)
  const [activeTab, setActiveTab] = useState('config')

  // 数据与变量
  const [projectName, setProjectName] = useState('ESG评级对企业融资成本的影响')
  const [dependentVar, setDependentVar] = useState('融资成本')
  const [independentVars, setIndependentVars] = useState<string[]>(['ESG评级'])
  const [controlVars, setControlVars] = useState<string[]>(['企业规模', '资产负债率', '盈利能力'])
  const [newVar, setNewVar] = useState('')
  const [newControl, setNewControl] = useState('')
  const [modelType, setModelType] = useState('fixed')
  const [result, setResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [latex, setLatex] = useState('')
  const [stockSearch, setStockSearch] = useState('')
  const [stockResult, setStockResult] = useState<any>(null)
  const [stockLoading, setStockLoading] = useState(false)
  const [dataPreview, setDataPreview] = useState<any>(null)
  const [dataLoading, setDataLoading] = useState(false)

  // 科研工具
  const [rdQuestion, setRdQuestion] = useState('')
  const [rdResult, setRdResult] = useState<any>(null)
  const [rdLoading, setRdLoading] = useState(false)
  const [guideTask, setGuideTask] = useState('回归代码')
  const [guideOutcome, setGuideOutcome] = useState('')
  const [guideTreatment, setGuideTreatment] = useState('')
  const [guideControls, setGuideControls] = useState('')
  const [guideDesign, setGuideDesign] = useState('DID')
  const [guideResult, setGuideResult] = useState<any>(null)
  const [guideLoading, setGuideLoading] = useState(false)
  const [paperSection, setPaperSection] = useState('引言')
  const [paperInfo, setPaperInfo] = useState('')
  const [paperResult, setPaperResult] = useState<any>(null)
  const [paperLoading, setPaperLoading] = useState(false)

  const handleAutoDetect = async () => {
    try {
      const res = await autoDetectVariables(projectName)
      const d = res.data
      if (d.dependent_var) setDependentVar(d.dependent_var)
      if (d.independent_vars?.length) setIndependentVars(d.independent_vars)
      if (d.control_vars?.length) setControlVars(d.control_vars)
      message.success(`已识别: ${d.dependent_var} ← ${d.independent_vars?.join(', ')}`)
    } catch {
      for (const topic of SUGGESTED_TOPICS) {
        if (projectName.includes(topic.name.substring(0, 4))) {
          setDependentVar(topic.dependent)
          setIndependentVars(topic.independent)
          message.success(`已匹配: ${topic.dependent} ← ${topic.independent.join(', ')}`)
          return
        }
      }
      message.info('未匹配到预设课题，请手动设置变量')
    }
  }

  const handleSearchStock = async () => {
    if (!stockSearch.trim()) return
    setStockLoading(true)
    try {
      const res = await searchStockData(stockSearch.trim())
      setStockResult(res.data)
      if (res.data.error) message.warning(res.data.error)
      else { message.success(`获取到 ${stockSearch} 的财务数据`); setCurrentStep(1) }
    } catch { message.error('搜索失败') }
    setStockLoading(false)
  }

  const handlePreviewData = async () => {
    setDataLoading(true)
    try {
      const res = await fetchResearchData({ dependent_var: dependentVar, independent_vars: independentVars.join(','), control_vars: controlVars.join(',') })
      setDataPreview(res.data)
      message.success(`已获取 ${res.data.n_obs} 条数据`)
    } catch { message.error('数据获取失败') }
    setDataLoading(false)
  }

  const handleUpload = async (file: File) => {
    try {
      const res = await uploadResearchData(file)
      if (res.data.error) { message.error(res.data.error); return false }
      setDataPreview(res.data)
      message.success(`上传成功: ${res.data.n_obs} 条数据`)
      setCurrentStep(1)
    } catch { message.error('上传失败') }
    return false
  }

  const handleRun = async () => {
    setLoading(true)
    try {
      const res = await runEmpirical({ project_name: projectName, dependent_var: dependentVar, independent_vars: independentVars, control_vars: controlVars, model_type: modelType, data: dataPreview?.data || null })
      setResult(res.data)
      setCurrentStep(3)
      setActiveTab('results')
      message.success('回归完成')
    } catch { message.error('回归失败') }
    setLoading(false)
  }

  const handleExportLatex = async () => {
    try {
      const res = await exportLatex({ project_name: projectName, dependent_var: dependentVar, independent_vars: independentVars, control_vars: controlVars, model_type: modelType, data: dataPreview?.data || null })
      setLatex(res.data.latex)
      message.success('LaTeX已生成')
    } catch { message.error('导出失败') }
  }

  const handleResearchDesign = async () => {
    if (!rdQuestion.trim()) { message.warning('请输入研究问题'); return }
    setRdLoading(true)
    try {
      const res = await getResearchDesign({ research_question: rdQuestion, data_type: 'panel', unit: 'enterprise', time_span: '' })
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
      const res = await getPaperSection({ section: paperSection, research_info: paperInfo, findings: '', contributions: '' })
      setPaperResult(res.data)
    } catch { message.error('获取写作模板失败') }
    setPaperLoading(false)
  }

  const addIndependentVar = () => { if (newVar && !independentVars.includes(newVar)) { setIndependentVars([...independentVars, newVar]); setNewVar('') } }
  const addControlVar = () => { if (newControl && !controlVars.includes(newControl)) { setControlVars([...controlVars, newControl]); setNewControl('') } }

  const isMobile = window.innerWidth < 768

  // 系数表
  const tableColumns = result?.coefficients
    ? Object.entries(result.coefficients).map(([name, stats]: [string, any]) => ({
        key: name, variable: name, coef: stats.coef, stdErr: stats.std_err,
        tStat: stats.t_stat, pValue: stats.p_value,
      }))
    : []

  const tableCols = [
    { title: '变量', dataIndex: 'variable', key: 'variable', render: (v: string) => <Text strong>{v}</Text> },
    {
      title: '系数', dataIndex: 'coef', key: 'coef',
      render: (v: number, record: any) => {
        const stars = record.pValue < 0.01 ? '***' : record.pValue < 0.05 ? '**' : record.pValue < 0.1 ? '*' : ''
        return <span style={{ fontFamily: 'monospace' }}>{v?.toFixed(4)}<span style={{ color: '#ff4d4f', fontWeight: 700 }}>{stars}</span></span>
      },
    },
    { title: '标准误', dataIndex: 'stdErr', key: 'stdErr', render: (v: number) => <span style={{ fontFamily: 'monospace', color: '#666' }}>({v?.toFixed(4)})</span> },
    { title: 't值', dataIndex: 'tStat', key: 'tStat', render: (v: number) => <span style={{ fontFamily: 'monospace' }}>[{v?.toFixed(4)}]</span> },
    {
      title: '显著性', dataIndex: 'pValue', key: 'pValue',
      render: (v: number) => {
        const interp = InterpretPValue(v)
        return <Tooltip title={`p值 = ${v?.toFixed(4)}`}><Tag color={interp.color} style={{ margin: 0 }}>{interp.text}</Tag></Tooltip>
      },
    },
  ]

  const coefChartOption = result?.coefficients && result?.confidence_intervals
    ? {
        tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
        grid: { left: '3%', right: '10%', bottom: '3%', containLabel: true },
        xAxis: { type: 'value', name: '系数值' },
        yAxis: { type: 'category', data: Object.keys(result.coefficients) },
        series: [{
          type: 'bar',
          data: Object.entries(result.coefficients).map(([name, stats]: [string, any]) => ({
            value: stats.coef,
            itemStyle: { color: stats.p_value < 0.05 ? '#1677ff' : '#ccc', borderRadius: [0, 4, 4, 0] },
          })),
          barWidth: 20,
        }],
      }
    : null

  const vifOption = result?.vif && Object.keys(result.vif).length > 0
    ? {
        tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
        grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
        xAxis: { type: 'value', name: 'VIF值' },
        yAxis: { type: 'category', data: Object.keys(result.vif) },
        series: [{
          type: 'bar',
          data: Object.values(result.vif).map((v: any) => ({
            value: v,
            itemStyle: { color: v > 10 ? '#ff4d4f' : v > 5 ? '#faad14' : '#52c41a', borderRadius: [0, 4, 4, 0] },
          })),
          markLine: { data: [{ xAxis: 5, lineStyle: { color: '#faad14', type: 'dashed' } }, { xAxis: 10, lineStyle: { color: '#ff4d4f', type: 'dashed' } }] },
        }],
      }
    : null

  // 结论摘要
  const renderConclusion = () => {
    if (!result || result.error) return null
    const sigVars = Object.entries(result.coefficients || {}).filter(([_, s]: [string, any]) => s.p_value < 0.05)
    const mainVar = independentVars[0]
    const mainCoef = result.coefficients?.[mainVar]
    if (!mainCoef) return null
    const direction = mainCoef.coef > 0 ? '正向' : '负向'
    const interp = InterpretPValue(mainCoef.p_value)
    return (
      <Alert
        type={mainCoef.p_value < 0.05 ? 'success' : 'info'}
        showIcon
        icon={<CheckCircleOutlined />}
        style={{ marginBottom: 20 }}
        message={
          <div>
            <Text strong style={{ fontSize: 14 }}>结论摘要</Text>
            <div style={{ marginTop: 4 }}>
              <Text>「<Text strong>{mainVar}</Text>」对「<Text strong>{dependentVar}</Text>」的影响系数为 <Text strong style={{ fontFamily: 'monospace' }}>{mainCoef.coef?.toFixed(4)}</Text>，方向为 <Tag color={mainCoef.coef > 0 ? 'red' : 'green'}>{direction}</Tag>，
              显著性水平 <Text strong style={{ color: interp.color }}>{interp.text}</Text>。</Text>
            </div>
            <div style={{ marginTop: 4 }}>
              {mainCoef.p_value < 0.05
                ? <Text type="success">在5%水平下统计显著，假设得到支持。</Text>
                : <Text type="warning">在5%水平下不显著，假设未得到支持。</Text>}
            </div>
            {sigVars.length > 1 && (
              <div style={{ marginTop: 4 }}>
                <Text type="secondary">其他显著变量：{sigVars.filter(([name]) => name !== mainVar).map(([name]) => name).join('、')}</Text>
              </div>
            )}
          </div>
        }
      />
    )
  }

  return (
    <div>
      {/* 页面标题 */}
      <div style={{ marginBottom: 20 }}>
        <Title level={3} style={{ fontSize: isMobile ? 20 : 24, marginBottom: 4 }}>实证研究辅助</Title>
        <Text type="secondary" style={{ fontSize: isMobile ? 12 : 14 }}>从数据到论文，一站式实证分析工具</Text>
      </div>

      {/* 步骤导航 */}
      <Card size="small" style={{ marginBottom: 20 }}>
        <Steps current={currentStep} size="small" direction={isMobile ? 'vertical' : 'horizontal'}
          onChange={(step) => {
            if (step <= currentStep) {
              setCurrentStep(step)
              if (step < 3) setActiveTab('config')
            }
          }}
          items={[
            { title: '获取数据', description: isMobile ? '' : '搜索或上传数据' },
            { title: '配置模型', description: isMobile ? '' : '选择变量与方法' },
            { title: '运行分析', description: isMobile ? '' : '执行回归' },
            { title: '查看结果', description: isMobile ? '' : '解读与导出' },
          ]}
        />
      </Card>

      <Tabs activeKey={activeTab} onChange={(key) => { setActiveTab(key); if (key === 'config') setCurrentStep(Math.min(currentStep, 2)) }}
        items={[
          // ==================== 主工作区 ====================
          {
            key: 'config',
            label: <Space><DatabaseOutlined /> 配置分析</Space>,
            children: (
              <Row gutter={[16, 16]}>
                {/* 左侧：数据源 */}
                <Col xs={24} lg={8}>
                  <Card title={<Space><SearchOutlined />数据来源</Space>} size="small" style={{ marginBottom: 16 }}>
                    <div style={{ marginBottom: 12 }}>
                      <Text type="secondary" style={{ fontSize: 12 }}>输入A股股票代码获取财务数据</Text>
                      <Input
                        value={stockSearch} onChange={e => setStockSearch(e.target.value)}
                        onPressEnter={handleSearchStock}
                        placeholder="如 600519（贵州茅台）"
                        prefix={<SearchOutlined />}
                        style={{ marginTop: 8 }}
                      />
                      <Space style={{ marginTop: 8 }} size={8}>
                        <Button type="primary" icon={<SearchOutlined />} onClick={handleSearchStock} loading={stockLoading} block>搜索</Button>
                        <Upload beforeUpload={handleUpload} showUploadList={false} accept=".csv,.xlsx,.xls">
                          <Button icon={<UploadOutlined />} block>上传CSV</Button>
                        </Upload>
                      </Space>
                    </div>

                    {stockResult && !stockResult.error && (
                      <div style={{ background: '#f6ffed', borderRadius: 8, padding: 12, marginTop: 12 }}>
                        <Text strong>{stockResult.realtime?.name || stockResult.code}</Text>
                        <Row gutter={8} style={{ marginTop: 8 }}>
                          <Col span={12}><Statistic title="最新价" value={stockResult.realtime?.price || '--'} valueStyle={{ fontSize: 16, color: (stockResult.realtime?.change || 0) >= 0 ? '#cf1322' : '#3f8600' }} /></Col>
                          <Col span={12}><Statistic title="涨跌幅" value={`${stockResult.realtime?.change_pct > 0 ? '+' : ''}${stockResult.realtime?.change_pct || '--'}%`} valueStyle={{ fontSize: 16 }} /></Col>
                        </Row>
                      </div>
                    )}
                  </Card>

                  {/* 热门课题 */}
                  <Card title={<Space><BulbOutlined />热门研究方向</Space>} size="small">
                    {SUGGESTED_TOPICS.map(t => (
                      <div key={t.name}
                        onClick={() => { setProjectName(t.name); setDependentVar(t.dependent); setIndependentVars(t.independent); setCurrentStep(1) }}
                        style={{
                          padding: '8px 10px', marginBottom: 6, borderRadius: 8, cursor: 'pointer', fontSize: 13,
                          background: projectName === t.name ? '#e6f4ff' : '#fafafa',
                          border: projectName === t.name ? '1px solid #1677ff' : '1px solid transparent',
                          transition: 'all 0.2s',
                        }}>
                        <div style={{ fontWeight: projectName === t.name ? 600 : 400 }}>{t.name}</div>
                        <div style={{ marginTop: 4 }}>
                          {t.tags.map(tag => <Tag key={tag} style={{ fontSize: 10, margin: '0 4px 4px 0' }}>{tag}</Tag>)}
                        </div>
                      </div>
                    ))}
                  </Card>
                </Col>

                {/* 右侧：变量配置 */}
                <Col xs={24} lg={16}>
                  {/* 数据预览 */}
                  {dataPreview && (
                    <Card
                      title={<Space>数据预览 <Tag color={dataPreview.data_source === 'simulated' ? 'orange' : 'green'}>{dataPreview.data_source === 'simulated' ? '模拟数据' : '真实数据'}</Tag></Space>}
                      size="small" style={{ marginBottom: 16 }}
                      extra={<Text type="secondary" style={{ fontSize: 12 }}>{dataPreview.n_obs}条数据 · {dataPreview.firms || 0}家企业</Text>}
                    >
                      <Table
                        dataSource={(dataPreview.preview || []).map((r: any, i: number) => ({ ...r, key: i }))}
                        columns={(dataPreview.columns || []).slice(0, 8).map((c: string) => ({
                          title: c, dataIndex: c, key: c, ellipsis: true,
                          render: (v: any) => typeof v === 'number' ? v.toFixed(2) : v,
                        }))}
                        pagination={false} size="small" scroll={{ x: 600 }}
                      />
                    </Card>
                  )}

                  {/* 研究课题 */}
                  <Card size="small" style={{ marginBottom: 16 }}>
                    <Row gutter={16} align="middle">
                      <Col flex="auto">
                        <Text type="secondary" style={{ fontSize: 12 }}>研究课题</Text>
                        <Input
                          value={projectName} onChange={e => setProjectName(e.target.value)}
                          placeholder="输入研究课题，如：ESG评级对企业融资成本的影响"
                          style={{ marginTop: 4 }}
                        />
                      </Col>
                      <Col>
                        <Button icon={<ThunderboltOutlined />} onClick={handleAutoDetect} style={{ marginTop: 18 }}>智能识别变量</Button>
                      </Col>
                    </Row>
                  </Card>

                  {/* 变量配置 */}
                  <Card title={<Space><TeamOutlined />变量配置</Space>} size="small" style={{ marginBottom: 16 }}>
                    <Alert type="info" showIcon style={{ marginBottom: 16 }}
                      message={<span><Text strong>Y = f(X₁, X₂, ...)</Text> — 被解释变量是结果，解释变量是原因，控制变量排除干扰</span>} />

                    <Row gutter={16}>
                      <Col xs={24} md={8}>
                        <div style={{ background: '#f6ffed', borderRadius: 8, padding: 12, marginBottom: 12 }}>
                          <Text strong style={{ fontSize: 13, color: '#52c41a' }}>被解释变量 (Y)</Text>
                          <Text type="secondary" style={{ fontSize: 11, display: 'block', marginTop: 2 }}>你想要解释的结果</Text>
                          <Input value={dependentVar} onChange={e => setDependentVar(e.target.value)} style={{ marginTop: 8 }} placeholder="如：融资成本" />
                        </div>
                      </Col>
                      <Col xs={24} md={16}>
                        <div style={{ background: '#e6f4ff', borderRadius: 8, padding: 12, marginBottom: 12 }}>
                          <Text strong style={{ fontSize: 13, color: '#1677ff' }}>核心解释变量 (X)</Text>
                          <Text type="secondary" style={{ fontSize: 11, display: 'block', marginTop: 2 }}>你认为会影响Y的因素</Text>
                          <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginTop: 8 }}>
                            {independentVars.map(v => (
                              <Tag key={v} closable onClose={() => setIndependentVars(independentVars.filter(x => x !== v))} color="blue">{v}</Tag>
                            ))}
                            <Input size="small" value={newVar} onChange={e => setNewVar(e.target.value)} onPressEnter={addIndependentVar}
                              style={{ width: 120 }} placeholder="添加变量" suffix={<PlusOutlined onClick={addIndependentVar} style={{ cursor: 'pointer' }} />} />
                          </div>
                        </div>
                      </Col>
                    </Row>

                    <div style={{ background: '#fafafa', borderRadius: 8, padding: 12 }}>
                      <Text strong style={{ fontSize: 13 }}>控制变量</Text>
                      <Text type="secondary" style={{ fontSize: 11, display: 'block', marginTop: 2 }}>其他可能影响Y的变量，用于排除干扰</Text>
                      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginTop: 8 }}>
                        {controlVars.map(v => (
                          <Tag key={v} closable onClose={() => setControlVars(controlVars.filter(x => x !== v))}>{v}</Tag>
                        ))}
                        <Input size="small" value={newControl} onChange={e => setNewControl(e.target.value)} onPressEnter={addControlVar}
                          style={{ width: 120 }} placeholder="添加控制变量" suffix={<PlusOutlined onClick={addControlVar} style={{ cursor: 'pointer' }} />} />
                      </div>
                    </div>
                  </Card>

                  {/* 计量方法选择 */}
                  <Card title={<Space><CodeOutlined />选择计量方法</Space>} size="small" style={{ marginBottom: 16 }}>
                    <Alert type="info" showIcon style={{ marginBottom: 16 }}
                      message="不同方法适用于不同研究场景。不确定时选OLS，后续可替换为更高级方法。" />
                    <Row gutter={[12, 12]}>
                      {MODEL_OPTIONS.map(m => (
                        <Col xs={12} sm={6} key={m.value}>
                          <div
                            onClick={() => setModelType(m.value)}
                            style={{
                              padding: 12, borderRadius: 10, cursor: 'pointer', textAlign: 'center',
                              background: modelType === m.value ? `${m.color}10` : '#fafafa',
                              border: modelType === m.value ? `2px solid ${m.color}` : '2px solid transparent',
                              transition: 'all 0.2s',
                            }}>
                            <div style={{ fontSize: 24, marginBottom: 4 }}>{m.icon}</div>
                            <Text strong style={{ fontSize: 13 }}>{m.label}</Text>
                            <br />
                            <Tag color={modelType === m.value ? m.color : 'default'} style={{ marginTop: 4, fontSize: 10 }}>{m.difficulty}</Tag>
                            <div style={{ fontSize: 11, color: '#999', marginTop: 4, lineHeight: 1.4 }}>{m.when}</div>
                          </div>
                        </Col>
                      ))}
                    </Row>
                  </Card>

                  {/* 操作按钮 */}
                  <Card size="small" style={{ background: 'linear-gradient(135deg, #f0f5ff 0%, #e6f7ff 100%)' }}>
                    <Row gutter={12} align="middle">
                      <Col flex="auto">
                        <Space wrap>
                          <Button type="primary" icon={<PlayCircleOutlined />} onClick={handleRun} loading={loading} size="large">
                            运行回归
                          </Button>
                          <Button icon={<BarChartOutlined />} onClick={handlePreviewData} loading={dataLoading}>
                            预览数据
                          </Button>
                          <Button icon={<ExportOutlined />} onClick={handleExportLatex} disabled={!result}>
                            导出LaTeX
                          </Button>
                          <Button icon={<ReloadOutlined />} onClick={() => { setResult(null); setLatex(''); setDataPreview(null); setStockResult(null); setCurrentStep(0) }}>
                            重置
                          </Button>
                        </Space>
                      </Col>
                    </Row>
                  </Card>
                </Col>
              </Row>
            ),
          },

          // ==================== 回归结果 ====================
          {
            key: 'results',
            label: <Space><BarChartOutlined /> 回归结果</Space>,
            children: result && !result.error ? (
              <div>
                {renderConclusion()}

                {result.data_source === 'simulated' && (
                  <Alert type="error" showIcon message="当前回归基于模拟数据" description={result.data_note || '结果仅供方法演示，不可用于学术论文'} style={{ marginBottom: 20 }} />
                )}

                {/* 系数表 */}
                <Card title="回归系数表" style={{ marginBottom: 20 }}>
                  <Table columns={tableCols} dataSource={tableColumns} pagination={false} size="small" />
                  <Divider />
                  <Row gutter={[16, 16]}>
                    <Col xs={12} sm={4}><Statistic title="R²" value={result.r_squared} precision={4} /></Col>
                    <Col xs={12} sm={4}><Statistic title="调整R²" value={result.adj_r_squared} precision={4} /></Col>
                    <Col xs={12} sm={4}><Statistic title="F统计量" value={result.f_statistic} precision={4} /></Col>
                    <Col xs={12} sm={4}><Statistic title="样本量" value={result.n_obs} /></Col>
                    <Col xs={12} sm={4}><Text type="secondary" style={{ fontSize: 12 }}>模型</Text><br /><Tag color="blue">{result.model_type?.toUpperCase()}</Tag></Col>
                    <Col xs={12} sm={4}><Text type="secondary" style={{ fontSize: 12 }}>标准误</Text><br /><Tag>{result.robust_std || 'OLS'}</Tag></Col>
                  </Row>
                </Card>

                {/* 图表 */}
                <Row gutter={[16, 16]} style={{ marginBottom: 20 }}>
                  {coefChartOption && (
                    <Col xs={24} lg={12}>
                      <Card title="系数可视化" size="small">
                        <ReactECharts option={coefChartOption} style={{ height: 280 }} />
                      </Card>
                    </Col>
                  )}
                  {vifOption && (
                    <Col xs={24} lg={12}>
                      <Card title="多重共线性检验 (VIF)" size="small">
                        <Alert type="info" showIcon style={{ marginBottom: 8 }}
                          message={<span>VIF &lt; 5 无共线性，5-10 中等，&gt; 10 严重共线性</span>} />
                        <ReactECharts option={vifOption} style={{ height: 280 }} />
                      </Card>
                    </Col>
                  )}
                </Row>

                {/* 模型诊断 */}
                {result.diagnostics && (
                  <Card title="模型诊断" size="small" style={{ marginBottom: 20 }}>
                    <Row gutter={[16, 16]}>
                      <Col xs={12} sm={6}>
                        <Tooltip title="检验残差自相关，接近2表示无自相关">
                          <Statistic title="Durbin-Watson" value={result.diagnostics.durbin_watson} precision={4}
                            valueStyle={{ color: Math.abs(result.diagnostics.durbin_watson - 2) > 0.5 ? '#faad14' : '#3f8600' }} />
                        </Tooltip>
                        <Text type="secondary" style={{ fontSize: 11 }}>{Math.abs(result.diagnostics.durbin_watson - 2) > 0.5 ? '可能存在自相关' : '无自相关'}</Text>
                      </Col>
                      <Col xs={12} sm={6}>
                        <Tooltip title="检验残差正态性，p>0.05表示正态">
                          <Statistic title="Jarque-Bera (p)" value={result.diagnostics.jarque_bera} precision={4}
                            valueStyle={{ color: result.diagnostics.jarque_bera < 0.05 ? '#faad14' : '#3f8600' }} />
                        </Tooltip>
                        <Text type="secondary" style={{ fontSize: 11 }}>{result.diagnostics.jarque_bera < 0.05 ? '残差非正态' : '残差正态'}</Text>
                      </Col>
                      <Col xs={12} sm={6}>
                        <Tooltip title="检验异方差，p>0.05表示同方差">
                          <Statistic title="White Test (p)" value={result.diagnostics.white_test} precision={4}
                            valueStyle={{ color: result.diagnostics.white_test < 0.05 ? '#faad14' : '#3f8600' }} />
                        </Tooltip>
                        <Text type="secondary" style={{ fontSize: 11 }}>{result.diagnostics.white_test < 0.05 ? '可能存在异方差' : '同方差'}</Text>
                      </Col>
                      <Col xs={12} sm={6}>
                        <Statistic title="偏度 / 峰度" value={`${result.diagnostics.skewness} / ${result.diagnostics.kurtosis}`} />
                      </Col>
                    </Row>
                  </Card>
                )}

                {/* 稳健性检验 */}
                {result.robustness_suggestions && (
                  <Card title="稳健性检验清单" size="small" style={{ marginBottom: 20 }}>
                    <Alert type="info" showIcon style={{ marginBottom: 8 }}
                      message="完成以下检验可增强论文结论的可信度" />
                    {result.robustness_suggestions.map((s: string, i: number) => (
                      <div key={i} style={{ padding: '6px 0', fontSize: 13, borderBottom: '1px solid #f0f0f0' }}>
                        <Checkbox /> {s}
                      </div>
                    ))}
                  </Card>
                )}

                {latex && (
                  <Card title="LaTeX表格代码" size="small">
                    <pre style={{ background: '#f5f5f5', padding: 12, borderRadius: 8, fontSize: 12, overflow: 'auto', maxHeight: 300 }}>{latex}</pre>
                  </Card>
                )}
              </div>
            ) : result?.error ? (
              <Alert type="error" message="回归错误" description={result.error} showIcon />
            ) : (
              <div style={{ textAlign: 'center', padding: '60px 0' }}>
                <BarChartOutlined style={{ fontSize: 48, color: '#d9d9d9' }} />
                <div style={{ marginTop: 16 }}>
                  <Text type="secondary">请先在「配置分析」中配置变量并运行回归</Text>
                </div>
              </div>
            ),
          },

          // ==================== 科研工具 ====================
          {
            key: 'tools',
            label: <Space><ExperimentOutlined /> 科研工具</Space>,
            children: (
              <Collapse defaultActiveKey={['design']} style={{ background: 'transparent' }}>
                {/* 研究设计 */}
                <Panel header={<Space><ExperimentOutlined /> 研究设计 <Text type="secondary" style={{ fontSize: 12 }}>输入研究问题，推荐因果识别策略</Text></Space>} key="design">
                  <Alert type="info" showIcon style={{ marginBottom: 12 }}
                    message="描述你的研究问题，AI将推荐最适合的因果识别方法（如DID、IV、RDD等）" />
                  <Input.TextArea value={rdQuestion} onChange={e => setRdQuestion(e.target.value)}
                    placeholder="例如：数字普惠金融发展对县域经济增长的影响研究"
                    autoSize={{ minRows: 2, maxRows: 4 }} />
                  <Button type="primary" icon={<ExperimentOutlined />} loading={rdLoading} onClick={handleResearchDesign} style={{ marginTop: 8 }}>生成识别方案</Button>

                  {rdResult && (
                    <div style={{ marginTop: 16 }}>
                      {rdResult.recommendations?.map((rec: any, idx: number) => (
                        <Card key={idx} size="small" style={{ marginBottom: 12, border: idx === 0 ? '2px solid #1677ff' : '1px solid #f0f0f0' }}
                          title={<Space>{idx === 0 && <Tag color="blue">推荐</Tag>}<Text strong>{rec.name}</Text></Space>}>
                          <Text type="secondary"><BulbOutlined /> 适用场景：</Text><br /><Text>{rec.when}</Text>
                          <Divider style={{ margin: '8px 0' }} />
                          <Text type="secondary">回归方程：</Text>
                          <pre style={{ background: '#f5f5f5', padding: 8, borderRadius: 6, fontSize: 12, whiteSpace: 'pre-wrap' }}>{rec.model}</pre>
                          {rec.fixed_effects && <><Text type="secondary">固定效应：</Text><Text>{rec.fixed_effects}</Text><br /></>}
                          <Text type="secondary">关键检验：</Text>
                          <ul style={{ margin: '4px 0', paddingLeft: 20 }}>{rec.tests?.map((t: string, i: number) => <li key={i} style={{ fontSize: 12 }}>{t}</li>)}</ul>
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
                </Panel>

                {/* 实证操作 */}
                <Panel header={<Space><BookOutlined /> 实证操作 <Text type="secondary" style={{ fontSize: 12 }}>生成回归代码、变量构造方法</Text></Space>} key="empirical">
                  <Row gutter={12} style={{ marginBottom: 12 }}>
                    <Col span={8}>
                      <Text type="secondary" style={{ fontSize: 12 }}>任务类型</Text>
                      <Select value={guideTask} onChange={setGuideTask} size="small" style={{ width: '100%' }}
                        options={[{ value: '回归代码', label: '回归代码' }, { value: '描述统计', label: '描述统计' }, { value: '变量构造', label: '变量构造' }, { value: '数据推荐', label: '数据推荐' }]} />
                    </Col>
                    {guideTask === '回归代码' && (
                      <>
                        <Col span={5}><Text type="secondary" style={{ fontSize: 12 }}>被解释变量</Text><Input size="small" value={guideOutcome} onChange={e => setGuideOutcome(e.target.value)} placeholder="如 Y" /></Col>
                        <Col span={5}><Text type="secondary" style={{ fontSize: 12 }}>处理变量</Text><Input size="small" value={guideTreatment} onChange={e => setGuideTreatment(e.target.value)} placeholder="如 treat_post" /></Col>
                        <Col span={5}><Text type="secondary" style={{ fontSize: 12 }}>控制变量</Text><Input size="small" value={guideControls} onChange={e => setGuideControls(e.target.value)} placeholder="如 x1, x2" /></Col>
                        <Col span={1}><Text type="secondary" style={{ fontSize: 12 }}>策略</Text><Select value={guideDesign} onChange={setGuideDesign} size="small" style={{ width: '100%' }}
                          options={[{ value: 'DID', label: 'DID' }, { value: 'IV', label: 'IV' }, { value: 'RDD', label: 'RDD' }, { value: 'OLS', label: 'OLS' }]} /></Col>
                      </>
                    )}
                    {guideTask === '变量构造' && (
                      <Col span={16}><Text type="secondary" style={{ fontSize: 12 }}>变量列表（逗号分隔）</Text><Input size="small" value={guideOutcome} onChange={e => setGuideOutcome(e.target.value)} placeholder="如 企业规模, ROE, 资产负债率" /></Col>
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
                    </div>
                  )}
                </Panel>

                {/* 论文写作 */}
                <Panel header={<Space><FileTextOutlined /> 论文写作 <Text type="secondary" style={{ fontSize: 12 }}>生成学术规范的段落模板</Text></Space>} key="writing">
                  <Row gutter={12} style={{ marginBottom: 12 }}>
                    <Col span={6}>
                      <Text type="secondary" style={{ fontSize: 12 }}>章节类型</Text>
                      <Select value={paperSection} onChange={setPaperSection} size="small" style={{ width: '100%' }}
                        options={[{ value: '引言', label: '引言' }, { value: '摘要', label: '摘要' }, { value: '文献综述', label: '文献综述' }, { value: '结论', label: '结论' }]} />
                    </Col>
                    <Col span={18}>
                      <Text type="secondary" style={{ fontSize: 12 }}>研究信息</Text>
                      <Input.TextArea value={paperInfo} onChange={e => setPaperInfo(e.target.value)}
                        placeholder="例如：研究数字普惠金融对县域经济增长的影响，发现数字金融显著促进增长"
                        autoSize={{ minRows: 2, maxRows: 4 }} />
                    </Col>
                  </Row>
                  <Button type="primary" icon={<FileTextOutlined />} loading={paperLoading} onClick={handlePaperSection}>生成模板</Button>

                  {paperResult && (
                    <div style={{ marginTop: 16 }}>
                      <Card size="small" style={{ marginBottom: 12 }}><Text type="secondary">结构：</Text><Text>{paperResult.structure}</Text></Card>
                      <Card size="small" title="段落模板" style={{ marginBottom: 12 }}>
                        <pre style={{ background: '#f5f5f5', padding: 12, borderRadius: 6, fontSize: 12, whiteSpace: 'pre-wrap', lineHeight: 1.8 }}>{paperResult.template}</pre>
                        <Button size="small" icon={<CopyOutlined />} onClick={() => copyToClipboard(paperResult.template || '')} style={{ marginTop: 8 }}>复制模板</Button>
                      </Card>
                      {paperResult.tips && (
                        <Card size="small" title="写作要点">
                          {paperResult.tips.map((tip: string, i: number) => (
                            <div key={i} style={{ padding: '4px 0', fontSize: 12, borderBottom: '1px solid #f0f0f0' }}>✓ {tip}</div>
                          ))}
                        </Card>
                      )}
                    </div>
                  )}
                </Panel>
              </Collapse>
            ),
          },
        ]}
      />
    </div>
  )
}
