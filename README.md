# MindMap - Web-based Mind Mapping Tool

A web service based on Markmap CLI with user management and admin dashboard.

## 🎯 Features

- **Mindmap Creation**: Create beautiful mindmaps from Markdown
- **Custom Borders**: 1px node borders matching node colors
- **User Management**: Login/Register with personal spaces
- **Admin Dashboard**: System statistics and metrics

## 🚀 Tech Stack

- **Backend**: FastAPI + SQLite
- **Frontend**: HTML/Tailwind/JavaScript
- **Mindmap**: Markmap CLI
- **Deploy**: Docker Compose

## 📦 Installation

```bash
# Clone repo
git clone https://github.com/gabi-agent/mindmap.git
cd mindmap

# Run with Docker
docker-compose up -d

# Access at http://localhost:8080
```

## 🔧 Development

```bash
# Install dependencies
cd backend
pip install -r requirements.txt

# Run development server
uvicorn main:app --reload --host 0.0.0.0 --port 8080
```

## 📊 API Endpoints

### Auth
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login
- `GET /api/auth/me` - Get current user

### Mindmaps
- `GET /api/mindmaps` - List user's mindmaps
- `POST /api/mindmaps` - Create new mindmap
- `GET /api/mindmaps/{id}` - Get mindmap
- `PUT /api/mindmaps/{id}` - Update mindmap
- `DELETE /api/mindmaps/{id}` - Delete mindmap
- `GET /api/mindmaps/{id}/render` - Render as HTML

### Admin
- `GET /api/admin/stats` - System statistics
- `GET /api/admin/users` - List all users
- `GET /api/admin/mindmaps` - List all mindmaps

## 🐳 Docker

```bash
# Build and run
docker-compose up -d --build

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

## 📝 License

MIT

---

*Built with ❤️ by Gabi and the OpenClaw team*
