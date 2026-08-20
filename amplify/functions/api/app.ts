import { Hono } from 'hono'

// Lambda ハンドラとローカル開発サーバーの両方から同じアプリを使う
export const app = new Hono()

app.get('/health', (c) => c.json({ ok: true }))

app.get('/pets', (c) => c.json({ items: [], total: 0 }))
