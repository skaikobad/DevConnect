import React, { useEffect, useState } from 'react'
import { createRoot } from 'react-dom/client'
import {
  ArrowDown,
  ArrowRight,
  BarChart3,
  CheckCircle2,
  Cloud,
  Container,
  Database,
  Eye,
  GitBranch,
  Heart,
  KeyRound,
  Layers3,
  LockKeyhole,
  LogOut,
  Loader2,
  MessageCircle,
  Network,
  Route,
  Scale,
  Shield,
  Sparkles,
  TrendingUp,
  Trash2,
  UserRound,
} from 'lucide-react'
import { api } from './api'
import './styles.css'

function App() {
  const [token, setToken] = useState(localStorage.getItem('cloudconnect_token'))
  const [user, setUser] = useState(JSON.parse(localStorage.getItem('cloudconnect_user') || 'null'))
  const [mode, setMode] = useState('login')
  const [page, setPage] = useState('home')
  const [error, setError] = useState('')

  function saveSession(data) {
    localStorage.setItem('cloudconnect_token', data.token)
    localStorage.setItem('cloudconnect_user', JSON.stringify(data.user))
    setToken(data.token)
    setUser(data.user)
    setError('')
    setPage('home')
  }

  function logout() {
    localStorage.removeItem('cloudconnect_token')
    localStorage.removeItem('cloudconnect_user')
    setToken(null)
    setUser(null)
    setPage('home')
  }

  return (
    <div className="app-shell">
      <BackgroundGrid />
      <Navbar user={user} logout={logout} page={page} setPage={setPage} setMode={setMode} />
      {page === 'architecture' && <ArchitecturePage />}
      {page === 'services' && <ServicesPage />}
      {page === 'security' && <SecurityPage />}
      {page === 'analytics' && <AnalyticsPage />}
      {page === 'home' && (!token ? (
        <Landing mode={mode} setMode={setMode} saveSession={saveSession} error={error} setError={setError} setPage={setPage} />
      ) : (
        <Dashboard user={user} setUser={setUser} />
      ))}
    </div>
  )
}

function BackgroundGrid() {
  return <><div className="orb orb-one" /><div className="orb orb-two" /><div className="grid-bg" /></>
}

function Navbar({ user, logout, page, setPage, setMode }) {
  const goHome = () => setPage('home')
  return (
    <nav className="nav">
      <button className="brand brand-button" onClick={goHome} aria-label="Go to home page">
        <span className="logo-mark">◆◆</span><span>DevConnect</span>
      </button>
      <div className="nav-links">
        <button className={page === 'home' ? 'active' : ''} onClick={goHome}>Home</button>
        <button className={page === 'architecture' ? 'active' : ''} onClick={() => setPage('architecture')}>Architecture</button>
        <button className={page === 'services' ? 'active' : ''} onClick={() => setPage('services')}>Services</button>
        <button className={page === 'security' ? 'active' : ''} onClick={() => setPage('security')}>Security</button>
        <button className={page === 'analytics' ? 'active' : ''} onClick={() => setPage('analytics')}>Analytics</button>
      </div>
      <div className="nav-actions">
        {user ? (
          <>
            <span className="hello">Hi, {user.name}</span>
            <button className="outline small" onClick={logout}><LogOut size={15} /> Logout</button>
          </>
        ) : (
          <button className="primary small" onClick={() => { setPage('home'); setMode('register') }}>Get Started <ArrowRight size={15} /></button>
        )}
      </div>
    </nav>
  )
}

