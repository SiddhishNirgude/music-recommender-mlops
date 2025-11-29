# Monitoring Setup Instructions

## 📋 Overview

This monitoring stack includes:
- **Prometheus**: Metrics collection (http://localhost:9090)
- **Grafana**: Visualization dashboards (http://localhost:3000)
- **Traffic Generator**: Simulates realistic API usage

## 🚀 Quick Start

### Step 1: Update Files

```bash
# Navigate to project
cd /Users/siddhishnirgude/Documents/Personal/USA/Semester\ 3\ MSU/MLOps/Project/music-recommender-mlops

# Create monitoring directory
mkdir -p monitoring/grafana/provisioning/datasources

# Move files
mv ~/Downloads/main_with_metrics.py src/api/main.py
mv ~/Downloads/prometheus.yml monitoring/
mv ~/Downloads/docker-compose-monitoring.yml docker-compose.yml
mv ~/Downloads/datasource.yml monitoring/grafana/provisioning/datasources/
mv ~/Downloads/generate_traffic.py scripts/

# Make traffic generator executable
chmod +x scripts/generate_traffic.py
```

### Step 2: Update requirements.txt

Add Prometheus client:

```bash
echo "prometheus-client==0.19.0" >> requirements.txt
```

### Step 3: Stop Existing Containers

```bash
docker-compose down
```

### Step 4: Start Monitoring Stack

```bash
# Build and start all services
docker-compose up --build

# Or run in background
docker-compose up -d --build
```

Wait 2-3 minutes for all services to start.

### Step 5: Verify Services

Open in browser:
- **API**: http://localhost:8000/docs
- **Streamlit**: http://localhost:8501
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000

### Step 6: Login to Grafana

1. Go to http://localhost:3000
2. Login:
   - Username: `admin`
   - Password: `admin`
3. Skip password change (or change it)

### Step 7: Verify Prometheus Connection

1. In Grafana, go to: Configuration → Data Sources
2. You should see "Prometheus" already configured
3. Click "Test" → Should show "Data source is working"

### Step 8: Generate Traffic

In a new terminal:

```bash
# Install requests if needed
pip install requests

# Run traffic generator
python scripts/generate_traffic.py
```

You should see:
```
🚀 Starting Traffic Generator
✅ API is accessible
[12:30:45] Requests: 50, RPM: 28.3, Errors: 0
```

## 📊 Available Metrics

### Request Metrics
- `http_requests_total` - Total requests by endpoint and status
- `http_request_duration_seconds` - Request latency histogram
- `recommendations_total` - Total recommendations by type
- `mood_requests_total` - Mood requests by mood name
- `similar_artist_requests_total` - Similar artist searches
- `charts_requests_total` - Top charts requests

### Model Metrics
- `model_loaded` - Whether model is loaded (0 or 1)
- `model_users_total` - Number of users in model
- `model_artists_total` - Number of artists in model

### Error Metrics
- `api_errors_total` - Total errors by endpoint and type

## 🎨 Creating Grafana Dashboards

### Example Queries

**1. Requests Per Minute**
```promql
rate(http_requests_total[1m]) * 60
```

**2. Average Response Time**
```promql
rate(http_request_duration_seconds_sum[5m]) / rate(http_request_duration_seconds_count[5m])
```

**3. Error Rate**
```promql
rate(api_errors_total[5m]) * 60
```

**4. Top Moods**
```promql
topk(5, mood_requests_total)
```

**5. Total Recommendations**
```promql
sum(recommendations_total)
```

### Creating a Dashboard

1. In Grafana, click "+" → "Dashboard"
2. Click "Add new panel"
3. Enter PromQL query
4. Configure visualization (Graph, Stat, Gauge, etc.)
5. Click "Apply"
6. Repeat for more panels
7. Save dashboard

## 🔍 Troubleshooting

### API Metrics Not Showing

Check if `/metrics` endpoint is accessible:
```bash
curl http://localhost:8000/metrics
```

Should return Prometheus format metrics.

### Prometheus Not Scraping

1. Go to http://localhost:9090/targets
2. Check if `music-recommender-api` target is UP
3. If DOWN, check API is running and accessible

### Grafana Can't Connect to Prometheus

1. In Grafana datasource settings, URL should be: `http://prometheus:9090`
2. Check both containers are on same network:
```bash
docker network inspect music-recommender-network
```

### Traffic Generator Errors

Make sure API is running:
```bash
curl http://localhost:8000/health
```

## 📈 What to Show Professor

1. **Live Dashboard** with:
   - Request volume (30+ req/min)
   - Response times (~0.2s average)
   - Error rate (<1%)
   - Top moods (Heartbreak 15%, Party 12%, etc.)
   - Total recommendations served

2. **Prometheus Metrics**
   - Show raw metrics at /metrics endpoint
   - Show Prometheus query interface

3. **Traffic Generator**
   - Show console output with stats
   - Explain it simulates realistic users

## 🎯 Dashboard Panels to Create

Suggested 6-8 panels:

1. **Requests/Minute** - Line graph
2. **Avg Response Time** - Stat panel
3. **Error Rate** - Gauge
4. **Top 5 Moods** - Bar chart
5. **Total Recommendations** - Stat panel
6. **Request by Endpoint** - Pie chart
7. **Model Status** - Stat panel (users/artists)
8. **API Uptime** - Stat panel

## 📝 Next Steps

After setup:
1. Let traffic generator run for 10-15 minutes
2. Create Grafana dashboards
3. Take screenshots for presentation
4. Practice demo walkthrough

## 🛑 Stopping

```bash
# Stop traffic generator: Ctrl+C

# Stop Docker containers
docker-compose down

# To remove volumes (start fresh)
docker-compose down -v
```
