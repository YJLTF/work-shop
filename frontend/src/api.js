/** 后端 API 的极薄封装，统一错误信息提取。 */

let connectionLostHandler = null

/** 注册"与服务器的连接断开"回调（服务退出或无响应时触发）。 */
export function onConnectionLost(handler) {
  connectionLostHandler = handler
}

/** 供任意模块主动上报连接断开（如组件动态加载失败）。 */
export function notifyConnectionLost() {
  if (connectionLostHandler) connectionLostHandler()
}

async function parseError(res) {
  let detail = res.statusText || `请求失败 (${res.status})`
  try {
    const body = await res.json()
    const d = body.detail
    if (typeof d === 'string') detail = d
    else if (Array.isArray(d)) detail = d.map((item) => item.msg || JSON.stringify(item)).join('；')
    else if (d) detail = JSON.stringify(d)
  } catch {
    /* 保留默认信息 */
  }
  return new Error(detail)
}

async function request(path, options) {
  let res
  try {
    res = await fetch(`/api${path}`, options)
  } catch (err) {
    // 网络层失败：本地服务大概率已退出
    if (connectionLostHandler) connectionLostHandler()
    throw err
  }
  if (!res.ok) throw await parseError(res)
  return res.json()
}

function jsonOptions(method, data) {
  return {
    method,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  }
}

export const api = {
  get: (path) => request(path),
  post: (path, data) => request(path, jsonOptions('POST', data)),
  postForm: (path, formData) => request(path, { method: 'POST', body: formData }),
}
