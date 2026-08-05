import { useState, useEffect, useRef } from 'react'
import { Input, Button, Typography, Upload, Space, Spin } from 'antd'
import { SendOutlined, PaperClipOutlined, RobotOutlined, UserOutlined } from '@ant-design/icons'
import ReactMarkdown from 'react-markdown'
import { chatSend, createSession } from '../api'

const { Text } = Typography
const { TextArea } = Input

export default function Chat() {
  const [sessionId, setSessionId] = useState('')
  const [messages, setMessages] = useState<{ role: string; content: string }[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    createSession()
      .then((res) => setSessionId(res.data.session_id))
      .catch(() => {})
  }, [])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = async () => {
    if (!input.trim() || !sessionId) return

    const userMsg = input.trim()
    setInput('')
    setMessages((prev) => [...prev, { role: 'user', content: userMsg }])
    setLoading(true)

    try {
      const res = await chatSend(sessionId, userMsg)
      setMessages((prev) => [...prev, { role: 'assistant', content: res.data.response }])
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: '抱歉，服务暂时不可用，请稍后重试。' },
      ])
    }
    setLoading(false)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const quickQuestions = [
    '帮我分析一下贵州茅台的杜邦分析',
    '如何设计一个动量因子回测策略？',
    '面板数据固定效应和随机效应怎么选？',
    '当前宏观经济形势怎么样？',
  ]

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 160px)' }}>
      <div className="chat-container" style={{ flex: 1 }}>
        {/* 消息区域 */}
        <div className="chat-messages">
          {messages.length === 0 && (
            <div style={{ textAlign: 'center', padding: '60px 20px' }}>
              <RobotOutlined style={{ fontSize: 64, color: '#1677ff', marginBottom: 16 }} />
              <div style={{ fontSize: 20, fontWeight: 600, marginBottom: 8 }}>
                你好，我是金融学院AI助手
              </div>
              <div style={{ color: '#8c8c8c', marginBottom: 24 }}>
                我可以帮你做实证分析、量化回测、财报解析、论文检索等
              </div>
              <Space wrap style={{ justifyContent: 'center' }}>
                {quickQuestions.map((q, i) => (
                  <Button
                    key={i}
                    onClick={() => setInput(q)}
                    style={{ borderRadius: 20 }}
                  >
                    {q}
                  </Button>
                ))}
              </Space>
            </div>
          )}

          {messages.map((msg, i) => (
            <div key={i} className={`chat-message ${msg.role}`}>
              <div
                style={{
                  width: 36,
                  height: 36,
                  borderRadius: '50%',
                  background: msg.role === 'user' ? '#1677ff' : '#f0f0f0',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  flexShrink: 0,
                }}
              >
                {msg.role === 'user' ? (
                  <UserOutlined style={{ color: '#fff' }} />
                ) : (
                  <RobotOutlined style={{ color: '#666' }} />
                )}
              </div>
              <div className={`chat-bubble ${msg.role}`}>
                {msg.role === 'assistant' ? (
                  <div className="markdown-content">
                    <ReactMarkdown>{msg.content}</ReactMarkdown>
                  </div>
                ) : (
                  msg.content
                )}
              </div>
            </div>
          ))}

          {loading && (
            <div className="chat-message assistant">
              <div
                style={{
                  width: 36,
                  height: 36,
                  borderRadius: '50%',
                  background: '#f0f0f0',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <RobotOutlined style={{ color: '#666' }} />
              </div>
              <div className="chat-bubble assistant">
                <Spin size="small" /> 思考中...
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* 输入区域 */}
        <div className="chat-input">
          <Upload showUploadList={false}>
            <Button icon={<PaperClipOutlined />} />
          </Upload>
          <TextArea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="问点什么... (Enter发送，Shift+Enter换行)"
            autoSize={{ minRows: 1, maxRows: 4 }}
            style={{ flex: 1 }}
          />
          <Button
            type="primary"
            icon={<SendOutlined />}
            onClick={handleSend}
            loading={loading}
          >
            发送
          </Button>
        </div>
      </div>
    </div>
  )
}
