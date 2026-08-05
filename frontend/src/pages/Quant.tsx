import { useState, useEffect } from 'react'
import { Row, Col, Card, Button, Select, InputNumber, DatePicker, Typography, Statistic, Space, Divider, Spin, message, Tag, Tooltip, Alert, Table, Tabs } from 'antd'
import { PlayCircleOutlined, DownloadOutlined, CodeOutlined, SwapOutlined, ThunderboltOutlined, ExperimentOutlined, RobotOutlined } from '@ant-design/icons'
import ReactECharts from 'echarts-for-react'
import dayjs from 'dayjs'
import { runBacktest, listStrategies, listVnpyStrategies, optimizeStrategy } from '../api'

const { Title, Text } = Typography
const { RangePicker } = DatePicker

const LEGACY_PARAMS: Record<string, { key: string; label: string; default: number; min: number; max: number; desc: string }[]> = {
  momentum: [
    { key: 'lookback', label: '回看周期(日)', default: 20, min: 5, max: 60, desc: '计算动量的回看天数' },
    { key: 'top_n', label: '持仓数量', default: 5, min: 1, max: 20, desc: '每次买入前N名' },
  ],
  mean_reversion: [
    { key: 'ma_window', label: '均线窗口', default: 20, min: 5, max: 60, desc: '计算均线的天数' },
    { key: 'entry_std', label: '入场标准差', default: 2.0, min: 0.5, max: 4.0, desc: '偏离几个标准差触发信号' },
  ],
  multi_factor: [
    { key: 'lookback', label: '回看周期(日)', default: 20, min: 5, max: 60, desc: '因子计算窗口' },
    { key: 'top_n', label: '持仓数量', default: 5, min: 1, max: 20, desc: '多因子打分前N名' },
  ],
  pair_trading: [
    { key: 'lookback', label: '价差窗口', default: 60, min: 20, max: 120, desc: '价差均值计算窗口' },
    { key: 'entry_threshold', label: '入场阈值', default: 2.0, min: 1.0, max: 3.0, desc: '价差偏离几个标准差' },
  ],
}

const VNPY_KEYS = ['double_ma', 'atr_rsi', 'bollinger', 'donchian', 'keltner']

