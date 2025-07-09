# BackDash Celery + Redis Setup Guide

## 🚀 **Phase 3: Real-time Features** - Now Complete!

This guide covers the enhanced task processing system with **Celery workers** and **Redis persistence**.

---

## **📋 Prerequisites**

### **Required Services**
1. **Redis Server** - Task broker and result storage
2. **Python 3.8+** - Runtime environment
3. **FastAPI Application** - Main API server

### **Installation**

```bash
# Install Redis (Ubuntu/Debian)
sudo apt update
sudo apt install redis-server

# Install Redis (macOS)
brew install redis

# Install Redis (Windows - via WSL or Docker)
docker run -d -p 6379:6379 redis:latest

# Install Python dependencies
pip install -r requirements.txt
```

---

## **🏗️ System Architecture**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI API   │◄──►│  Redis Broker   │◄──►│ Celery Workers  │
│   (main.py)     │    │   (Task Queue)  │    │ (Background)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  WebSocket UI   │    │ Task Persistence │    │ Progress Updates│
│  (Real-time)    │    │  (Redis Store)  │    │  (WebSocket)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### **Key Components:**
- **FastAPI API**: Receives requests, queues tasks
- **Celery Workers**: Process tasks in background
- **Redis**: Task queue, result storage, progress tracking
- **WebSocket**: Real-time progress updates
- **Flower**: Task monitoring dashboard

---

## **🚀 Quick Start**

### **1. Start Redis Server**
```bash
# Start Redis
redis-server

# Verify Redis is running
redis-cli ping
# Should return: PONG
```

### **2. Start FastAPI Application**
```bash
# From backend directory
python main.py

# Application will be available at:
# http://localhost:8000
# API docs: http://localhost:8000/docs
```

### **3. Start Celery Workers**
```bash
# Start Celery worker (required for task processing)
python start_celery.py worker

# Or start all services for development
python start_celery.py all
```

### **4. Monitor with Flower (Optional)**
```bash
# Start Flower monitoring
python start_celery.py flower

# Flower dashboard: http://localhost:5555
```

---

## **📊 Available Services**

### **Task Queues:**
- `backtest` - Backtesting execution tasks
- `strategy` - Strategy validation tasks  
- `analytics` - Analytics and maintenance tasks

### **API Endpoints:**

#### **Backtest Endpoints** (`/api/v1/backtest/`)
- `POST /run` - Start backtest with Celery
- `GET /status/{task_id}` - Get task status
- `GET /result/{task_id}` - Get backtest results
- `POST /cancel/{task_id}` - Cancel running task
- `GET /active` - List active backtest tasks
- `GET /statistics` - Task processing statistics

#### **Admin Endpoints** (`/api/v1/admin/`)
- `GET /health` - System health check
- `GET /statistics` - System statistics
- `GET /tasks/active` - All active tasks
- `POST /tasks/{task_id}/cancel` - Cancel any task
- `DELETE /tasks/{task_id}` - Delete task data
- `POST /cleanup` - Clean expired tasks
- `GET /celery/workers` - Celery worker info
- `GET /redis/info` - Redis server info

#### **WebSocket Endpoints** (`/ws/`)
- `/ws/backtest/{task_id}` - Real-time backtest updates
- `/ws/strategy/{strategy_id}` - Strategy validation updates

---

## **🔧 Configuration**

### **Environment Variables** (`.env`)
```bash
# Redis Configuration
REDIS_URL=redis://localhost:6379

# Task Processing
MAX_CONCURRENT_BACKTESTS=5
TASK_TIMEOUT_SECONDS=3600

# Application
DEBUG=false
ENVIRONMENT=development
```

### **Celery Configuration**
- **Worker Concurrency**: Based on `MAX_CONCURRENT_BACKTESTS`
- **Task Routing**: Separate queues for different task types
- **Result Persistence**: 24 hours for results, 1 hour for progress
- **Automatic Cleanup**: Every 5 minutes via Celery Beat

---

## **🎯 Usage Examples**

### **1. Start a Backtest**
```bash
curl -X POST "http://localhost:8000/api/v1/backtest/run" \
  -H "Content-Type: application/json" \
  -d '{
    "strategy": {...},
    "timeframe": "1h",
    "start_date": "2023-01-01T00:00:00Z",
    "end_date": "2023-12-31T23:59:59Z",
    "initial_capital": 100000
  }'

# Response:
{
  "task_id": "abc123-def456-ghi789",
  "status": "started",
  "message": "Backtest started with Celery",
  "websocket_url": "/ws/backtest/abc123-def456-ghi789",
  "celery_task_id": "abc123-def456-ghi789"
}
```

