import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

# App config & session imports
from backend.app.config.settings import settings
from backend.app.database.session import Base, engine, SessionLocal
from backend.app.database.seeder import seed_database
from backend.app.routers import auth, inventory, forecast, core_routers

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("pharmacy_platform")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager that handles startup database migrations and seeding."""
    logger.info("Starting up Smart Pharmacy Platform API server...")
    
    # 1. Database initializations & Alembic Migrations
    try:
        from alembic.config import Config
        from alembic import command
        
        config_dir = os.path.dirname(os.path.abspath(__file__)) # backend/app
        backend_dir = os.path.dirname(config_dir) # backend
        ini_path = os.path.join(backend_dir, "alembic.ini")
        
        alembic_cfg = Config(ini_path)
        alembic_cfg.set_main_option("script_location", os.path.join(backend_dir, "alembic"))
        
        # Test connection & check schema
        db = SessionLocal()
        schema_ok = True
        try:
            # Query standard table to verify columns exist
            db.execute(text("SELECT user_id, username, role, password_hash FROM users LIMIT 1"))
        except Exception as query_err:
            logger.warning(f"Database schema check failed: {query_err}")
            schema_ok = False
        finally:
            db.close()
            
        if schema_ok:
            logger.info("Database connection validated. Running migration upgrades...")
            command.upgrade(alembic_cfg, "head")
        else:
            if settings.ENV == "development":
                logger.warning("Recreating database tables in development mode...")
                Base.metadata.drop_all(bind=engine)
                Base.metadata.create_all(bind=engine)
                command.stamp(alembic_cfg, "head")
            else:
                logger.error("Database query failed in production. Applying migrations head...")
                command.upgrade(alembic_cfg, "head")
                
    except Exception as err:
        logger.error(f"Error during Alembic migration startup: {err}. Falling back to metadata create_all...", exc_info=True)
        Base.metadata.create_all(bind=engine)
        
    # 2. Database Seeding
    db = SessionLocal()
    try:
        seed_database(db)
    except Exception as e:
        logger.error(f"Failed to seed database during startup: {e}", exc_info=True)
    finally:
        db.close()
        
    yield
    
    logger.info("Shutting down Smart Pharmacy Platform API server...")

app = FastAPI(
    title="Smart Pharmacy Platform API",
    description="Production-grade AI-powered Pharmacy demand forecasting and inventory tracking API.",
    version=settings.API_VERSION,
    lifespan=lifespan
)

# Configure CORS Middleware
allowed_origins = ["*"]
if settings.ENV == "production":
    origins_env = os.environ.get("ALLOWED_ORIGINS", "")
    allowed_origins = [o.strip() for o in origins_env.split(",") if o.strip()]
    if not allowed_origins:
        # Fallback to default streamlit local client address if none defined in prod
        allowed_origins = ["http://localhost:8501"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception occurred: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred. Please contact the administrator."}
    )

# Include Routers under API v1 prefix
api_prefix = f"/api/{settings.API_VERSION}"
app.include_router(auth.router, prefix=api_prefix)
app.include_router(inventory.router, prefix=api_prefix)
app.include_router(forecast.router, prefix=api_prefix)
app.include_router(core_routers.router, prefix=api_prefix)

@app.get("/")
def health_check():
    """General health check endpoint."""
    return {
        "status": "healthy",
        "environment": settings.ENV,
        "api_version": settings.API_VERSION,
        "database": "sqlite" if settings.DATABASE_URL.startswith("sqlite") else "postgresql"
    }