export default function Quant() {
  const [strategies, setStrategies] = useState<any[]>([])
  const [vnpyStrategies, setVnpyStrategies] = useState<Record<string, any>>({})
  const [pools, setPools] = useState<any[]>([])
  const [strategyType, setStrategyType] = useState('momentum')
  const [stockPool, setStockPool] = useState('hs300')
  const [dateRange, setDateRange] = useState<[dayjs.Dayjs, dayjs.Dayjs]>([
    dayjs('2019-01-01'),
    dayjs('2024-12-31'),
  ])
  const [initialCapital, setInitialCapital] = useState(1000000)
  const [params, setParams] = useState<Record<string, any>>({})
  const [result, setResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [optimizing, setOptimizing] = useState(false)
  const [optResults, setOptResults] = useState<any[]>([])
  const [activeTab, setActiveTab] = useState('equity')

  const isVnpy = VNPY_KEYS.includes(strategyType)

  useEffect(() => {
    listStrategies().then((res) => {
      setStrategies(res.data.strategies || [])
      setPools(res.data.pools || [])
    }).catch(() => {})
    listVnpyStrategies().then((res) => {
      setVnpyStrategies(res.data.strategies || {})
    }).catch(() => {})
  }, [])

  useEffect(() => {
    const defaults: Record<string, any> = {}
    if (isVnpy) {
      const info = vnpyStrategies[strategyType]
      if (info?.params) {
        info.params.forEach((p: any) => { defaults[p.key] = p.default })
      }
    } else {
      const cfg = LEGACY_PARAMS[strategyType] || []
      cfg.forEach((p) => { defaults[p.key] = p.default })
    }
    setParams(defaults)
  }, [strategyType, vnpyStrategies])

  const handleBacktest = async () => {
    setLoading(true)
    try {
      const res = await runBacktest({
        strategy_type: strategyType,
        stock_pool: stockPool,
        start_date: dateRange[0].format('YYYY-MM-DD'),
        end_date: dateRange[1].format('YYYY-MM-DD'),
        initial_capital: initialCapital,
        params: isVnpy ? { ...params, _strategy_type: strategyType } : params,
      })
      setResult(res.data)
      message.success('回测完成')
    } catch {
      message.error('回测失败')
    }
    setLoading(false)
  }

  const handleOptimize = async () => {
    setOptimizing(true)
    try {
      const res = await optimizeStrategy({
        strategy_type: strategyType,
        stock_pool: stockPool,
        start_date: dateRange[0].format('YYYY-MM-DD'),
        end_date: dateRange[1].format('YYYY-MM-DD'),
        initial_capital: initialCapital,
        params: { _strategy_type: strategyType },
      })
      setOptResults(res.data.results || [])
      message.success(`优化完成，共${res.data.results?.length || 0}组参数`)
    } catch {
      message.error('优化失败')
    }
    setOptimizing(false)
  }

  const applyOptParams = (p: Record<string, any>) => {
    setParams(p)
    message.success('已应用最优参数')
  }

  const strategyCategoryMap: Record<string, string> = {
    momentum: '趋势跟踪', mean_reversion: '统计套利', multi_factor: '因子投资', pair_trading: '统计套利',
  }

  const getCurrentParams = () => isVnpy ? (vnpyStrategies[strategyType]?.params || []) : (LEGACY_PARAMS[strategyType] || [])

  // equity curve chart
  const chartOption = result?.equity_curve
    ? {
        tooltip: { trigger: 'axis', axisPointer: { type: 'cross' } },
        legend: { data: ['策略净值', '基准(线性)'], top: 5 },
        grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
        xAxis: { type: 'category', data: result.equity_curve.map((d: any) => d.date), axisLabel: { fontSize: 11 } },
        yAxis: { type: 'value', axisLabel: { formatter: (v: number) => (v / 10000).toFixed(0) + '万' } },
        series: [
          {
            name: '策略净值', type: 'line', data: result.equity_curve.map((d: any) => d.value),
            smooth: true, lineStyle: { color: '#1677ff', width: 2 },
            areaStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: 'rgba(22,119,255,0.3)' }, { offset: 1, color: 'rgba(22,119,255,0.02)' }] } },
            itemStyle: { color: '#1677ff' },
          },
          {
            name: '基准(线性)', type: 'line',
            data: result.equity_curve.map((_: any, i: number) => {
              const s = result.equity_curve[0].value, e = result.equity_curve[result.equity_curve.length - 1].value
              return s + (e - s) * (i / (result.equity_curve.length - 1))
            }),
            lineStyle: { color: '#aaa', width: 1, type: 'dashed' }, itemStyle: { color: '#aaa' },
          },
        ],
      }
    : null

  // drawdown chart
  const drawdownOption = result?.equity_curve
    ? (() => {
        const values = result.equity_curve.map((d: any) => d.value)
        let peak = values[0]
        const dd = values.map((v: number) => { if (v > peak) peak = v; return ((v - peak) / peak) * 100 })
        return {
          tooltip: { trigger: 'axis', formatter: (p: any) => `${p[0].axisValue}<br/>回撤: ${p[0].value.toFixed(2)}%` },
          grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
          xAxis: { type: 'category', data: result.equity_curve.map((d: any) => d.date), axisLabel: { fontSize: 10 } },
          yAxis: { type: 'value', axisLabel: { formatter: (v: number) => v.toFixed(0) + '%' }, max: 0 },
          series: [{ type: 'line', data: dd, lineStyle: { color: '#ff4d4f', width: 1.5 }, areaStyle: { color: 'rgba(255,77,79,0.15)' }, itemStyle: { color: '#ff4d4f' }, showSymbol: false }],
        }
      })()
    : null

  // trade log
  const tradeColumns = [
    { title: '日期', dataIndex: 'date', key: 'date', width: 100 },
    { title: '方向', dataIndex: 'direction', key: 'direction', render: (v: string) => <Tag color={v === 'LONG' ? 'green' : 'red'}>{v === 'LONG' ? '做多' : '做空'}</Tag> },
    { title: '开平', dataIndex: 'offset', key: 'offset', render: (v: string) => <Tag>{v === 'OPEN' ? '开仓' : '平仓'}</Tag> },
    { title: '价格', dataIndex: 'price', key: 'price', render: (v: number) => v?.toFixed(2) },
    { title: '数量', dataIndex: 'volume', key: 'volume' },
    { title: '手续费', dataIndex: 'commission', key: 'commission', render: (v: number) => v?.toFixed(2) },
  ]

  const optColumns = [
    { title: '参数组合', dataIndex: 'params', key: 'params', render: (v: Record<string, any>) => Object.entries(v).map(([k, val]) => <Tag key={k}>{k}={val}</Tag>) },
    { title: 'Sharpe', key: 'sharpe', render: (_: any, r: any) => r.metrics?.sharpe_ratio?.toFixed(2) },
    { title: '年化收益', key: 'annual', render: (_: any, r: any) => `${r.metrics?.annual_return?.toFixed(2)}%` },
    { title: '最大回撤', key: 'dd', render: (_: any, r: any) => <Text type="danger">{r.metrics?.max_drawdown?.toFixed(2)}%</Text> },
    { title: '胜率', key: 'wr', render: (_: any, r: any) => `${r.metrics?.win_rate?.toFixed(1)}%` },
    { title: '操作', key: 'action', render: (_: any, r: any) => <Button size="small" type="link" onClick={() => applyOptParams(r.params)}>应用</Button> },
  ]

  return (
    <div>
      <div className="page-header">
        <Title level={3}>📈 量化策略回测</Title>
        <Text type="secondary">基于vnpy框架的专业量化回测，支持参数优化与交易日志</Text>
      </div>

      <Row gutter={24}>
        {/* 左侧策略列表 */}
        <Col xs={24} lg={8}>
          {/* vnpy策略 */}
          <Card title={<><RobotOutlined /> CTA策略 (vnpy)</>} size="small" style={{ marginBottom: 16 }}>
            {Object.entries(vnpyStrategies).map(([key, info]: [string, any]) => (
              <div
                key={key}
                onClick={() => setStrategyType(key)}
                style={{
                  padding: '10px 12px', marginBottom: 6, borderRadius: 8, cursor: 'pointer',
                  background: strategyType === key ? '#e6f4ff' : '#fafafa',
                  border: strategyType === key ? '1px solid #1677ff' : '1px solid transparent',
                }}
              >
                <Space>
                  <Text strong style={{ color: strategyType === key ? '#1677ff' : undefined }}>{info.name}</Text>
                  <Tag color={strategyType === key ? 'blue' : 'default'} style={{ fontSize: 10 }}>{info.category}</Tag>
                </Space>
                <br />
                <Text type="secondary" style={{ fontSize: 12 }}>{info.description}</Text>
              </div>
            ))}
          </Card>

          {/* 传统策略 */}
          <Card title="📋 经典策略" size="small" style={{ marginBottom: 16 }}>
            {strategies.map((s: any) => (
              <div
                key={s.key}
                onClick={() => setStrategyType(s.key)}
                style={{
                  padding: '10px 12px', marginBottom: 6, borderRadius: 8, cursor: 'pointer',
                  background: strategyType === s.key ? '#e6f4ff' : '#fafafa',
                  border: strategyType === s.key ? '1px solid #1677ff' : '1px solid transparent',
                }}
              >
                <Space>
                  <Text strong style={{ color: strategyType === s.key ? '#1677ff' : undefined }}>{s.name}</Text>
                  <Tag color={strategyType === s.key ? 'blue' : 'default'} style={{ fontSize: 10 }}>{s.category || strategyCategoryMap[s.key]}</Tag>
                </Space>
                <br />
                <Text type="secondary" style={{ fontSize: 12 }}>{s.description}</Text>
              </div>
            ))}
          </Card>

          {/* 策略参数 */}
          <Card title="🔧 策略参数" size="small" style={{ marginBottom: 16 }}>
            {getCurrentParams().map((p: any) => (
              <div key={p.key} style={{ marginBottom: 10 }}>
                <Tooltip title={p.desc}>
                  <Text strong style={{ fontSize: 13 }}>{p.label}</Text>
                </Tooltip>
                <InputNumber
                  value={params[p.key]}
                  onChange={(v) => v !== null && setParams({ ...params, [p.key]: v })}
                  min={p.min} max={p.max}
                  step={typeof p.default === 'number' && p.default % 1 !== 0 ? 0.5 : 1}
                  style={{ width: '100%', marginTop: 4 }}
                />
              </div>
            ))}
            {isVnpy && (
              <Button
                icon={<ExperimentOutlined />}
                onClick={handleOptimize}
                loading={optimizing}
                block
                style={{ marginTop: 8 }}
              >
                参数优化 (网格搜索)
              </Button>
            )}
          </Card>

          {/* 风险指标说明 */}
          <Card title="📊 风险指标" size="small">
            {[
              { name: 'Sharpe比率', desc: '每单位风险的超额收益' },
              { name: 'Sortino比率', desc: '只考虑下行风险的收益风险比' },
              { name: 'Calmar比率', desc: '年化收益/最大回撤' },
              { name: '胜率', desc: '正收益天数占比' },
              { name: '盈亏比', desc: '平均盈利/平均亏损' },
            ].map((m) => (
              <div key={m.name} style={{ padding: '3px 0', fontSize: 12, borderBottom: '1px solid #f0f0f0' }}>
                <Text strong>{m.name}</Text>
                <Text type="secondary" style={{ marginLeft: 8 }}>{m.desc}</Text>
              </div>
            ))}
          </Card>
        </Col>

        {/* 右侧配置和结果 */}
        <Col xs={24} lg={16}>
          <Card title="⚙️ 策略配置" style={{ marginBottom: 16 }}>
            <Row gutter={16}>
              <Col span={12}>
                <Text strong>股票池: </Text>
                <Select
                  value={stockPool} onChange={setStockPool}
                  style={{ width: '100%', marginTop: 4 }}
                  options={pools.map((p: any) => ({ value: p.key, label: `${p.name} (${p.count}只)` }))}
                />
              </Col>
              <Col span={12}>
                <Text strong>回测区间: </Text>
                <RangePicker value={dateRange} onChange={(v) => v && setDateRange(v as any)} style={{ width: '100%', marginTop: 4 }} />
              </Col>
              <Col span={12} style={{ marginTop: 16 }}>
                <Text strong>初始资金: </Text>
                <InputNumber
                  value={initialCapital} onChange={(v) => v && setInitialCapital(v)}
                  style={{ width: '100%', marginTop: 4 }}
                  formatter={(v) => `${v}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
                />
              </Col>
            </Row>
            <Space style={{ marginTop: 16 }}>
              <Button type="primary" icon={<PlayCircleOutlined />} onClick={handleBacktest} loading={loading} size="large">
                开始回测
              </Button>
              {isVnpy && (
                <Button icon={<ThunderboltOutlined />} onClick={handleOptimize} loading={optimizing}>
                  参数优化
                </Button>
              )}
            </Space>
          </Card>

          {result?.synthetic && (
            <Alert type="warning" message="当前显示为模拟数据" description="因网络原因未能获取真实行情数据，以下为基于历史统计特征的模拟回测结果。" showIcon style={{ marginBottom: 16 }} />
          )}

          {result?.pair && (
            <Card size="small" style={{ marginBottom: 16 }}>
              <Space>
                <SwapOutlined style={{ color: '#1677ff' }} />
                <Text>配对: <Text strong>{result.pair[0]}</Text> 与 <Text strong>{result.pair[1]}</Text></Text>
                <Tag color="blue">相关系数: {result.correlation}</Tag>
              </Space>
            </Card>
          )}

          {/* 优化结果 */}
          {optResults.length > 0 && (
            <Card title="🏆 参数优化结果" size="small" style={{ marginBottom: 16 }}>
              <Table
                columns={optColumns}
                dataSource={optResults.map((r, i) => ({ ...r, key: i }))}
                pagination={{ pageSize: 5 }}
                size="small"
              />
            </Card>
          )}

          {/* 结果 */}
          {result && (
            <Tabs activeKey={activeTab} onChange={setActiveTab} items={[
              {
                key: 'equity', label: '净值曲线',
                children: (
                  <>
                    <Card style={{ marginBottom: 16 }}>
                      {chartOption ? <ReactECharts option={chartOption} style={{ height: 350 }} /> : <Spin />}
                    </Card>
                    {drawdownOption && (
                      <Card title="📉 回撤曲线" size="small" style={{ marginBottom: 16 }}>
                        <ReactECharts option={drawdownOption} style={{ height: 180 }} />
                      </Card>
                    )}
                  </>
                ),
              },
              {
                key: 'metrics', label: '绩效指标',
                children: (
                  <>
                    <Card style={{ marginBottom: 16 }}>
                      <Row gutter={[16, 16]}>
                        <Col span={6}><Statistic title="总收益" value={result.total_return} suffix="%" valueStyle={{ color: result.total_return > 0 ? '#3f8600' : '#cf1322', fontSize: 20 }} /></Col>
                        <Col span={6}><Statistic title="年化收益" value={result.annual_return} suffix="%" valueStyle={{ color: result.annual_return > 0 ? '#3f8600' : '#cf1322', fontSize: 20 }} /></Col>
                        <Col span={6}><Statistic title="最大回撤" value={result.max_drawdown} suffix="%" valueStyle={{ color: '#cf1322', fontSize: 20 }} /></Col>
                        <Col span={6}><Statistic title="年化波动率" value={result.volatility} suffix="%" valueStyle={{ fontSize: 20 }} /></Col>
                      </Row>
                      <Divider style={{ margin: '12px 0' }} />
                      <Row gutter={[16, 16]}>
                        <Col span={6}><Statistic title="Sharpe比率" value={result.sharpe_ratio} valueStyle={{ color: result.sharpe_ratio > 1 ? '#3f8600' : '#faad14', fontSize: 18 }} /></Col>
                        <Col span={6}><Statistic title="Sortino比率" value={result.sortino_ratio} valueStyle={{ fontSize: 18 }} /></Col>
                        <Col span={6}><Statistic title="Calmar比率" value={result.calmar_ratio} valueStyle={{ fontSize: 18 }} /></Col>
                        <Col span={6}><Statistic title="收益回撤比" value={result.total_return && result.max_drawdown ? (Math.abs(result.total_return / result.max_drawdown)).toFixed(2) : '-'} valueStyle={{ fontSize: 18 }} /></Col>
                      </Row>
                    </Card>
                    <Card title="📈 详细统计" size="small" style={{ marginBottom: 16 }}>
                      <Row gutter={[16, 12]}>
                        <Col span={8}><Text type="secondary">胜率</Text><br /><Text strong style={{ fontSize: 16 }}>{result.win_rate}%</Text></Col>
                        <Col span={8}><Text type="secondary">盈亏比</Text><br /><Text strong style={{ fontSize: 16 }}>{result.profit_loss_ratio}</Text></Col>
                        <Col span={8}><Text type="secondary">总交易次数</Text><br /><Text strong style={{ fontSize: 16 }}>{result.total_trades || result.trade_count}</Text></Col>
                        <Col span={8}><Text type="secondary">最大回撤持续天数</Text><br /><Text strong style={{ fontSize: 16 }}>{result.max_drawdown_duration || result.max_drawdown_days}</Text></Col>
                        <Col span={8}><Text type="secondary">最佳月份</Text><br /><Text strong style={{ fontSize: 16, color: result.best_month > 0 ? '#3f8600' : undefined }}>{result.best_month > 0 ? '+' : ''}{result.best_month}%</Text></Col>
                        <Col span={8}><Text type="secondary">最差月份</Text><br /><Text strong style={{ fontSize: 16, color: '#cf1322' }}>{result.worst_month}%</Text></Col>
                        <Col span={8}><Text type="secondary">盈利天数</Text><br /><Text strong style={{ fontSize: 16 }}>{result.profit_days || '-'}</Text></Col>
                        <Col span={8}><Text type="secondary">亏损天数</Text><br /><Text strong style={{ fontSize: 16 }}>{result.loss_days || '-'}</Text></Col>
                        <Col span={8}><Text type="secondary">总手续费</Text><br /><Text strong style={{ fontSize: 16 }}>{result.total_commission || '-'}</Text></Col>
                      </Row>
                    </Card>
                  </>
                ),
              },
              {
                key: 'trades', label: '交易日志',
                children: (
                  <Card>
                    <Table
                      columns={tradeColumns}
                      dataSource={(result.trades || []).map((t: any, i: number) => ({ ...t, key: i }))}
                      pagination={{ pageSize: 20 }}
                      size="small"
                      scroll={{ y: 400 }}
                    />
                  </Card>
                ),
              },
            ]} />
          )}
        </Col>
      </Row>
    </div>
  )
}
