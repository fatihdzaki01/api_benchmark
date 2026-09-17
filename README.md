# Api - Benchmarking

Benchmarking API file-serving untuk menemukan **batas kemampuan sistem** (sampai berapa banyak user sebelum sistem error / latency melonjak).

- **Skenario 1 (S1)**: 1 API instance, tanpa load balancer.
- **Skenario 2 (S2)**: 3 API instance + Nginx load balancer.
- Kedua skenario diuji **berurutan** (S1 selesai dulu, baru S2) lalu hasilnya dibandingkan.

## Tech Stack
- **API**: Python FastAPI + Uvicorn
- **Load Balancer**: Nginx
- **Testing**: Locust (headless, otomatis)
- **Container**: Docker + Docker Compose

## Folder Structure
```
├── api/
│   ├── main.py                 # FastAPI server (serve file)
│   ├── generate_files.py       # Generate file .bin (1kb-100mb)
│   ├── requirements.txt        # Dependencies
│   └── Dockerfile              # Build image
├── files/                      # File hasil generate (volume host)
├── nginx/
│   └── nginx.conf              # Load balancer config
├── loadtest/
│   ├── locustfile.py           # Skenario test (5 ukuran file)
│   ├── run_headless.sh         # Runner: ladder users + deteksi batas
│   ├── make_summary.py         # Buat ringkasan HTML (satuan second)
│   ├── requirements.txt
│   ├── Dockerfile
│   └── results/                # Output: *.html (dibuat saat test)
├── docker-compose.single.yml   # Scenario 1 (1 API)
├── docker-compose.cluster.yml  # Scenario 2 (3 API + Nginx LB)
└── README.md
```

## API Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/files/{size}` | Serve file (1kb, 10kb, 1mb, 10mb, 100mb) |
| GET | `/health` | Health check |

## File Sizes
| File | Size |
|------|------|
| file_1kb.bin | 1 KB |
| file_10kb.bin | 10 KB |
| file_1mb.bin | 1 MB |
| file_10mb.bin | 10 MB |
| file_100mb.bin | 100 MB |


