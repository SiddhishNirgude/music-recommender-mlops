"""
FastAPI Application with Prometheus Metrics

This version includes comprehensive monitoring:
- Request counts by endpoint
- Response times
- Error rates
- Mood popularity tracking
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from typing import Optional
import time

# Prometheus imports
from prometheus_client import Counter, Histogram, Gauge, make_asgi_app
from prometheus_client import REGISTRY, CollectorRegistry

from src.api.models import (
    RecommendRequest,
    RecommendResponse,
    SimilarArtistRequest,
    SimilarArtistResponse,
    ChartsResponse,
    HealthResponse,
    MoodsResponse
)
from src.api.recommender import RecommenderService
from src.api.mood_profiles import MOOD_PROFILES, get_mood_seed_artists

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global recommender instance
recommender: Optional[RecommenderService] = None

# ============================================================================
# PROMETHEUS METRICS DEFINITIONS
# ============================================================================

# Request counters
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

# Request duration histogram
http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint']
)

# Recommendation-specific metrics
recommendations_total = Counter(
    'recommendations_total',
    'Total recommendations served',
    ['type']
)

mood_requests = Counter(
    'mood_requests_total',
    'Mood recommendation requests',
    ['mood']
)

similar_artist_requests = Counter(
    'similar_artist_requests_total',
    'Similar artist search requests'
)

charts_requests = Counter(
    'charts_requests_total',
    'Top charts requests'
)

# Model metrics
model_loaded = Gauge(
    'model_loaded',
    'Whether the model is loaded (1) or not (0)'
)

model_users = Gauge(
    'model_users_total',
    'Total number of users in model'
)

model_artists = Gauge(
    'model_artists_total',
    'Total number of artists in model'
)

# Error tracking
api_errors_total = Counter(
    'api_errors_total',
    'Total API errors',
    ['endpoint', 'error_type']
)

# ============================================================================
# FASTAPI LIFESPAN & INITIALIZATION
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events
    """
    global recommender
    
    # Startup
    logger.info("🚀 Starting Music Recommender API...")
    
    try:
        recommender = RecommenderService()
        logger.info("✅ Recommender service loaded successfully")
        
        # Set model metrics
        model_loaded.set(1)
        if recommender.model:
            model_users.set(recommender.model.user_factors.shape[0])
            model_artists.set(recommender.model.item_factors.shape[0])
        
    except Exception as e:
        logger.error(f"❌ Failed to load recommender: {e}")
        model_loaded.set(0)
        recommender = None
    
    yield
    
    # Shutdown
    logger.info("👋 Shutting down Music Recommender API...")


