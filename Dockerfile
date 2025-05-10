# ── Dockerfile ─────────────────────────────────────────
FROM python:3.10-slim

# -------- OS deps ----------
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# -------- Python deps -------
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# -------- Project code ------
COPY . .

# -------- Default start -----
CMD ["uvicorn", "webapp:app", "--host", "0.0.0.0", "--port", "8000"]