function Landing({ mode, setMode, saveSession, error, setError, setPage }) {
  return (
    <main className="landing">
      <section className="hero">
        <div className="pill"><Sparkles size={14} /> ECS Fargate Microservices Project</div>
        <h1>A Developer Social App for Learning Cloud Native DevOps</h1>
        <p>Build a professional developer social platform with React, FastAPI microservices, PostgreSQL, Redis Queue, Docker, Kubernetes, GitOps, and observability-ready architecture.</p>
        <div className="hero-actions">
          <button className="primary" onClick={() => setMode('register')}>Create Account <ArrowRight size={16} /></button>
          <button className="outline" onClick={() => setMode('login')}>Sign In</button>
          <button className="outline" onClick={() => setPage('architecture')}>View Architecture</button>
        </div>
      </section>
      <section className="console-card">
        <div className="console-top"><span></span><span></span><span></span><p>local.cloudconnect.dev</p></div>
        <div className="console-body">
          <aside><b>DevConnect</b><a>Overview</a><a>Auth API</a><a>Posts</a><a>Comments</a><a>Likes</a></aside>
          <div className="console-main">
            <div className="welcome">Welcome back, DevOps Engineer</div>
            <div className="metric"><span>Running services</span><strong>10</strong><small>Frontend + 6 FastAPI + Worker + Redis + PostgreSQL</small></div>
            <div className="chart"><span style={{ height: '36%' }}></span><span style={{ height: '46%' }}></span><span style={{ height: '30%' }}></span><span style={{ height: '68%' }}></span><span style={{ height: '78%' }}></span><span style={{ height: '88%' }}></span></div>
          </div>
          <AuthCard mode={mode} setMode={setMode} saveSession={saveSession} error={error} setError={setError} />
        </div>
      </section>
      <section className="feature-panel">
        <div className="pill subtle">Features</div>
        <h2>A Real Social App Wrapped in a DevOps Deployment Platform</h2>
        <div className="cards">
          <Feature icon={<Container />} title="Containerized Services" text="Frontend, Auth, User, Post, Like, and Comment services run as isolated containers." />
          <Feature icon={<Network />} title="ALB-Ready Routing" text="Local Nginx path routing mirrors the future AWS Application Load Balancer design." />
          <Feature icon={<Database />} title="PostgreSQL Database" text="Shared local PostgreSQL prepares students for Amazon RDS PostgreSQL." />
          <Feature icon={<Shield />} title="JWT Security" text="Protected APIs use bearer tokens, just like real backend services." />
          <Feature icon={<BarChart3 />} title="Analytics Service" text="A separate FastAPI service reads PostgreSQL data and shows users, posts, impressions, and engagement metrics." />
        </div>
      </section>
    </main>
  )
}

function Feature({ icon, title, text }) {
  return <div className="feature-card"><div className="feature-icon">{icon}</div><h3>{title}</h3><p>{text}</p></div>
}

function AuthCard({ mode, setMode, saveSession, error, setError }) {
  const [form, setForm] = useState({ name: '', email: '', password: '' })
  async function submit(e) {
    e.preventDefault(); setError('')
    try {
      const data = mode === 'register' ? await api.register(form) : await api.login({ email: form.email, password: form.password })
      saveSession(data)
    } catch (err) { setError(err.message) }
  }
  return <form className="auth-card" onSubmit={submit}><h3>{mode === 'register' ? 'Create account' : 'Welcome back'}</h3>{mode === 'register' && <input placeholder="Full name" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} />}<input placeholder="Email" type="email" value={form.email} onChange={e => setForm({ ...form, email: e.target.value })} /><input placeholder="Password" type="password" value={form.password} onChange={e => setForm({ ...form, password: e.target.value })} />{error && <div className="error">{error}</div>}<button className="primary full">{mode === 'register' ? 'Sign up' : 'Sign in'} <ArrowRight size={15} /></button><p className="switch">{mode === 'register' ? 'Already have an account?' : 'New here?'} <button type="button" onClick={() => setMode(mode === 'register' ? 'login' : 'register')}>{mode === 'register' ? 'Sign in' : 'Create account'}</button></p></form>
}

