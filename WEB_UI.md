# Web UI (MVP)

## 1) Backend API (Python)

```bash
cd /Users/raulbehnke/mp3-youtube
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Endpoints:
- `POST /api/collect`
- `POST /api/download`
- `GET /api/destinations`
- `POST /api/select-directory`
- `GET /api/status/{job_id}`

## 2) Frontend (Next.js + Tailwind)

```bash
cd /Users/raulbehnke/mp3-youtube/frontend
npm install
NEXT_PUBLIC_API_BASE=http://localhost:8000 npm run dev
```

Abra:
- `http://localhost:3000`

## Payloads esperados

`POST /api/collect`

```json
{
  "type": "playlist",
  "value": "https://www.youtube.com/playlist?list=...",
  "limit": 20
}
```

`POST /api/download`

```json
{
  "urls": ["https://www.youtube.com/watch?v=..."],
  "output_path": "/Volumes/PENDRIVE/musicas",
  "archive": "archive.txt"
}
```

Observação:
- Qualidade é fixa no backend: MP3 192 kbps.
- Botão "Selecionar pasta" usa seletor nativo do sistema operacional via backend local.
