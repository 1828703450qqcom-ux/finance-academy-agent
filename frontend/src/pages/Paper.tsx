import { useState } from 'react'
import { Row, Col, Card, Button, Input, Typography, Tag, Space, List, Checkbox, DatePicker, Spin, message, Divider } from 'antd'
import { SearchOutlined, StarOutlined, StarFilled, LinkOutlined, FileTextOutlined } from '@ant-design/icons'
import { searchPapersAdvanced, addFavorite, removeFavorite, listFavorites } from '../api'

const { Title, Text, Paragraph } = Typography
const { RangePicker } = DatePicker

export default function Paper() {
  const [query, setQuery] = useState('')
  const [sources, setSources] = useState<string[]>(['openalex', 'arxiv', 'semantic_scholar'])
  const [yearRange, setYearRange] = useState<[number, number]>([2020, 2025])
  const [results, setResults] = useState<any[]>([])
  const [favorites, setFavorites] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [showFavs, setShowFavs] = useState(false)

  const handleSearch = async () => {
    if (!query.trim()) {
      message.warning('请输入搜索关键词')
      return
    }
    setLoading(true)
    try {
      const res = await searchPapersAdvanced({
        query,
        sources,
        year_from: yearRange[0],
        year_to: yearRange[1],
      })
      setResults(res.data.results || [])
    } catch {
      message.error('搜索失败')
    }
    setLoading(false)
  }

  const handleFavorite = async (paper: any) => {
    try {
      await addFavorite(paper)
      message.success('收藏成功')
      loadFavorites()
    } catch {
      message.error('收藏失败')
    }
  }

  const handleRemoveFav = async (id: number) => {
    try {
      await removeFavorite(id)
      message.success('已取消收藏')
      loadFavorites()
    } catch {}
  }

  const loadFavorites = async () => {
    try {
      const res = await listFavorites()
      setFavorites(res.data.favorites || [])
    } catch {}
  }

  const isFavorited = (title: string) => favorites.some((f) => f.title === title)

  return (
    <div>
      <div className="page-header">
        <Title level={3}>📚 学术论文检索</Title>
        <Text type="secondary">支持OpenAlex、arXiv、Semantic Scholar、CNKI、NBER、SSRN等数据源</Text>
      </div>

      <Row gutter={24}>
        {/* 左侧 */}
        <Col xs={24} lg={6}>
          <Card title="📂 检索历史" size="small" style={{ marginBottom: 16 }}>
            <Space direction="vertical" style={{ width: '100%' }}>
              {['资产定价', 'ESG', '动量因子', '机器学习'].map((h) => (
                <div
                  key={h}
                  onClick={() => { setQuery(h); handleSearch() }}
                  style={{ padding: '6px 0', cursor: 'pointer', fontSize: 13, borderBottom: '1px solid #f0f0f0' }}
                >
                  {h}
                </div>
              ))}
            </Space>
          </Card>

          <Card
            title="⭐ 收藏夹"
            size="small"
            extra={
              <a onClick={() => { setShowFavs(!showFavs); loadFavorites() }}>
                {showFavs ? '返回' : `(${favorites.length})`}
              </a>
            }
          >
            {favorites.map((f) => (
              <div key={f.id} style={{ padding: '6px 0', borderBottom: '1px solid #f0f0f0' }}>
                <Text style={{ fontSize: 12 }} ellipsis>{f.title}</Text>
                <Button type="link" size="small" onClick={() => handleRemoveFav(f.id)}>取消</Button>
              </div>
            ))}
            {favorites.length === 0 && <Text type="secondary" style={{ fontSize: 12 }}>暂无收藏</Text>}
          </Card>
        </Col>

        {/* 右侧 */}
        <Col xs={24} lg={18}>
          {/* 搜索栏 */}
          <Card style={{ marginBottom: 16 }}>
            <Space.Compact style={{ width: '100%' }}>
              <Input
                prefix={<SearchOutlined />}
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onPressEnter={handleSearch}
                placeholder="搜索论文关键词，如：机器学习 资产定价"
                size="large"
              />
              <Button type="primary" onClick={handleSearch} loading={loading} size="large">
                搜索
              </Button>
            </Space.Compact>

            <div style={{ marginTop: 12, display: 'flex', gap: 16, alignItems: 'center', flexWrap: 'wrap' }}>
              <span>数据源:</span>
              <Checkbox.Group
                value={sources}
                onChange={(v) => setSources(v as string[])}
                options={[
                  { label: 'OpenAlex', value: 'openalex' },
                  { label: 'arXiv', value: 'arxiv' },
                  { label: 'Semantic Scholar', value: 'semantic_scholar' },
                  { label: 'CNKI知网', value: 'cnki' },
                  { label: 'NBER', value: 'nber' },
                  { label: 'SSRN', value: 'ssrn' },
                ]}
              />
              <span>年份:</span>
              <Space>
                <Input
                  size="small"
                  value={yearRange[0]}
                  onChange={(e) => setYearRange([parseInt(e.target.value) || 2020, yearRange[1]])}
                  style={{ width: 70 }}
                />
                ~
                <Input
                  size="small"
                  value={yearRange[1]}
                  onChange={(e) => setYearRange([yearRange[0], parseInt(e.target.value) || 2025])}
                  style={{ width: 70 }}
                />
              </Space>
            </div>
          </Card>

          {/* 搜索结果 */}
          {loading ? (
            <div style={{ textAlign: 'center', padding: 40 }}><Spin size="large" /></div>
          ) : (
            <>
              {results.length > 0 && (
                <Text type="secondary" style={{ marginBottom: 12, display: 'block' }}>
                  找到 {results.length} 篇相关论文
                </Text>
              )}
              <List
                dataSource={results}
                renderItem={(item: any, index: number) => (
                  <Card size="small" style={{ marginBottom: 8 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <div style={{ flex: 1 }}>
                        <Text strong style={{ fontSize: 15 }}>{item.title}</Text>
                        <br />
                        <Text type="secondary" style={{ fontSize: 13 }}>
                          {item.authors} ({item.year})
                        </Text>
                        <br />
                        <Space style={{ marginTop: 4 }}>
                          <Tag color="blue">{item.source}</Tag>
                          {item.citation_count > 0 && (
                            <Tag color="orange">被引: {item.citation_count}</Tag>
                          )}
                        </Space>
                        {item.abstract && (
                          <Paragraph
                            type="secondary"
                            ellipsis={{ rows: 2, expandable: true }}
                            style={{ fontSize: 12, marginTop: 8 }}
                          >
                            {typeof item.abstract === 'string' ? item.abstract : JSON.stringify(item.abstract)}
                          </Paragraph>
                        )}
                      </div>
                      <Space direction="vertical">
                        <Button
                          type="text"
                          icon={isFavorited(item.title) ? <StarFilled style={{ color: '#faad14' }} /> : <StarOutlined />}
                          onClick={() => handleFavorite(item)}
                        />
                        {item.url && (
                          <Button type="text" icon={<LinkOutlined />} href={item.url} target="_blank" />
                        )}
                      </Space>
                    </div>
                  </Card>
                )}
              />
              {results.length === 0 && !loading && (
                <div style={{ textAlign: 'center', padding: 60, color: '#ccc' }}>
                  <FileTextOutlined style={{ fontSize: 48 }} />
                  <p>输入关键词搜索学术论文</p>
                </div>
              )}
            </>
          )}
        </Col>
      </Row>
    </div>
  )
}
