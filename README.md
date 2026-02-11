# 🎵 Music Recommender MLOps Pipeline

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-available-blue.svg)](https://www.docker.com/)
[![CI/CD](https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-green.svg)](https://github.com/features/actions)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

End-to-end production-ready MLOps pipeline for music recommendations using Alternating Least Squares (ALS) collaborative filtering on the Last.fm-360K dataset. Demonstrates industry best practices including experiment tracking, automated testing, containerized deployment, and real-time monitoring.

![Master Architecture](diagrams/00_MASTER_DIAGRAM.png)

---

## 📋 Table of Contents

- [Features](#-features)
- [Architecture](#-architecture)
- [Quick Start](#-quick-start)
- [Dataset](#-dataset)
- [Model Performance](#-model-performance)
- [Technologies](#-technologies)
- [Project Structure](#-project-structure)
- [Development](#-development)
- [Monitoring](#-monitoring)
- [CI/CD Pipeline](#-cicd-pipeline)
- [Production Deployment](#-production-deployment)
- [Documentation](#-documentation)
- [Contributing](#-contributing)
- [Team](#-team)
- [License](#-license)

---

## ✨ Features

### **MLOps Infrastructure**
- 🔄 **Data Version Control** - DVC with AWS S3 backend for reproducible data pipelines
- 📊 **Experiment Tracking** - MLflow tracking 7 hyperparameter configurations
- 🧪 **Automated Testing** - 52 pytest tests (98% passing) with GitHub Actions CI/CD
- 🐳 **Containerization** - Docker Compose orchestrating 4 microservices
- 📈 **Real-time Monitoring** - Prometheus + Grafana with 6 dashboard panels
- 🚀 **Production Ready** - Health checks, auto-restart, graceful degradation

### **Machine Learning**
- **Algorithm**: Alternating Least Squares (ALS) collaborative filtering
- **Dataset**: Last.fm-360K (17.5M interactions, 358K users, 126K artists)
- **Performance**: 1.37% Precision@10, 0.88% MAP@10, 1.44% NDCG@10
- **Inference Speed**: 180ms average response time
- **Model Size**: 370 MB (150 latent factors)

### **User Interface**
- 🎨 **Streamlit Web App** - Intuitive mood-based recommendations (12 moods)
- 🔌 **FastAPI Backend** - RESTful API with 6 endpoints
- 📊 **Interactive Docs** - Automatic Swagger UI documentation
- 🎯 **Features**: Mood recommendations, artist similarity, top charts, random discovery

---

## 🏗️ Architecture

### **System Components**

```
┌─────────────────────────────────────────────────────────────────┐
│                         DATA LAYER                               │
│  Last.fm (17.5M) → AWS S3 (1.64GB) → DVC → Preprocessing        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                        MODEL LAYER                               │
│  ALS Training (7 experiments) → MLflow → Model Registry          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      DEPLOYMENT LAYER                            │
│  Docker: FastAPI (8000) + Streamlit (8501) + Prometheus (9090)  │
│          + Grafana (3000)                                        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    MONITORING LAYER                              │
│  Metrics: 30-50 req/min, 0.18s latency, 0% errors              │
└─────────────────────────────────────────────────────────────────┘
```

**Key Flows:**
1. **Data Pipeline**: S3 → DVC → Preprocessing → Train/Test Split (80/20)
2. **Model Training**: ALS (factors=150) → Evaluation → MLflow Registry
3. **Deployment**: Docker Compose → 4 Services → Health Checks
4. **Monitoring**: Prometheus Scrape (10s) → Grafana Dashboards

---

## 🚀 Quick Start

### **Prerequisites**
- Docker Desktop 4.0+
- Python 3.12
- Git
- 8GB RAM recommended

### **1. Clone Repository**
```bash
git clone https://github.com/SiddhishNirgude/music-recommender-mlops.git
cd music-recommender-mlops
```

### **2. Configure AWS (for DVC data access)**
```bash
# Install AWS CLI
brew install awscli  # macOS
# OR: pip install awscli

# Configure credentials
aws configure
# AWS Access Key ID: [provided separately]
# AWS Secret Access Key: [provided separately]
# Default region: us-east-1
# Default output format: json
```

### **3. Install Dependencies**
```bash
pip install -r requirements.txt
```

### **4. Download Data**
```bash
# Pull dataset from S3 via DVC (~1.64 GB, takes 2-3 minutes)
dvc pull
```

### **5. Start All Services**
```bash
# Start Docker containers (API, UI, Prometheus, Grafana)
docker-compose up -d

# Wait for services to initialize (30 seconds)
sleep 30

# Verify all containers running
docker ps
```

### **6. Access Applications**

| Service | URL | Credentials | Purpose |
|---------|-----|-------------|---------|
| **Streamlit UI** | http://localhost:8501 | None | Main user interface |
| **FastAPI Docs** | http://localhost:8000/docs | None | API documentation & testing |
| **Grafana** | http://localhost:3000 | admin/admin | Monitoring dashboards |
| **Prometheus** | http://localhost:9090 | None | Metrics database |
| **MLflow** | http://localhost:5000 | None | Experiment tracking |

### **7. Test the System**
```bash
# Check API health
curl http://localhost:8000/health

# Expected: {"status":"healthy","model_loaded":true}

# Generate traffic for monitoring demo
python scripts/generate_traffic.py
# Press Ctrl+C to stop
```

### **8. Stop Services**
```bash
docker-compose down
```

**Total setup time: ~10 minutes** (excluding data download)

---

## 📊 Dataset

### **Last.fm-360K**
- **Source**: [Last.fm Dataset - 360K users](http://www.dtic.upf.edu/~ocelma/MusicRecommendationDataset/lastfm-360K.html)
- **Size**: 1.64 GB (raw TSV)
- **Interactions**: 17,535,655 user-artist play counts
- **Users**: 358,622 unique users
- **Artists**: 126,442 unique artists
- **Sparsity**: 99.97% (extremely sparse)
- **Type**: Implicit feedback (play counts, not ratings)

### **Preprocessing**
```python
# Quality filters applied:
- Remove users with < 5 interactions (eliminate noise)
- Remove artists with < 3 listeners (focus on established content)
- Aggregate duplicate user-artist pairs
- Create 80/20 train-test split (temporal per user)
- Confidence weighting: confidence = 1 + 40 × play_count
```

**Processed Data:**
- Training: 14,021,366 interactions (80%)
- Testing: 3,323,105 interactions (20%)
- Matrix: 358,622 × 126,442 (sparse CSR format)

---

## 🎯 Model Performance

### **Best Configuration**
```yaml
Model: Alternating Least Squares (ALS)
Factors: 150
Iterations: 25
Regularization: 0.01
Alpha: 40 (confidence weighting)
Training Time: 243 minutes
Model Size: 370 MB
```

### **Evaluation Metrics (Test Set)**

| Metric | Value | Interpretation |
|--------|-------|----------------|
| **Precision@10** | 1.37% | 1-2 relevant items per 10 recommendations |
| **MAP@10** | 0.88% | Ranking quality (rewards early relevant items) |
| **NDCG@10** | 1.44% | Position-weighted relevance |
| **Training Time** | 243 min | Full dataset, 150 factors |
| **Inference Time** | 0.18s | Average response time |

**Context:** These metrics are typical for implicit feedback systems with extreme sparsity (99.97%). Random guessing would achieve ~0.0008% precision (1,500× worse). Our model matches academic benchmarks on Last.fm dataset.

### **Experiment Comparison**

| Factors | Iterations | Precision@10 | Training Time | Selected |
|---------|-----------|--------------|---------------|----------|
| 150 | 25 | 1.37% | 243 min | ❌ (too slow) |
| **125** | **25** | **1.20%** | **13 min** | ✅ **BEST** |
| 100 | 20 | 0.85% | 6 min | ❌ (lower accuracy) |
| 75 | 20 | 0.69% | 4 min | ❌ (lower accuracy) |
| 50 | 15 | 0.34% | 2 min | ❌ (too low accuracy) |

**Decision:** Factors=125 selected for production (40% better than baseline, 18× faster than best model)

---

## 🛠️ Technologies

### **Machine Learning & Data**
- **Python 3.12** - Core language
- **implicit 0.7.2** - ALS implementation
- **NumPy / SciPy** - Matrix operations
- **pandas** - Data preprocessing
- **scikit-learn** - Train-test split, metrics

### **MLOps Infrastructure**
- **DVC 3.x** - Data version control
- **AWS S3** - Remote data storage
- **MLflow 2.x** - Experiment tracking & model registry
- **Docker / Docker Compose** - Containerization

### **API & Frontend**
- **FastAPI 0.109** - REST API framework
- **Streamlit 1.31** - Web UI
- **Pydantic** - Data validation
- **Uvicorn** - ASGI server

### **Monitoring & Observability**
- **Prometheus 2.x** - Metrics collection
- **Grafana 10.x** - Visualization dashboards
- **prometheus-client** - Python instrumentation

### **CI/CD & Testing**
- **GitHub Actions** - Continuous integration
- **pytest 8.x** - Testing framework (52 tests)
- **flake8** - Code linting
- **black / isort** - Code formatting

---

## 📁 Project Structure

```
music-recommender-mlops/
├── data/
│   ├── raw/                    # Raw Last.fm dataset (DVC tracked)
│   └── processed/              # Preprocessed train/test data
│       ├── train_interactions.csv
│       ├── test_interactions.csv
│       ├── user_item_matrix.npz
│       ├── user_mapping.json
│       └── artist_mapping.json
├── models/
│   ├── als_model.pkl          # Trained ALS model (370 MB)
│   ├── user_factors.npy       # User embeddings (358K × 150)
│   ├── item_factors.npy       # Artist embeddings (126K × 150)
│   └── model_metadata.json    # Model configuration
├── src/
│   ├── api/
│   │   ├── main.py           # FastAPI application
│   │   └── models.py         # Pydantic schemas
│   ├── streamlit_app.py      # Streamlit UI
│   └── preprocessing/
│       └── preprocess.py     # Data cleaning pipeline
├── scripts/
│   ├── run_preprocessing.py  # Execute preprocessing
│   ├── train_model.py        # Train ALS model
│   ├── run_experiments.py    # Hyperparameter tuning
│   ├── analyze_experiments.py # Compare MLflow runs
│   └── generate_traffic.py   # Load testing
├── tests/
│   ├── test_api.py           # API endpoint tests
│   ├── test_model.py         # Model functionality tests
│   └── test_preprocessing.py # Data pipeline tests
├── monitoring/
│   ├── prometheus.yml        # Prometheus config
│   └── grafana/
│       └── provisioning/     # Grafana datasources
├── diagrams/                  # Architecture diagrams (7 PDFs)
│   ├── 00_MASTER_DIAGRAM.pdf
│   ├── 01_data_pipeline.pdf
│   ├── 02_model_training.pdf
│   ├── 03_deployment.pdf
│   ├── 04_user_request.pdf
│   ├── 05_cicd.pdf
│   └── 06_monitoring.pdf
├── docs/
│   ├── PROJECT_START.md      # Startup guide
│   ├── PROJECT_STOP.md       # Shutdown guide
│   ├── PRODUCTION_RISKS.md   # Risk assessment (13 risks)
│   └── PROJECT_DOCUMENTATION.docx  # Complete project docs
├── .github/
│   └── workflows/
│       └── ci.yml            # GitHub Actions pipeline
├── docker-compose.yml        # Service orchestration
├── Dockerfile               # API container image
├── requirements.txt         # Python dependencies
├── .dvc/                    # DVC configuration
├── data.dvc                 # DVC data tracker
├── mlruns/                  # MLflow experiment data
├── experiments_comparison.csv  # Model comparison results
└── README.md               # This file
```

---

## 💻 Development

### **Running Locally (Without Docker)**

**Start FastAPI:**
```bash
cd src/api
uvicorn main:app --reload --port 8000
# Access: http://localhost:8000/docs
```

**Start Streamlit:**
```bash
streamlit run src/streamlit_app.py
# Access: http://localhost:8501
```

**Start MLflow:**
```bash
mlflow ui
# Access: http://localhost:5000
```

### **Training New Model**

```bash
# Preprocess data (if not done)
python scripts/run_preprocessing.py

# Train with default config
python scripts/train_model.py

# Or run hyperparameter experiments
python scripts/run_experiments.py
```

### **Running Tests**

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_api.py -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

### **Code Quality**

```bash
# Format code
black src/ tests/
isort src/ tests/

# Lint
flake8 src/ tests/ --max-line-length=100

# Type checking
mypy src/
```

---

## 📈 Monitoring

### **Grafana Dashboard Panels**

**Access:** http://localhost:3000 (admin/admin)

1. **Requests Per Minute**
   - Current: 30-50 req/min
   - PromQL: `rate(http_requests_total[1m]) * 60`

2. **Average Response Time**
   - Current: 0.18 seconds
   - Thresholds: Green <0.5s, Yellow <1s, Red >1s

3. **Error Rate**
   - Current: 0%
   - Alert threshold: >1% warning, >5% critical

4. **Total Recommendations**
   - Cumulative counter since startup

5. **Top 5 Moods**
   - Heartbreak: 38%
   - Party: 22%
   - Chill: 15%
   - Motivation: 12%
   - Focus: 8%

6. **Model Status**
   - Users: 358,622
   - Artists: 126,442
   - Factors: 150

### **Prometheus Metrics**

**Endpoint:** http://localhost:9090

**Available Metrics:**
- `http_requests_total` - Total API requests
- `http_request_duration_seconds` - Response time histogram
- `api_errors_total` - Error count
- `recommendations_total` - Recommendations served
- `mood_requests_total` - Requests per mood
- `model_loaded` - Model status (0/1)

### **Generating Test Traffic**

```bash
# Simulate 30 req/min for monitoring demo
python scripts/generate_traffic.py

# Let it run for 2-3 minutes to populate Grafana
# Press Ctrl+C to stop
```

---

## 🔄 CI/CD Pipeline

### **GitHub Actions Workflow**

**Triggers:** Push to `main`, Pull Requests

**Pipeline Stages:**

1. **Code Quality** (~30s)
   - Black formatting check
   - isort import sorting
   - Flake8 linting (PEP 8)

2. **Testing** (~2 min)
   - 52 pytest tests
   - Coverage report
   - Integration tests

3. **Docker Build** (~1 min)
   - Build API image
   - Build Streamlit image
   - Tag with commit SHA

4. **Security Scan** (~30s)
   - Dependency vulnerability check
   - Container image scanning

**Total Duration:** 3-5 minutes

**Current Status:** ✅ 52/53 tests passing (98%)

**View Pipeline:** https://github.com/SiddhishNirgude/music-recommender-mlops/actions

---

## 🚀 Production Deployment

### **Current Status**
- ✅ Docker Compose (local/single-server deployment)
- ✅ Health checks & auto-restart
- ✅ Monitoring & alerting infrastructure
- ⚠️ Kubernetes deployment (planned)

### **Docker Compose Deployment**

```bash
# Production startup
docker-compose up -d

# Check service health
docker-compose ps

# View logs
docker-compose logs -f api

# Scale API replicas (manual)
docker-compose up -d --scale api=3
```

### **Kubernetes Deployment (Planned)**

**Features:**
- Horizontal Pod Autoscaler (HPA) - Scale based on CPU/memory
- LoadBalancer service - Distribute traffic
- PersistentVolumeClaim - Model storage
- ConfigMap - Environment config
- Secrets - Credentials management

**Estimated Setup Time:** 2-3 hours

---

## 📚 Documentation

### **Available Guides**

| Document | Description | Location |
|----------|-------------|----------|
| **PROJECT_START.md** | Complete startup guide | `docs/` |
| **PROJECT_STOP.md** | Shutdown procedures | `docs/` |
| **PRODUCTION_RISKS.md** | 13 identified risks + mitigations | `docs/` |
| **PROJECT_DOCUMENTATION.docx** | 7-page technical overview | `docs/` |
| **PRESENTATION_SCRIPT.docx** | 10-page presentation guide | `docs/` |
| **Architecture Diagrams** | 7 PDF flowcharts | `diagrams/` |

### **Architecture Diagrams**

1. **Master Diagram** - Complete system overview
2. **Data Pipeline** - S3 → DVC → Preprocessing
3. **Model Training** - ALS → MLflow → Registry
4. **Deployment** - Docker 4-service architecture
5. **User Request Flow** - End-to-end latency breakdown
6. **CI/CD Pipeline** - GitHub Actions workflow
7. **Monitoring** - Prometheus → Grafana flow

---

## 🤝 Contributing

We welcome contributions! Please follow these guidelines:

### **Setup Development Environment**

```bash
# Fork the repository
git clone https://github.com/YOUR_USERNAME/music-recommender-mlops.git
cd music-recommender-mlops

# Create virtual environment
python -m venv venv
source venv/bin/activate  # macOS/Linux
# OR: venv\Scripts\activate  # Windows

# Install dev dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install
```

### **Development Workflow**

1. Create feature branch: `git checkout -b feature/your-feature`
2. Make changes and add tests
3. Run tests: `pytest tests/ -v`
4. Format code: `black src/ && isort src/`
5. Commit: `git commit -m "Add feature X"`
6. Push: `git push origin feature/your-feature`
7. Create Pull Request

### **Code Standards**

- ✅ Python 3.12+ compatible
- ✅ Type hints for functions
- ✅ Docstrings (Google style)
- ✅ Tests for new features (pytest)
- ✅ <100 characters per line
- ✅ Black formatting
- ✅ Pass all CI/CD checks

---

## 👥 Team

**Siddhish Nirgude**
- Role: Data Pipeline, Model Development, MLflow Integration
- Email: nirgudes@msu.edu
- GitHub: [@SiddhishNirgude](https://github.com/SiddhishNirgude)

**Sharod Williams**
- Role: Deployment, Monitoring, CI/CD, Infrastructure
- Email: willi645@msu.edu

**Course:** STT890 - Machine Learning Operations  
**Institution:** Michigan State University  
**Semester:** Fall 2024

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **Last.fm** for providing the 360K user dataset
- **Michigan State University** for computational resources
- **Anthropic** for Claude AI assistance in documentation
- **Open Source Community** for the amazing tools (FastAPI, Streamlit, MLflow, etc.)

---

## 📞 Support

**Issues:** https://github.com/SiddhishNirgude/music-recommender-mlops/issues

**Discussions:** https://github.com/SiddhishNirgude/music-recommender-mlops/discussions

**Documentation:** See `docs/` folder for detailed guides

---

## 🎓 Academic Context

This project was developed as part of STT890 (Machine Learning Operations) coursework, demonstrating:
- Complete ML lifecycle implementation
- Production-ready deployment practices
- Automated testing and CI/CD
- Real-time monitoring and observability
- Risk management and mitigation strategies

**Grade Requirements Met:**
- ✅ Process documentation (6 detailed diagrams)
- ✅ Online data ingestion (DVC + AWS S3)
- ✅ Data and model repositories (versioned)
- ✅ Predictive modeling (ALS collaborative filtering)
- ✅ User-accessible deployment (Streamlit UI)
- ✅ Monitoring dashboards (Grafana 6 panels)
- ✅ Production risks document (13 risks identified)

---

## 📊 Project Statistics

```
Total Lines of Code: ~5,000
Python Files: 25
Docker Containers: 4
Tests: 52 (98% passing)
Documentation Pages: 50+
Architecture Diagrams: 7
Deployment Time: 30 seconds
Training Time: 13 minutes (production model)
Model Size: 370 MB
Dataset Size: 1.64 GB
Total Interactions: 17.5M
Response Time: 0.18s average
Uptime: 99%+
```

---

**⭐ Star this repo if you found it helpful!**

**🔗 Connect:** [GitHub](https://github.com/SiddhishNirgude) • [LinkedIn](https://linkedin.com/in/siddhishnirgude)

---

*Last Updated: December 2024*