function ArchitecturePage() {
  return (
    <main className="info-page">
      <section className="page-hero">
        <div className="pill"><Network size={14} /> Professional Social Platform Architecture</div>
        <h1>DevConnect Production Architecture</h1>
        <p>DevConnect is designed as a developer social platform: users create profiles, publish posts with optional public images, comment, like content, and view analytics. Locally it runs with Docker Compose and Nginx. In production it maps to Kubernetes on EC2, ArgoCD GitOps, DockerHub images, PostgreSQL, Redis Queue, and a full Prometheus/Grafana/Loki monitoring stack.</p>
      </section>

      <section className="architecture-board">
        <div className="diagram-title">
          <div><span className="kicker">End-to-end flow</span><h2>Developer → GitHub Actions → DockerHub → ArgoCD → Kubernetes → DevConnect</h2></div>
          <div className="diagram-badge">Docker Compose locally • Kubernetes on EC2</div>
        </div>
        <div className="architecture-diagram">
          <DiagramNode icon={<GitBranch />} label="CI/CD Pipeline" text="Pull requests run tests, Trivy, OWASP Dependency-Check, and SonarQube. Main branch builds images and pushes them to DockerHub." />
          <DiagramArrow />
          <DiagramNode icon={<Container />} label="DockerHub Images" text="Each app service is published as a separate container image under bongodev/* and referenced by Kubernetes manifests." />
          <DiagramArrow />
          <DiagramNode icon={<Route />} label="ArgoCD GitOps" text="ArgoCD watches the Kubernetes manifests in Git and syncs the desired state into the k3s cluster running on EC2." highlight />
          <DiagramArrow />
          <div className="vpc-box">
            <div className="vpc-label"><Cloud size={16} /> Runtime Platform</div>
            <div className="subnet-row">
              <div className="subnet public-subnet"><b>Entry Layer</b><span>Browser traffic enters through Nginx locally, and through Ingress or ALB-style routing in Kubernetes.</span></div>
              <div className="subnet private-subnet"><b>Social App Services</b><span>Auth, User, Post, Like, Comment, Analytics, and Worker run as isolated containers.</span></div>
              <div className="subnet private-subnet"><b>Data and Async Layer</b><span>PostgreSQL stores durable data. Redis powers post-creation queueing, worker processing, and operational metrics.</span></div>
            </div>
            <div className="service-map">
              <ServicePill path="/" name="React Social UI + Nginx" />
              <ServicePill path="/api/auth/*" name="Auth: register, login, JWT" />
              <ServicePill path="/api/user/*" name="Profiles and developer bios" />
              <ServicePill path="/api/post/*" name="Queued post creation + image URLs" />
              <ServicePill path="worker" name="Worker consumes Redis jobs" />
              <ServicePill path="redis" name="Redis Queue + counters" />
              <ServicePill path="/api/like/*" name="Post likes" />
              <ServicePill path="/api/comment/*" name="Comments + comment likes" />
              <ServicePill path="/api/analytics/*" name="Social analytics and impressions" />
            </div>
          </div>
          <DiagramArrow />
          <DiagramNode icon={<BarChart3 />} label="Observability Layer" text="Prometheus collects metrics, Grafana visualizes dashboards, Loki stores logs, Grafana Alloy ships logs, and node-exporter/cAdvisor expose host and container metrics." />
        </div>
      </section>

      <section className="info-grid three">
        <InfoCard icon={<MessageCircle />} title="Real social workflow" text="Users publish posts, attach optional public images, comment, like content, and generate impressions that flow into the analytics service." />
        <InfoCard icon={<Database />} title="Async post pipeline" text="Post requests are accepted quickly, stored as jobs, queued in Redis, and completed by a Worker Service before appearing in the feed." />
        <InfoCard icon={<Shield />} title="Production deployment mindset" text="The project connects application design with CI/CD, image scanning, GitOps, Kubernetes rollouts, logs, metrics, and secure runtime configuration." />
      </section>
    </main>
  )
}

