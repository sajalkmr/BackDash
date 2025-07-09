"""
Configuration management for BackDash Backend
Supports environment-based configuration with proper defaults
"""

import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Application Info
    app_name: str = "BackDash"
    app_version: str = "2.0.0"
    app_description: str = "Professional backtesting platform for quantitative trading strategies"
    debug: bool = False
    
    # Server Configuration
    host: str = "127.0.0.1"
    port: int = 8000
    reload: bool = True
    log_level: str = "info"
    
    # CORS Configuration
    cors_origins: str = "http://localhost:3000,http://localhost:5173,http://localhost:8080"
    cors_allow_credentials: bool = True
    cors_allow_all_origins: bool = False
    
    # API Configuration
    api_v1_prefix: str = "/api/v1"
    docs_url: str = "/docs"
    redoc_url: str = "/redoc"
    openapi_url: str = "/api/v1/openapi.json"
    
    # Database Configuration
    database_url: Optional[str] = None
    redis_url: str = "redis://localhost:6379"
    
    # Security Configuration
    secret_key: str = "your-secret-key-change-in-production"
    access_token_expire_minutes: int = 30
    algorithm: str = "HS256"
    
    # Data Configuration
    data_directory: str = "./data"
    max_file_size_mb: int = 100
    supported_file_types: str = "csv,json,parquet"
    
    # Backtesting Configuration
    default_initial_capital: float = 100000.0
    default_commission: float = 0.001
    default_slippage: float = 0.0001
    max_backtest_duration_days: int = 365*5
    
    # WebSocket Configuration
    websocket_heartbeat_interval: int = 30
    websocket_timeout: int = 300
    
    # Task Processing Configuration
    max_concurrent_backtests: int = 5
    task_timeout_seconds: int = 3600
    
    # Analytics Configuration
    performance_benchmark: str = "BTC-USDT"
    risk_free_rate: float = 0.02
    confidence_level: float = 0.05
    
    # Monitoring and Logging
    enable_metrics: bool = True
    log_sql_queries: bool = False
    sentry_dsn: Optional[str] = None
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore"
    }
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Convert CORS origins string to list"""
        if self.cors_allow_all_origins:
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    @property
    def supported_file_types_list(self) -> List[str]:
        """Convert supported file types string to list"""
        return [file_type.strip() for file_type in self.supported_file_types.split(",")]
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return os.getenv("ENVIRONMENT", "development").lower() == "production"
    
    @property
    def database_config(self) -> dict:
        """Get database configuration"""
        if self.database_url:
            return {
                "url": self.database_url,
                "echo": self.log_sql_queries and not self.is_production,
                "pool_pre_ping": True,
                "pool_size": 10,
                "max_overflow": 20
            }
        return {}


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Global settings instance
settings = get_settings() 