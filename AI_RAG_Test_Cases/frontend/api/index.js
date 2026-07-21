const Groq = require('groq-sdk');
const TOP_K = parseInt(process.env.TOP_K || '10');
const LLM = process.env.LLM_MODEL || 'llama-3.3-70b-versatile';

let store = { chunks: [], total: 0, name: '', status: 'idle' };

function chunkText(text) {
  const chunks = []; let cid = 0; const sz = 500, ov = 100; let s = 0;
  while (s < text.length) {
    let e = Math.min(s + sz, text.length);
    if (e < text.length) {
      const bp = Math.max(text.lastIndexOf('. ', e), text.lastIndexOf('\n', e));
      if (bp > s + sz / 2) e = bp + 1;
    }
    const ct = text.slice(s, e).trim();
    if (ct.length > 30) chunks.push({ id: 'c' + String(cid).padStart(4, '0'), text: ct, idx: cid });
    cid++; s = e - ov; if (e >= text.length) break;
  }
  return chunks;
}

module.exports = async (req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', '*');
  if (req.method === 'OPTIONS') return res.status(200).end();

  const url = req.url || '/';

  try {
    // HEALTH
    if (req.method === 'GET' && url.startsWith('/api/health')) {
      return res.json({
        status: 'ok',
        services: { groq: !!process.env.GROQ_API_KEY },
        ingestion: store,
        config: { top_k: TOP_K, llm_model: LLM }
      });
    }

    // INGEST
    if (req.method === 'POST' && url === '/api/ingest') {
      const chunks = [];
      for await (const chunk of req) chunks.push(chunk);
      const body = Buffer.concat(chunks);
      const ct = req.headers['content-type'] || '';
      const bnd = ct.split('boundary=')[1]?.replace(/"/g, '');
      if (!bnd) throw new Error('Not multipart');
      const parts = body.toString().split('--' + bnd);
      let fd = '', fn = 'upload.file';
      for (const p of parts) {
        if (p.includes('filename=')) {
          const he = p.indexOf('\r\n\r\n');
          const h = p.slice(0, he);
          fd = p.slice(he + 4).trim();
          fd = fd.replace(new RegExp('--' + bnd + '--?$'), '').trim();
          const m = h.match(/filename="([^"]+)"/);
          if (m) fn = m[1];
          break;
        }
      }
      if (!fd) throw new Error('No file');
      store.chunks = chunkText(fd);
      store.total = store.chunks.length;
      store.name = fn;
      store.status = 'done';
      return res.json({ message: `Ingested ${fn}: ${store.total} chunks`, status: 'done', total: store.total });
    }

    // QUERY
    if (req.method === 'POST' && url === '/api/query') {
      const { query } = req.body || {};
      if (!query) throw new Error('Query empty');
      if (store.status !== 'done') throw new Error('No document ingested');
      const groqKey = req.headers['x-groq-key'] || process.env.GROQ_API_KEY;
      if (!groqKey) throw new Error('GROQ_API_KEY missing');

      const ql = query.toLowerCase().split(/\s+/).filter(w => w.length > 2);
      const scored = store.chunks.map(c => {
        const w = c.text.toLowerCase().split(/\s+/);
        const m = ql.filter(qw => w.some(cw => cw.includes(qw)));
        return { ...c, score: m.length / (ql.length || 1) };
      });
      scored.sort((a, b) => b.score - a.score);
      const k = Math.min(req.body?.top_k || TOP_K, 50);
      const top = scored.slice(0, k).map(c => ({
        id: c.id, text: c.text.slice(0, 1200),
        relevance_score: Math.round(c.score * 100)
      }));

      const ctx = top.map(c => `[${c.id}]\n${c.text}`).join('\n\n---\n\n');
      const groq = new Groq({ apiKey: groqKey });
      const ans = await groq.chat.completions.create({
        model: LLM,
        messages: [
          { role: 'system', content: 'You analyze test case documents. Use ONLY the context. Be concise and format clearly.' },
          { role: 'user', content: `Context:\n${ctx}\n\n---\nQuestion: ${query}` }
        ],
        temperature: 0.2, max_tokens: 1024
      });
      return res.json({ query, chunks: top, answer: ans.choices[0].message.content || 'No answer.', model: LLM });
    }

    return res.status(404).json({ error: 'Not found' });
  } catch (e) {
    return res.status(500).json({ detail: e.message });
  }
};
