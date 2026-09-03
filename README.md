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

## Cara Pakai (Headless Otomatis)

Test dijalankan bertahap per jumlah user: **100 → 1000 → dst** (default `100,1000,10000`), tiap tahap `5m`. Otomatis berhenti saat sistem mulai jebol (error > 10% ATAU p99 > 60s). Setiap tahap menghasilkan `results/<prefix>_<users>_users.html` + satu `results/<prefix>_ringkasan_seconds.html`.

> **PENTING**: saat test berjalan, jangan menjalankan aplikasi/tugas berat lain supaya hasil tidak terkontaminasi.

### 1. Generate file (sekali)
```bash
docker compose -f docker-compose.single.yml run --rm api-single python generate_files.py
```

### 2. Scenario 1: 1 API (tanpa LB)
```bash
docker compose -f docker-compose.single.yml up --build locust
# selesai → lihat hasil
docker compose -f docker-compose.single.yml down
```
Hasil: `loadtest/results/s1_*.html` + `s1_ringkasan_seconds.html`.

### 3. Scenario 2: 3 API + Nginx LB
```bash
docker compose -f docker-compose.cluster.yml up --build locust
# selesai → lihat hasil
docker compose -f docker-compose.cluster.yml down
```
Hasil: `loadtest/results/s2_*.html` + `s2_ringkasan_seconds.html`.

> Nginx tersedia di `http://localhost:80` (opsional, untuk cek manual).

### Mengubah jumlah user / durasi
Override lewat environment variable sebelum `up` (PowerShell):
```powershell
$env:LOCUST_USERS_LIST="100,1000,5000,10000,20000"
$env:LOCUST_RUN_TIME="5m"
docker compose -f docker-compose.single.yml up --build locust
docker compose -f docker-compose.single.yml down
```
Variabel lain yang bisa di-override: `LOCUST_SPAWN_RATE` (default `auto` = users/60 per detik), `LOCUST_MAX_ERROR_PCT` (default 10), `LOCUST_MAX_P99_S` (default 60), `SCENARIO_PREFIX`.

## Hasil yang Dihasilkan
1. **`results/<prefix>_<users>_users.html`** — laporan lengkap Locust: request count, RPS, error, dan distribusi response time per endpoint (grafik + tabel, dalam milidetik).
2. **`results/<prefix>_ringkasan_seconds.html`** — tabel ringkasan agregat **semua latensi dalam satuan detik (s)**: p50, p75, p90, p95, p99, max, RPS, dan error %, untuk tiap jumlah user. Baris **BATAS** = user count di mana sistem sudah lewat batas.

## Cara Baca / Cari Batas Sistem
- Cari baris pertama berstatus **BATAS** di `_ringkasan_seconds.html`.
- User count terakhir yang masih **OK** = batas kemampuan sistem sebelum error/latensi membengkak.
- Bandingkan `s1_ringkasan_seconds.html` vs `s2_ringkasan_seconds.html`: di user berapa masing-masing masih OK, dan bagaimana p50/p90/p95/p99-nya.

## Output untuk Tugas (video + PDF)
- **Video demo**: rekam proses menjalankan perintah S1 lalu S2 (step 2-3) dan buka file HTML hasilnya.
- **PDF (dibuat manual)**: ambil angka dari `_ringkasan_seconds.html` (semua sudah dalam **detik**), tambahkan penjelasan: metode, skenario, dan kesimpulan perbandingan S1 vs S2 + batas sistem.