function DiagramNode({ icon, label, text, highlight }) {
  return <div className={highlight ? 'diagram-node highlight' : 'diagram-node'}><div className="diagram-icon">{icon}</div><b>{label}</b><span>{text}</span></div>
}
function DiagramArrow() { return <div className="diagram-arrow"><ArrowDown size={22} /></div> }
function ServicePill({ path, name }) { return <div className="service-pill"><code>{path}</code><span>{name}</span></div> }

function ServicesPage() {
  const services = [
    { icon: <Container />, title: 'Frontend Social UI', cloud: 'React + Nginx / Kubernetes Service', details: 'Delivers the DevConnect social experience: landing page, feed, profile card, posts with public images, comments, likes, and analytics navigation. Nginx also acts as the local reverse proxy for API routes.' },
    { icon: <KeyRound />, title: 'Auth Service', cloud: 'FastAPI + JWT + password hashing', details: 'Handles registration, login, JWT generation, and protected API access. In production, JWT secrets and database credentials should be provided through Kubernetes Secrets or AWS Secrets Manager.' },
    { icon: <UserRound />, title: 'User Service', cloud: 'FastAPI profile service', details: 'Owns developer profile data such as name, email, role, and bio. This turns the app from a demo feed into a developer-networking experience.' },
    { icon: <MessageCircle />, title: 'Post Service', cloud: 'FastAPI + Redis Queue producer', details: 'Accepts post creation requests, validates optional public image URLs, creates post jobs, and pushes work into Redis so multiple post requests can be handled asynchronously.' },
    { icon: <Container />, title: 'Worker Service', cloud: 'Background processor', details: 'Consumes Redis post-creation jobs, inserts completed posts into PostgreSQL, updates job status, and records worker/queue processing counters for analytics.' },
    { icon: <Database />, title: 'Redis Service', cloud: 'Redis locally / ElastiCache or Redis on Kubernetes', details: 'Provides the queue backend for post creation and stores lightweight operational counters such as queue depth and processed-job totals.' },
    { icon: <Heart />, title: 'Like Service', cloud: 'FastAPI engagement service', details: 'Handles post likes and unlikes so engagement behavior is isolated from the post service and can scale independently.' },
    { icon: <MessageCircle />, title: 'Comment Service', cloud: 'FastAPI conversation service', details: 'Stores comments, supports optional public image URLs in comments, and includes comment likes to make the feed feel like a real social application.' },
    { icon: <BarChart3 />, title: 'Analytics Service', cloud: 'FastAPI + PostgreSQL + Redis metrics', details: 'Builds the social analytics view: users, posts, comments, likes, impressions, top content, queued jobs, failed jobs, and worker processing metrics.' },
    { icon: <Database />, title: 'PostgreSQL Database', cloud: 'PostgreSQL locally / RDS or Kubernetes StatefulSet', details: 'Acts as the source of truth for users, posts, jobs, likes, comments, impressions, and analytics-ready data.' },
    { icon: <GitBranch />, title: 'CI/CD Pipeline', cloud: 'GitHub Actions + DockerHub', details: 'Runs tests and quality gates, scans code and images with Trivy/OWASP/SonarQube, builds Docker images, and pushes versioned images to DockerHub.' },
    { icon: <Route />, title: 'GitOps Deployment', cloud: 'ArgoCD + Kubernetes manifests', details: 'ArgoCD continuously reconciles the cluster with the manifests in Git so deployments are traceable, repeatable, and easy for students to inspect.' },
    { icon: <TrendingUp />, title: 'Monitoring Stack', cloud: 'Prometheus + Grafana + Loki + Alloy', details: 'Collects metrics, dashboards, and logs from application pods, Kubernetes workloads, EC2 node resources, containers, and platform services.' },
  ]
  return (
    <main className="info-page">
      <section className="page-hero">
        <div className="pill"><Container size={14} /> Real Social App Service Breakdown</div>
        <h1>Services Behind DevConnect</h1>
        <p>DevConnect is a developer social network built for DevOps learning. Each service owns a focused responsibility so students can understand service boundaries, Docker images, Kubernetes workloads, GitOps deployment, and observability in one professional project.</p>
      </section>
      <section className="service-detail-grid">
        {services.map(service => <InfoCard key={service.title} icon={service.icon} title={service.title} eyebrow={service.cloud} text={service.details} />)}
      </section>
      <section className="feature-panel compact-panel">
        <div className="pill subtle">Technology stack represented in this project</div>
        <div className="cloud-list">
          <span>React</span><span>Nginx</span><span>FastAPI</span><span>JWT</span><span>PostgreSQL</span><span>Redis Queue</span><span>Worker Service</span><span>Docker</span><span>Docker Compose</span><span>DockerHub</span><span>GitHub Actions</span><span>Trivy</span><span>OWASP Dependency-Check</span><span>SonarQube</span><span>Kubernetes/k3s</span><span>ArgoCD</span><span>Prometheus</span><span>Grafana</span><span>Loki</span><span>Grafana Alloy</span><span>node-exporter</span><span>cAdvisor</span>
        </div>
      </section>
    </main>
  )
}

