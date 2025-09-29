# Email Helper - Quick Start Guide

Get up and running with Email Helper in 5 minutes!

## 🎯 Prerequisites

Before you begin, ensure you have:

- [x] **Docker Desktop** installed ([Download](https://www.docker.com/products/docker-desktop))
- [x] **Docker Compose** (included with Docker Desktop)
- [x] **Azure OpenAI** access and API key
- [x] **Microsoft Graph API** credentials (optional, for email integration)

## 🚀 5-Minute Setup

### Step 1: Clone the Repository

```bash
git clone https://github.com/AmeliaRose802/email_helper.git
cd email_helper
```

### Step 2: Configure Environment

```bash
# Copy the environment template
cp .env.docker .env

# Edit .env with your configuration
nano .env  # or use your favorite editor
```

**Required Configuration:**
```bash
# Update these values in .env:
SECRET_KEY=your-secret-key-here  # Generate with: openssl rand -hex 32
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_DEPLOYMENT=gpt-4o
```

### Step 3: Start the Application

```bash
# Start all services (backend, frontend, Redis)
docker-compose up -d

# Wait for services to be ready (about 30 seconds)
sleep 30
```

### Step 4: Verify Installation

```bash
# Check service health
curl http://localhost:8000/health   # Backend health check
curl http://localhost/health.html   # Frontend health check

# Or use the health check script
./deployment/scripts/health-check.sh dev
```

### Step 5: Access the Application

Open your browser and navigate to:

- **Frontend**: http://localhost
- **API Documentation**: http://localhost:8000/docs
- **Backend Health**: http://localhost:8000/health

## 📱 Using the Application

### 1. Register a User

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "SecurePassword123!"
  }'
```

### 2. Login

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "SecurePassword123!"
  }'
```

Save the `access_token` from the response.

### 3. Access Protected Endpoints

```bash
# Use the access token
curl http://localhost:8000/auth/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 4. Use the Web Interface

1. Navigate to http://localhost
2. Click "Login"
3. Enter your credentials
4. Explore the dashboard, email list, and tasks

## 🔧 Common Commands

### View Logs

```bash
# View all logs
docker-compose logs -f

# View specific service
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Restart Services

```bash
# Restart all services
docker-compose restart

# Restart specific service
docker-compose restart backend
```

### Stop Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

### Update Services

```bash
# Pull latest changes
git pull

# Rebuild and restart
docker-compose up -d --build
```

## 🐛 Troubleshooting

### Backend Won't Start

**Problem**: Backend container exits immediately

**Solution**:
```bash
# Check logs for errors
docker-compose logs backend

# Common issues:
# 1. Missing SECRET_KEY in .env
# 2. Invalid Azure OpenAI credentials
# 3. Port 8000 already in use

# Verify environment variables
docker-compose exec backend env | grep SECRET_KEY
```

### Frontend Can't Connect to Backend

**Problem**: Frontend shows "Network Error"

**Solution**:
```bash
# Check backend is running
docker-compose ps backend

# Test backend from host
curl http://localhost:8000/health

# Test from frontend container
docker-compose exec frontend curl http://backend:8000/health

# Check nginx configuration
docker-compose exec frontend cat /etc/nginx/conf.d/default.conf
```

### Database Errors

**Problem**: SQLite database locked or permission errors

**Solution**:
```bash
# Reset database
docker-compose down -v
docker-compose up -d

# Or switch to PostgreSQL (edit docker-compose.yml)
# Uncomment database service and update DATABASE_URL
```

### Port Conflicts

**Problem**: "Port is already allocated"

**Solution**:
```bash
# Check what's using the port
sudo lsof -i :8000
sudo lsof -i :80

# Stop the conflicting service or change ports in docker-compose.yml
```

## 🎓 Next Steps

### For Developers

1. **Explore the API**: http://localhost:8000/docs
2. **Read the Backend Docs**: [backend/README.md](./backend/README.md)
3. **Read the Frontend Docs**: [frontend/README.md](./frontend/README.md)
4. **Run Tests**:
   ```bash
   # Backend tests
   docker-compose exec backend pytest
   
   # Frontend tests
   cd frontend && npm test
   ```

### For DevOps

1. **Production Deployment**: See [deployment/PRODUCTION_DEPLOYMENT.md](./deployment/PRODUCTION_DEPLOYMENT.md)
2. **Monitoring Setup**: See [deployment/MONITORING.md](./deployment/MONITORING.md)
3. **CI/CD Configuration**: See [.github/workflows/](../.github/workflows/)

### Configuration Options

#### Environment Variables

Full list of configuration options in `.env.docker`:

**Backend**:
- `DEBUG` - Enable debug mode (true/false)
- `SECRET_KEY` - JWT secret key (required)
- `DATABASE_URL` - Database connection string
- `AZURE_OPENAI_*` - Azure OpenAI configuration
- `GRAPH_*` - Microsoft Graph API configuration
- `REDIS_URL` - Redis connection string

**Frontend**:
- `VITE_API_BASE_URL` - Backend API URL

#### Database Options

**SQLite** (Default - Development):
```bash
DATABASE_URL=sqlite:///./runtime_data/email_helper_history.db
```

**PostgreSQL** (Production):
```bash
# Uncomment database service in docker-compose.yml
DATABASE_URL=postgresql://emailhelper:changeme@database:5432/email_helper
```

## 📚 Additional Resources

### Documentation
- [Complete Deployment Guide](./DEPLOYMENT.md)
- [Architecture Overview](./docs/)
- [API Documentation](http://localhost:8000/docs) (when running)

### Support
- GitHub Issues: https://github.com/AmeliaRose802/email_helper/issues
- Backend API Tests: `docker-compose exec backend pytest -v`
- Frontend Tests: `cd frontend && npm test`

### Useful Links
- [Docker Documentation](https://docs.docker.com/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [Azure OpenAI Documentation](https://learn.microsoft.com/en-us/azure/ai-services/openai/)

## ✅ Success Criteria

You should now have:

- ✅ Backend API running at http://localhost:8000
- ✅ Frontend web app at http://localhost
- ✅ API documentation at http://localhost:8000/docs
- ✅ Health checks passing
- ✅ Ability to register and login users
- ✅ Access to email and task management features

## 🎉 You're Ready!

Congratulations! Your Email Helper instance is now running locally.

**What's Next?**
- Configure Microsoft Graph API for email integration
- Customize the application for your needs
- Deploy to production using the deployment guides

---

**Need Help?** Open an issue on GitHub or check the [troubleshooting section](#troubleshooting) above.