### **2. Monitor Task Progress**
```bash
# Get task status
curl "http://localhost:8000/api/v1/backtest/status/abc123-def456-ghi789"

# Response:
{
  "task_id": "abc123-def456-ghi789",
  "status": "running",
  "progress": 45,
  "message": "Processing bar 450/1000",
  "source": "redis"
}
```

### **3. Get Results**
```bash
# Get backtest results
curl "http://localhost:8000/api/v1/backtest/result/abc123-def456-ghi789"

# Returns: Complete BacktestResult object
```

### **4. System Health Check**
```bash
curl "http://localhost:8000/api/v1/admin/health"

# Response:
{
  "timestamp": "2024-01-01T12:00:00Z",
  "overall_status": "healthy",
  "components": {
    "api": "healthy",
    "redis": "healthy", 
    "celery": "healthy"
  }
}
```

---

## **📈 Monitoring & Management**

### **Flower Dashboard**
- **URL**: http://localhost:5555
- **Features**: Task monitoring, worker management, real-time stats

### **Redis Monitoring**
```bash
# Redis CLI monitoring
redis-cli monitor

# Memory usage
redis-cli info memory

# Key statistics  
redis-cli info keyspace
```

### **Task Management**
```bash
# List active tasks
curl "http://localhost:8000/api/v1/admin/tasks/active"

# Cancel a task
curl -X POST "http://localhost:8000/api/v1/admin/tasks/{task_id}/cancel"

# Clean up expired tasks
curl -X POST "http://localhost:8000/api/v1/admin/cleanup"
```

---

## **🔍 Troubleshooting**

### **Common Issues:**

#### **Redis Connection Failed**
```bash
# Check if Redis is running
redis-cli ping

# Check Redis logs
tail -f /var/log/redis/redis-server.log

# Restart Redis
sudo systemctl restart redis-server
```

#### **Celery Worker Not Starting**
```bash
# Check Celery configuration
python -c "from app.celery_app import celery_app; print(celery_app.conf)"

# Start worker with debug
celery -A app.celery_app worker --loglevel=debug
```

#### **Tasks Stuck in Pending**
```bash
# Check worker status
curl "http://localhost:8000/api/v1/admin/celery/workers"

# Restart workers
pkill -f "celery worker"
python start_celery.py worker
```

#### **WebSocket Connection Issues**
- Ensure both FastAPI and WebSocket endpoints are accessible
- Check CORS configuration for WebSocket origins
- Verify task_id exists in Redis

---

## **🚀 Production Deployment**

### **Recommended Setup:**
1. **Redis Cluster** - High availability
2. **Multiple Celery Workers** - Horizontal scaling  
3. **Load Balancer** - FastAPI instances
4. **Process Manager** - systemd/supervisor
5. **Monitoring** - Flower + Prometheus

### **systemd Service Example:**
```ini
# /etc/systemd/system/backdash-worker.service
[Unit]
Description=BackDash Celery Worker
After=network.target redis.service

[Service]
Type=exec
User=backdash
Group=backdash
WorkingDirectory=/opt/backdash
ExecStart=/opt/backdash/venv/bin/python start_celery.py worker
Restart=always

[Install]
WantedBy=multi-user.target
```

---

## **✅ Phase 3 Completion Status**

### **✅ Implemented:**
- ✅ **Celery Integration** - Replace FastAPI BackgroundTasks
- ✅ **Redis Persistence** - Task and result storage  
- ✅ **Real-time Updates** - WebSocket integration maintained
- ✅ **Task Management** - Cancel, monitor, cleanup
- ✅ **Admin Interface** - Health checks and monitoring
- ✅ **Production Ready** - Scalable worker architecture

### **🎯 Benefits:**
- **Persistent Tasks** - Survive server restarts
- **Horizontal Scaling** - Multiple workers
- **Better Reliability** - Task retry and error handling
- **Monitoring** - Comprehensive task tracking
- **Production Ready** - Enterprise-grade architecture

---

## **🔄 What's Next?**

**Phase 3 is now 100% complete!** 

The system now features:
- Professional-grade task processing with Celery
- Persistent storage with Redis
- Real-time monitoring capabilities  
- Production-ready architecture

Ready for **Phase 4** (Advanced Analytics) or **Phase 5** (Database Integration)! 