function SecurityPage() {
  return (
    <main className="info-page">
      <section className="page-hero">
        <div className="pill"><Shield size={14} /> Professional Security and Delivery Controls</div>
        <h1>Security Model for DevConnect</h1>
        <p>DevConnect teaches security across the full delivery lifecycle: secure code checks before merge, container image scanning before publish, GitOps-controlled deployment, runtime authentication, private data services, and monitoring-driven incident visibility.</p>
      </section>
      <section className="security-timeline">
        <SecurityItem icon={<GitBranch />} title="Secure CI quality gates" text="Pull requests and main-branch builds run tests, Trivy filesystem scans, OWASP Dependency-Check, and SonarQube analysis before deployment is allowed." />
        <SecurityItem icon={<Container />} title="Trusted container image flow" text="Each service is packaged as its own Docker image and pushed to DockerHub with version tags. Kubernetes pulls those images through declared manifests instead of manual server changes." />
        <SecurityItem icon={<Route />} title="GitOps deployment control" text="ArgoCD deploys the desired state from Git, giving students a clear audit trail of what changed, who changed it, and which image tag is running." />
        <SecurityItem icon={<KeyRound />} title="JWT-based API protection" text="Auth, profile, post, like, comment, analytics, and impression endpoints verify bearer tokens before returning user-specific or protected data." />
        <SecurityItem icon={<LockKeyhole />} title="Secrets and configuration separation" text="Database credentials, JWT secrets, DockerHub tokens, SonarQube tokens, and SMTP credentials should stay in GitHub Secrets, Kubernetes Secrets, or cloud secret stores — never in source code." />
        <SecurityItem icon={<Database />} title="Private data and queue services" text="PostgreSQL and Redis are internal platform services. In Kubernetes or cloud deployment, they should not be exposed publicly; only app services and workers should reach them over the cluster network." />
        <SecurityItem icon={<Shield />} title="Least-privilege network design" text="Only the frontend/ingress layer should be user-facing. Backend services, worker, Redis, and PostgreSQL should communicate internally through service DNS and tightly scoped ports." />
        <SecurityItem icon={<BarChart3 />} title="Observability for security and reliability" text="Prometheus, Grafana, Loki, Alloy, node-exporter, cAdvisor, and kube-state-metrics help detect failed pods, high resource usage, queue buildup, unusual errors, and deployment regressions." />
      </section>
    </main>
  )
}

