import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 60000,
})

// Chat
export const chatSend = (session_id: string, message: string) =>
  api.post('/chat/send', { session_id, message })

export const chatHistory = (session_id: string) =>
  api.get(`/chat/history/${session_id}`)

export const createSession = () => api.post('/chat/session')

// Empirical
export const runEmpirical = (data: any) => api.post('/empirical/run', data)
export const exportLatex = (data: any) => api.post('/empirical/export-latex', data)
export const listProjects = () => api.get('/empirical/projects')
export const autoDetectVariables = (projectName: string) =>
  api.post(`/empirical/auto-detect?project_name=${encodeURIComponent(projectName)}`)
export const fetchResearchData = (data: any) => api.post('/empirical/fetch-data', null, { params: data })
export const searchStockData = (stockCode: string) =>
  api.post(`/empirical/search-stock?stock_code=${encodeURIComponent(stockCode)}`)
export const searchVariableData = (variableName: string) =>
  api.post(`/empirical/search-variable?variable_name=${encodeURIComponent(variableName)}`)
export const uploadResearchData = (file: File) => {
  const formData = new FormData()
  formData.append('file', file)
  return api.post('/empirical/upload-data', formData, { timeout: 120000 })
}

// Research Guide
export const getResearchDesign = (data: any) => api.post('/empirical/research-design', null, { params: data })
export const getEmpiricalGuide = (data: any) => api.post('/empirical/empirical-guide', null, { params: data })
export const getPaperSection = (data: any) => api.post('/empirical/paper-section', null, { params: data })

// Quant
export const runBacktest = (data: any) => api.post('/quant/backtest', data)
export const listStrategies = () => api.get('/quant/strategies')
export const listVnpyStrategies = () => api.get('/quant/strategies/vnpy')
export const optimizeStrategy = (data: any) => api.post('/quant/optimize', data)
export const backtestHistory = () => api.get('/quant/history')

// Report
export const uploadReport = (file: File) => {
  const formData = new FormData()
  formData.append('file', file)
  return api.post('/report/upload', formData)
}
export const analyzeReport = (report_id: number, dimensions: string[]) =>
  api.post('/report/analyze', { report_id, dimensions })
export const listReports = () => api.get('/report/list')

// Paper
export const searchPapers = (data: any) => api.post('/paper/search', data)
export const searchPapersAdvanced = (data: any) => api.post('/paper/search-advanced', data)
export const listFavorites = () => api.get('/paper/favorites')
export const addFavorite = (paper: any) => api.post('/paper/favorite', paper)
export const removeFavorite = (id: number) => api.delete(`/paper/favorite/${id}`)

// Macro
export const macroOverview = () => api.get('/macro/overview')
export const macroChart = (indicator: string) => api.get(`/macro/chart/${indicator}`)
export const listIndicators = () => api.get('/macro/indicators')
export const macroCrawler = (indicator: string) => api.get(`/macro/crawler/${indicator}`)
export const macroCrawlerAll = () => api.get('/macro/crawler/all')
