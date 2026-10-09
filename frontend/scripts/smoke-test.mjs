import fs from 'node:fs';

const main = fs.readFileSync(new URL('../src/main.jsx', import.meta.url), 'utf8');
const api = fs.readFileSync(new URL('../src/api.js', import.meta.url), 'utf8');
const nginx = fs.readFileSync(new URL('../nginx.conf', import.meta.url), 'utf8');

const requiredUiText = ['Home', 'Architecture', 'Services', 'Security', 'Analytics', 'DevConnect'];
for (const text of requiredUiText) {
  if (!main.includes(text)) {
    throw new Error(`Missing required UI text: ${text}`);
  }
}

const requiredRoutes = ['/api/auth/', '/api/user/', '/api/post/', '/api/like/', '/api/comment/', '/api/analytics/'];
for (const route of requiredRoutes) {
  if (!nginx.includes(route)) {
    throw new Error(`Missing nginx route: ${route}`);
  }
}

if (!api.includes('Authorization')) {
  throw new Error('API helper should send Authorization bearer token when available.');
}

console.log('Frontend smoke tests passed.');