function AnalyticsPage() {
  const [metrics, setMetrics] = useState(null)
  const [error, setError] = useState('')
  async function loadMetrics() {
    try { setMetrics(await api.analyticsMetrics()); setError('') }
    catch (e) { setError(e.message || 'Unable to load analytics') }
  }
  useEffect(() => { loadMetrics() }, [])
  const totals = metrics?.totals || {}
  const daily = metrics?.daily || []
  const maxValue = Math.max(1, ...daily.flatMap(day => [Number(day.posts || 0), Number(day.comments || 0), Number(day.impressions || 0)]))
  return (
    <main className="info-page analytics-page">
      <section className="page-hero">
        <div className="pill"><BarChart3 size={14} /> Analytics Microservice</div>
        <h1>DevConnect Analytics</h1>
        <p>This page calls a separate Analytics FastAPI service. The service reads PostgreSQL and Redis Queue data to return users, posts, comments, likes, impressions, queue depth, and worker processing metrics.</p>
        <button className="outline" onClick={loadMetrics}>Refresh Metrics</button>
      </section>
      {error && <div className="error wide">{error}. Login first, then open Analytics again.</div>}
      <section className="analytics-grid">
        <MetricCard icon={<UserRound />} label="Users" value={totals.users || 0} text="Registered accounts" />
        <MetricCard icon={<MessageCircle />} label="Posts" value={totals.posts || 0} text="Published feed items" />
        <MetricCard icon={<Eye />} label="Impressions" value={totals.impressions || 0} text="Stored feed views" />
        <MetricCard icon={<TrendingUp />} label="Engagements" value={totals.engagements || 0} text="Likes + comments" />
      </section>
      {metrics?.queue && <section className="analytics-grid queue-grid">
        <MetricCard icon={<Database />} label="Redis Queue" value={metrics.queue.queue_depth ?? 0} text={`Depth: ${metrics.queue.redis_status}`} />
        <MetricCard icon={<CheckCircle2 />} label="Worker Processed" value={metrics.queue.processed_by_worker || 0} text="Post jobs completed" />
        <MetricCard icon={<Cloud />} label="Queued Jobs" value={totals.queued_post_jobs || 0} text="Waiting in database status" />
        <MetricCard icon={<Shield />} label="Failed Jobs" value={totals.failed_post_jobs || 0} text="Should remain zero" />
      </section>}
      <section className="analytics-board">
        <div className="diagram-title"><div><span className="kicker">Last 7 days</span><h2>Database-backed activity graph</h2></div><div className="diagram-badge">PostgreSQL + Redis Queue</div></div>
        <div className="analytics-chart">
          {daily.map(day => (
            <div className="analytics-day" key={day.day}>
              <div className="bar-stack">
                <span className="bar impressions" style={{ height: `${Math.max(6, (Number(day.impressions || 0) / maxValue) * 100)}%` }} title={`Impressions: ${day.impressions}`}></span>
                <span className="bar comments" style={{ height: `${Math.max(6, (Number(day.comments || 0) / maxValue) * 100)}%` }} title={`Comments: ${day.comments}`}></span>
                <span className="bar posts" style={{ height: `${Math.max(6, (Number(day.posts || 0) / maxValue) * 100)}%` }} title={`Posts: ${day.posts}`}></span>
              </div>
              <small>{new Date(day.day).toLocaleDateString(undefined, { weekday: 'short' })}</small>
            </div>
          ))}
        </div>
        <div className="chart-legend"><span className="legend-dot posts"></span>Posts <span className="legend-dot comments"></span>Comments <span className="legend-dot impressions"></span>Impressions</div>
      </section>
      <section className="analytics-board">
        <div className="diagram-title"><div><span className="kicker">Top content</span><h2>Most visible posts</h2></div></div>
        <div className="top-posts">
          {(metrics?.top_posts || []).map(post => (
            <div className="top-post" key={post.id}>
              <div><b>{post.author_name}</b><p>{post.content}</p></div>
              <div className="top-post-stats"><span>{post.impressions} views</span><span>{post.likes} likes</span><span>{post.comments} comments</span></div>
            </div>
          ))}
          {metrics && !metrics.top_posts?.length && <div className="empty">No analytics yet. Create posts, open the feed, then refresh this page.</div>}
        </div>
      </section>
    </main>
  )
}

