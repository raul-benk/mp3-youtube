# mp3-youtube

Ferramenta para coletar links do YouTube (playlist, busca ou lista manual) e baixar áudio em MP3 em lote.

Inclui:
- CLI em Python
- API backend em FastAPI
- Frontend web em Next.js + Tailwind

## Requisitos

- Python 3.8+
- Node.js 18+ e npm
- FFmpeg no `PATH`
- Internet ativa (YouTube)

## 1) Rodar Backend (API)

```bash
cd /Users/raulbehnke/mp3-youtube
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Validação:
- [http://localhost:8000/health](http://localhost:8000/health) -> `{"ok": true}`
- [http://localhost:8000/docs](http://localhost:8000/docs) -> Swagger

## 2) Rodar Frontend (Web)

Abra outro terminal:

```bash
cd /Users/raulbehnke/mp3-youtube/frontend
npm install
NEXT_PUBLIC_API_BASE=http://localhost:8000 npm run dev
```

Abra:
- [http://localhost:3000](http://localhost:3000)

## 3) Fluxo de uso (UI)

1. Em **Entrada de Dados**, escolha `Playlist`, `Busca` ou `Lista manual`.
2. Clique **Buscar músicas** para gerar os links.
3. Em **Download**, clique **Selecionar pasta** para abrir o explorador nativo.
4. Revise/seleciona os links.
5. Clique **Baixar todas**.
6. Acompanhe progresso no bloco **Status**.

Observações:
- Qualidade é fixa em MP3 **192 kbps**.
- O backend valida permissões de escrita no diretório antes de iniciar o job.

## Endpoints principais

- `GET /health`
- `GET /api/destinations`
- `POST /api/select-directory`
- `POST /api/collect`
- `POST /api/download`
- `GET /api/status/{job_id}`
- `GET /api/status?job_id=...`

## Exemplo de payload

`POST /api/collect`

```json
{
  "type": "playlist",
  "value": "https://www.youtube.com/watch?v=0ZF5em0MTwY&list=PLiP4bA16O4aNVBHoj9bGrjfqfcs6icy44",
  "limit": 20
}
```

`POST /api/download`

```json
{
  "urls": ["https://www.youtube.com/watch?v=0ZF5em0MTwY"],
  "output_path": "/Users/seu_usuario/Downloads/musicas",
  "archive": "archive.txt"
}
```

## Executar somente CLI (opcional)

```bash
cd /Users/raulbehnke/mp3-youtube
source .venv/bin/activate
python cli.py --playlist "https://www.youtube.com/watch?v=0ZF5em0MTwY&list=PLiP4bA16O4aNVBHoj9bGrjfqfcs6icy44"
```

Outros modos:
- `--search "Linkin Park" --limit 20`
- `--file links.txt`

## Troubleshooting

### `{"detail":"Not Found"}` no browser

Você provavelmente abriu `http://localhost:8000/` (backend).  
Abra `http://localhost:3000` para a interface web.

### `Seletor nativo indisponível`

O backend tenta abrir o seletor nativo por:
- `tkinter`
- macOS: `osascript`
- Windows: `powershell` (FolderBrowserDialog)
- Linux: `zenity`/`kdialog`

Se não abrir, informe `output_path` manualmente no campo de destino.

### Playlist retorna vazia

- Verifique se a playlist é pública.
- Confirme se a URL contém `list=...`.
- Teste novamente após alguns segundos (instabilidade de rede/YouTube).