# Create FastAPI app
app = FastAPI(
    title="Music Recommender API",
    description="ALS-based music recommendation system with monitoring",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# ============================================================================
# MIDDLEWARE FOR AUTOMATIC METRICS COLLECTION
# ============================================================================

@app.middleware("http")
async def add_metrics_middleware(request, call_next):
    """
    Middleware to automatically collect metrics for all requests
    """
    start_time = time.time()
    
    # Get endpoint path
    endpoint = request.url.path
    method = request.method
    
    try:
        response = await call_next(request)
        status = response.status_code
        
        # Record metrics
        http_requests_total.labels(
            method=method,
            endpoint=endpoint,
            status=status
        ).inc()
        
        duration = time.time() - start_time
        http_request_duration_seconds.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)
        
        return response
        
    except Exception as e:
        # Record error
        api_errors_total.labels(
            endpoint=endpoint,
            error_type=type(e).__name__
        ).inc()
        
        duration = time.time() - start_time
        http_request_duration_seconds.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)
        
        raise


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "message": "Music Recommender API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "recommend": "/recommend",
            "similar": "/similar",
            "charts": "/charts",
            "moods": "/moods",
            "metrics": "/metrics"
        }
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Health check endpoint
    Returns model status and metadata
    """
    if recommender is None:
        raise HTTPException(
            status_code=503,
            detail="Recommender service not initialized"
        )
    
    return HealthResponse(
        status="healthy",
        model_loaded=recommender.model is not None,
        model_info={
            "n_users": recommender.model.user_factors.shape[0] if recommender.model else 0,
            "n_artists": recommender.model.item_factors.shape[0] if recommender.model else 0,
            "n_factors": recommender.model.user_factors.shape[1] if recommender.model else 0,
        }
    )


@app.post("/recommend", response_model=RecommendResponse, tags=["Recommendations"])
async def get_recommendations(request: RecommendRequest):
    """
    Get music recommendations
    
    Supports three types:
    - mood: Based on mood profiles
    - user: Based on user ID
    - random: Random user recommendations
    """
    if recommender is None:
        api_errors_total.labels(
            endpoint="/recommend",
            error_type="ServiceUnavailable"
        ).inc()
        raise HTTPException(
            status_code=503,
            detail="Recommender service not available"
        )
    
    try:
        # Track recommendation type
        recommendations_total.labels(type=request.type).inc()
        
        if request.type == "mood":
            if not request.mood:
                api_errors_total.labels(
                    endpoint="/recommend",
                    error_type="MissingParameter"
                ).inc()
                raise HTTPException(
                    status_code=400,
                    detail="mood parameter required for mood-based recommendations"
                )
            
            # Track mood popularity
            mood_requests.labels(mood=request.mood).inc()
            
            # Get mood recommendations
            recs, seed_artists = recommender.get_recommendations_by_mood(
                request.mood,
                k=request.k
            )
            
            return RecommendResponse(
                recommendations=[
                    {
                        "artist_name": artist,
                        "score": float(score),
                        "rank": i + 1
                    }
                    for i, (artist, score) in enumerate(recs)
                ],
                type="mood",
                metadata={
                    "mood": request.mood,
                    "seed_artists": seed_artists
                }
            )
        
        elif request.type == "user":
            if request.user_id is None:
                api_errors_total.labels(
                    endpoint="/recommend",
                    error_type="MissingParameter"
                ).inc()
                raise HTTPException(
                    status_code=400,
                    detail="user_id required for user-based recommendations"
                )
            
            recs = recommender.get_user_recommendations(
                request.user_id,
                k=request.k
            )
            
            return RecommendResponse(
                recommendations=[
                    {
                        "artist_name": artist,
                        "score": float(score),
                        "rank": i + 1
                    }
                    for i, (artist, score) in enumerate(recs)
                ],
                type="user",
                metadata={"user_id": request.user_id}
            )
        
        elif request.type == "random":
            recs, user_id = recommender.get_random_recommendations(k=request.k)
            
            return RecommendResponse(
                recommendations=[
                    {
                        "artist_name": artist,
                        "score": float(score),
                        "rank": i + 1
                    }
                    for i, (artist, score) in enumerate(recs)
                ],
                type="random",
                metadata={"sampled_user_id": user_id}
            )
        
        else:
            api_errors_total.labels(
                endpoint="/recommend",
                error_type="InvalidType"
            ).inc()
            raise HTTPException(
                status_code=400,
                detail=f"Invalid recommendation type: {request.type}"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        api_errors_total.labels(
            endpoint="/recommend",
            error_type=type(e).__name__
        ).inc()
        logger.error(f"Error in recommend endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/similar", response_model=SimilarArtistResponse, tags=["Recommendations"])
async def get_similar_artists(request: SimilarArtistRequest):
    """
    Get similar artists based on artist name
    Uses cosine similarity on item factors
    """
    if recommender is None:
        api_errors_total.labels(
            endpoint="/similar",
            error_type="ServiceUnavailable"
        ).inc()
        raise HTTPException(
            status_code=503,
            detail="Recommender service not available"
        )
    
    try:
        # Track similar artist requests
        similar_artist_requests.inc()
        
        similar = recommender.get_similar_artists(
            request.artist_name,
            k=request.k
        )
        
        return SimilarArtistResponse(
            query_artist=request.artist_name,
            similar_artists=[
                {
                    "artist_name": artist,
                    "score": float(similarity),
                    "rank": i + 1
                }
                for i, (artist, similarity) in enumerate(similar)
            ]
        )
    
    except ValueError as e:
        api_errors_total.labels(
            endpoint="/similar",
            error_type="ArtistNotFound"
        ).inc()
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        api_errors_total.labels(
            endpoint="/similar",
            error_type=type(e).__name__
        ).inc()
        logger.error(f"Error in similar endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/charts", response_model=ChartsResponse, tags=["Charts"])
async def get_top_charts(k: int = 20):
    """
    Get top K most popular artists by play count
    """
    if recommender is None:
        api_errors_total.labels(
            endpoint="/charts",
            error_type="ServiceUnavailable"
        ).inc()
        raise HTTPException(
            status_code=503,
            detail="Recommender service not available"
        )
    
    try:
        # Track charts requests
        charts_requests.inc()
        
        charts = recommender.get_top_charts(k=k)
        
        return ChartsResponse(
            charts=[
                {
                    "artist_name": artist,
                    "play_count": int(plays),
                    "listener_count": int(listeners),
                    "rank": i + 1
                }
                for i, (artist, plays, listeners) in enumerate(charts)
            ]
        )
    
    except Exception as e:
        api_errors_total.labels(
            endpoint="/charts",
            error_type=type(e).__name__
        ).inc()
        logger.error(f"Error in charts endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/moods", response_model=MoodsResponse, tags=["Moods"])
async def get_available_moods():
    """
    Get all available mood profiles
    """
    return MoodsResponse(moods=MOOD_PROFILES)


# ============================================================================
# EXCEPTION HANDLERS
# ============================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """
    Global exception handler
    """
    api_errors_total.labels(
        endpoint=request.url.path,
        error_type=type(exc).__name__
    ).inc()
    
    logger.error(f"Unhandled exception: {exc}")
    
    return {
        "error": str(exc),
        "type": type(exc).__name__
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