function MetricCard({ icon, label, value, text }) {
  return <div className="metric-card"><div className="feature-icon">{icon}</div><span>{label}</span><strong>{value}</strong><p>{text}</p></div>
}

function InfoCard({ icon, title, eyebrow, text }) {
  return <div className="info-card"><div className="feature-icon">{icon}</div>{eyebrow && <span className="eyebrow">{eyebrow}</span>}<h3>{title}</h3><p>{text}</p></div>
}
function SecurityItem({ icon, title, text }) {
  return <div className="security-item"><div className="security-icon">{icon}</div><div><h3>{title}</h3><p>{text}</p></div></div>
}

function Dashboard({ user, setUser }) {
  const [posts, setPosts] = useState([])
  const [content, setContent] = useState('')
  const [imageUrl, setImageUrl] = useState('')
  const [bio, setBio] = useState(user.bio || '')
  const [error, setError] = useState('')
  const [creatingPost, setCreatingPost] = useState(false)
  const [postJob, setPostJob] = useState(null)
  async function load() {
    try {
      const data = await api.posts()
      setPosts(data)
      if (data.length) api.trackImpressions(data.map(p => p.id)).catch(() => {})
    } catch (e) { setError(e.message) }
  }
  useEffect(() => { load() }, [])
  const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms))
  async function waitForPostJob(jobId) {
    let latest = null
    for (let attempt = 0; attempt < 6; attempt += 1) {
      latest = await api.postJob(jobId)
      setPostJob(latest)
      if (['completed', 'failed'].includes(latest.status)) return latest
      await sleep(700)
    }
    return latest
  }
  async function createPost(e) {
    e.preventDefault()
    if (!content.trim() || creatingPost) return
    setError('')
    setCreatingPost(true)
    setPostJob({ status: 'queued' })
    const startedAt = Date.now()
    try {
      const accepted = await api.createPost({ content, image_url: imageUrl.trim() || null })
      setPostJob(accepted)
      const remaining = Math.max(2000 - (Date.now() - startedAt), 0)
      await sleep(remaining)
      if (accepted.job_id) {
        const finalJob = await waitForPostJob(accepted.job_id)
        if (finalJob?.status === 'failed') throw new Error(finalJob.error || 'Worker failed to create the post')
      }
      setContent('')
      setImageUrl('')
      await load()
    } catch (err) {
      setError(err.message)
    } finally {
      setCreatingPost(false)
      setPostJob(null)
    }
  }
  async function saveProfile() { const next = await api.updateProfile({ name: user.name, bio }); localStorage.setItem('cloudconnect_user', JSON.stringify(next)); setUser(next) }
  async function likePost(id) { await api.togglePostLike(id); load() }
  async function deletePost(id) { await api.deletePost(id); load() }
  return <main className="dashboard"><section className="dash-hero"><div><div className="pill"><Cloud size={14} /> Local Docker Environment</div><h1>Microservices Social Feed</h1><p>Connect with developers, share DevOps lessons, attach optional public images, and discuss ideas through comments and likes. Nginx routes the React experience to independent FastAPI services, while Redis Queue and the Worker Service process post creation asynchronously like a real cloud-native social platform.</p></div><div className="service-strip"><span>frontend</span><span>auth</span><span>user</span><span>post</span><span>worker</span><span>redis</span><span>like</span><span>comment</span><span>analytics</span><span>postgres</span></div></section>{error && <div className="error wide">{error}</div>}<div className="dash-grid"><aside className="profile-card"><div className="avatar">{user.name?.[0]?.toUpperCase()}</div><h3>{user.name}</h3><p>{user.email}</p><textarea value={bio} onChange={e => setBio(e.target.value)} placeholder="Add a short DevOps bio" /><button className="outline full" onClick={saveProfile}>Save Profile</button><div className="mini-arch"><b>Local Routing</b><span>Browser → Nginx → Post Service → Redis Queue → Worker → PostgreSQL</span></div></aside><section className="feed"><form className="composer" onSubmit={createPost}><textarea value={content} onChange={e => setContent(e.target.value)} placeholder="Share what you learned about ECS, Docker, ALB, RDS, Redis Queue, or private subnets..." disabled={creatingPost} /><input value={imageUrl} onChange={e => setImageUrl(e.target.value)} placeholder="Optional public image URL, e.g. https://images.unsplash.com/..." disabled={creatingPost} />{creatingPost && <div className="create-loader"><div className="loader-ring"><Loader2 size={26} /></div><div><b>Queuing your post through Redis...</b><span>{postJob?.status ? `Current status: ${postJob.status}` : 'Waiting for Worker Service'}</span></div></div>}<div className="composer-footer"><span>Image is optional. Create post waits 2 seconds to demonstrate async Redis Queue + Worker processing.</span><button className="primary" disabled={creatingPost}>{creatingPost ? 'Processing...' : 'Publish Post'} {!creatingPost && <ArrowRight size={15} />}</button></div></form>{posts.map(post => <PostCard key={post.id} post={post} currentUser={user} onLike={likePost} onDelete={deletePost} reloadPosts={load} />)}{!posts.length && <div className="empty">No posts yet. Create the first DevConnect post.</div>}</section></div></main>
}

