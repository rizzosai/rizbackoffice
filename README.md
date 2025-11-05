# Backoffice Backend

This is a fresh Node.js/Express backend for your backoffice. It uses SQLite for storage and supports Docker deployment.

## Quick Start

1. Install dependencies:
   ```powershell
   npm install
   ```
2. Start the server:
   ```powershell
   npm start
   ```
3. Environment variables are in `.env`.

## Docker

Build and run with Docker:
```powershell
docker build -t backoffice .
docker run -p 3000:3000 --env-file .env backoffice
```

## API Endpoints
- `GET /` — Health check
- `POST /user` — Add user (JSON: `{ "email": "..." }`)
