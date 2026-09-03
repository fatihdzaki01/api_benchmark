# Tugas 2 - File Serving API dengan Load Balancer

## Tech Stack
- **API**: Python FastAPI + Uvicorn
- **Load Balancer**: Nginx
- **Testing**: Locust
- **Container**: Docker + Docker Compose

## Folder Structure
```
├── api/
│   ├── main.py                 # FastAPI server
│   ├── generate_files.py       # Generate test files
│   ├── requirements.txt        # Dependencies
│   └── Dockerfile              # Build image
├── files/                      # Pre-generated test files
│   ├── file_1kb.bin
│   ├── file_10kb.bin
│   ├── file_1mb.bin
│   ├── file_10mb.bin
│   └── file_100mb.bin
├── nginx/
│   └── nginx.conf              # Load balancer config
├── loadtest/
│   ├── locustfile.py           # Test scenarios
│   ├── requirements.txt        # Dependencies
│   ├── Dockerfile              # Build image
│   └── results/                # Test results
├── docker-compose.single.yml   # Scenario 1
├── docker-compose.cluster.yml  # Scenario 2
└── README.md
```

## API Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/files/{size}` | Serve file (1kb, 10kb, 1mb, 10mb, 100mb) |
| GET | `/health` | Health check |

## How to Use

### 1. Build Images
```bash
# Scenario 1
docker-compose -f docker-compose.single.yml build

# Scenario 2
docker-compose -f docker-compose.cluster.yml build
```

### 2. Generate Files (otomatis saat build, atau manual)
```bash
docker-compose -f docker-compose.single.yml run api-single python generate_files.py
```

### 3. Scenario 1: Single Instance (No LB)
```bash
docker-compose -f docker-compose.single.yml up api-single
# API available at http://localhost:8000
# Test: curl http://localhost:8000/files/1kb
```

### 4. Scenario 2: Cluster (3 Instances + Nginx LB)
```bash
docker-compose -f docker-compose.cluster.yml up
# Nginx LB available at http://localhost:80
# API instances: api-single:8000, api-2:8000, api-3:8000
```

### 5. Run Locust Load Testing
```bash
# Single instance test
docker-compose -f docker-compose.single.yml up locust
# Locust UI: http://localhost:8089

# Cluster test
docker-compose -f docker-compose.cluster.yml up locust
# Locust UI: http://localhost:8089
```

### 6. Locust Test Configuration
Di Locust UI, isi:
- **Number of users**: 100 (atau 1000)
- **Spawn rate**: 10 (users per second)
- **Run time**: 5m (5 menit)

### 7. Stop All
```bash
docker-compose -f docker-compose.single.yml down
docker-compose -f docker-compose.cluster.yml down
```

## Test Scenarios

### Scenario 1: Single Instance
- 1 API instance di port 8000
- Tanpa Load Balancer
- Test: 100 users → 1000 users → naik bertahap

### Scenario 2: Cluster + Nginx LB
- 3 API instances (api-single, api-2, api-3)
- Nginx di port 80 sebagai Load Balancer
- Round-robin distribution
- Test: 100 users → 1000 users → naik bertahap

## Metrics to Capture
- Response Time (avg, median, p95, p99)
- Throughput (Requests per Second / RPS)
- Error Rate (%)
- Total Requests

## File Sizes
| File | Size |
|------|------|
| file_1kb.bin | 1 KB |
| file_10kb.bin | 10 KB |
| file_1mb.bin | 1 MB |
| file_10mb.bin | 10 MB |
| file_100mb.bin | 100 MB |