function PublicImage({ src, alt, compact = false }) {
  const [hidden, setHidden] = useState(false)
  if (!src || hidden) return null
  return <div className={compact ? 'public-image compact' : 'public-image'}><img src={src} alt={alt} loading="lazy" onError={() => setHidden(true)} /></div>
}

function PostCard({ post, currentUser, onLike, onDelete, reloadPosts }) {
  const [comments, setComments] = useState([])
  const [open, setOpen] = useState(false)
  const [text, setText] = useState('')
  const [commentImageUrl, setCommentImageUrl] = useState('')
  async function loadComments() { setComments(await api.comments(post.id)) }
  async function toggleComments() { const next = !open; setOpen(next); if (next) loadComments() }
  async function addComment(e) {
    e.preventDefault()
    if (!text.trim()) return
    await api.createComment(post.id, { content: text, image_url: commentImageUrl.trim() || null })
    setText('')
    setCommentImageUrl('')
    loadComments()
    reloadPosts()
  }
  async function likeComment(id) { await api.toggleCommentLike(id); loadComments() }
  return <article className="post-card"><div className="post-head"><div className="avatar small-avatar">{post.author_name?.[0]}</div><div><b>{post.author_name}</b><small>{new Date(post.created_at).toLocaleString()}</small></div>{post.user_id === currentUser.id && <button className="icon-btn" onClick={() => onDelete(post.id)}><Trash2 size={15} /></button>}</div><p>{post.content}</p><PublicImage src={post.image_url} alt={`Image shared by ${post.author_name}`} /><div className="post-actions"><button className={post.liked_by_me ? 'glow-btn active' : 'glow-btn'} onClick={() => onLike(post.id)}><Heart size={16} /> {post.like_count}</button><button className="glow-btn" onClick={toggleComments}><MessageCircle size={16} /> {post.comment_count} comments</button></div>{open && <div className="comments"><form onSubmit={addComment} className="comment-form image-comment-form"><div className="comment-inputs"><input value={text} onChange={e => setText(e.target.value)} placeholder="Write a comment..." /><input value={commentImageUrl} onChange={e => setCommentImageUrl(e.target.value)} placeholder="Optional public image URL" /></div><button className="primary small">Reply</button></form>{comments.map(c => <div key={c.id} className="comment"><div><b>{c.author_name}</b><p>{c.content}</p><PublicImage src={c.image_url} alt={`Image shared by ${c.author_name}`} compact /></div><button className={c.liked_by_me ? 'tiny-like active' : 'tiny-like'} onClick={() => likeComment(c.id)}><Heart size={13} /> {c.like_count}</button></div>)}</div>}</article>
}

createRoot(document.getElementById('root')).render(<App />)
