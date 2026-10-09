const getToken = () => localStorage.getItem('cloudconnect_token')
async function request(path, options = {}) {
  const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) }
  const token = getToken()
  if (token) headers.Authorization = `Bearer ${token}`
  const res = await fetch(path, { ...options, headers })
  const data = await res.json().catch(() => ({}))
  if (!res.ok) throw new Error(data.detail || 'Request failed')
  return data
}
export const api = {
  register: (payload) => request('/api/auth/register', { method: 'POST', body: JSON.stringify(payload) }),
  login: (payload) => request('/api/auth/login', { method: 'POST', body: JSON.stringify(payload) }),
  updateProfile: (payload) => request('/api/user/profile', { method: 'PUT', body: JSON.stringify(payload) }),
  posts: () => request('/api/post/posts'),
  createPost: (payload) => request('/api/post/posts', { method: 'POST', body: JSON.stringify(payload) }),
  postJob: (jobId) => request(`/api/post/posts/jobs/${jobId}`),
  deletePost: (id) => request(`/api/post/posts/${id}`, { method: 'DELETE' }),
  togglePostLike: (id) => request(`/api/like/posts/${id}/toggle`, { method: 'POST' }),
  comments: (postId) => request(`/api/comment/posts/${postId}/comments`),
  createComment: (postId, payload) => request(`/api/comment/posts/${postId}/comments`, { method: 'POST', body: JSON.stringify(payload) }),
  toggleCommentLike: (commentId) => request(`/api/comment/comments/${commentId}/like/toggle`, { method: 'POST' }),
  analyticsMetrics: () => request('/api/analytics/metrics'),
  trackImpressions: (postIds) => request('/api/analytics/impressions', { method: 'POST', body: JSON.stringify({ post_ids: postIds, source: 'feed' }) }),
}
