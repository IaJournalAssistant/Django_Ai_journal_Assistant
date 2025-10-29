# Task & Project Planning API Documentation

## 🎉 API Implementation Complete!

The Django REST Framework API for the Task & Project Planning module is now fully functional with comprehensive CRUD operations, filtering, searching, and joint entity management.

## 🌐 Base URL
```
http://127.0.0.1:8000/planning/api/
```

## 🔑 Authentication
The API uses Token Authentication. Include the token in your requests:
```
Authorization: Token f6dc9929d54a168a952c91e280e3908fc60feb36
```

## 📊 API Endpoints

### Tasks API (`/tasks/`)
**Full CRUD operations for tasks with advanced features**

#### Standard Endpoints:
- `GET /tasks/` - List all user's tasks (paginated, filterable, searchable)
- `POST /tasks/` - Create a new task
- `GET /tasks/{id}/` - Retrieve specific task details
- `PUT /tasks/{id}/` - Update a task
- `PATCH /tasks/{id}/` - Partially update a task
- `DELETE /tasks/{id}/` - Delete a task

#### Custom Actions:
- `POST /tasks/{id}/mark_completed/` - Mark task as completed
- `POST /tasks/{id}/mark_in_progress/` - Mark task as in progress
- `GET /tasks/overdue/` - Get all overdue tasks
- `GET /tasks/by_priority/` - Get tasks grouped by priority
- `GET /tasks/ai_suggested/` - Get all AI-suggested tasks

#### Filtering & Search:
- **Filters**: `status`, `priority`, `project`, `ai_suggested`
- **Search**: `title`, `description`
- **Ordering**: `created_at`, `updated_at`, `due_date`, `priority`

### Projects API (`/projects/`)
**Project management with task relationships**

#### Standard Endpoints:
- `GET /projects/` - List all user's projects
- `POST /projects/` - Create a new project
- `GET /projects/{id}/` - Retrieve project with all tasks
- `PUT /projects/{id}/` - Update a project
- `PATCH /projects/{id}/` - Partially update a project
- `DELETE /projects/{id}/` - Delete a project

#### Custom Actions:
- `POST /projects/{id}/update_progress/` - Recalculate progress from tasks
- `POST /projects/{id}/mark_completed/` - Mark project as completed
- `POST /projects/{id}/assign_task/` - Assign a task to project
- `POST /projects/{id}/remove_task/` - Remove a task from project
- `GET /projects/{id}/tasks/` - Get all tasks for project
- `GET /projects/active/` - Get all active projects
- `GET /projects/overdue/` - Get all overdue projects

#### Joint Entity Operations:
```json
// Assign task to project
POST /projects/{id}/assign_task/
{
    "task_id": 123
}

// Remove task from project
POST /projects/{id}/remove_task/
{
    "task_id": 123
}
```

### Goals API (`/goals/`)
**Goal tracking and progress management**

#### Standard Endpoints:
- `GET /goals/` - List all user's goals
- `POST /goals/` - Create a new goal
- `GET /goals/{id}/` - Retrieve specific goal
- `PUT /goals/{id}/` - Update a goal
- `PATCH /goals/{id}/` - Partially update a goal
- `DELETE /goals/{id}/` - Delete a goal

#### Custom Actions:
- `POST /goals/{id}/update_progress/` - Update goal progress percentage
- `POST /goals/{id}/mark_achieved/` - Mark goal as achieved
- `GET /goals/active/` - Get all active goals
- `GET /goals/achieved/` - Get all achieved goals
- `GET /goals/overdue/` - Get all overdue goals

### Comments API (`/comments/`)
**Task comments and discussions**

#### Standard Endpoints:
- `GET /comments/` - List comments for user's tasks
- `POST /comments/` - Create a new comment
- `GET /comments/{id}/` - Retrieve specific comment
- `PUT /comments/{id}/` - Update a comment
- `DELETE /comments/{id}/` - Delete a comment

### AI Insights API (`/insights/`)
**AI-generated suggestions and insights**

#### Standard Endpoints:
- `GET /insights/` - List all user's AI insights
- `POST /insights/` - Create a new AI insight
- `GET /insights/{id}/` - Retrieve specific insight
- `PUT /insights/{id}/` - Update an insight
- `DELETE /insights/{id}/` - Delete an insight

#### Custom Actions:
- `POST /insights/{id}/apply/` - Mark insight as applied
- `POST /insights/{id}/dismiss/` - Mark insight as dismissed
- `GET /insights/pending/` - Get all pending insights

## 📝 Example API Usage

### Create a Task
```bash
curl -X POST http://127.0.0.1:8000/planning/api/tasks/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Complete API documentation",
    "description": "Write comprehensive API docs",
    "priority": "high",
    "due_date": "2025-11-01T10:00:00Z"
  }'
```

### Create a Project
```bash
curl -X POST http://127.0.0.1:8000/planning/api/projects/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Website Redesign",
    "description": "Complete website overhaul",
    "start_date": "2025-10-30",
    "target_completion_date": "2025-12-15"
  }'
```

### Assign Task to Project
```bash
curl -X POST http://127.0.0.1:8000/planning/api/projects/1/assign_task/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"task_id": 5}'
```

### Filter Tasks by Status
```bash
curl "http://127.0.0.1:8000/planning/api/tasks/?status=in_progress" \
  -H "Authorization: Token YOUR_TOKEN"
```

### Search Tasks
```bash
curl "http://127.0.0.1:8000/planning/api/tasks/?search=documentation" \
  -H "Authorization: Token YOUR_TOKEN"
```

## 🔧 API Features

### ✅ **Comprehensive CRUD Operations**
- Full Create, Read, Update, Delete for all entities
- Proper validation and error handling
- User isolation (users only see their own data)

### ✅ **Advanced Filtering & Search**
- Multi-field filtering with django-filter
- Full-text search across relevant fields
- Flexible ordering and sorting

### ✅ **Joint Entity Management**
- Task-Project relationship management
- Automatic progress calculation
- Bulk operations support

### ✅ **Smart Features**
- Overdue detection for tasks, projects, and goals
- Progress calculation and tracking
- AI insight management
- Status change actions

### ✅ **Security & Authentication**
- Token-based authentication
- User data isolation
- Permission-based access control
- Input validation and sanitization

### ✅ **Developer Experience**
- Browsable API interface at `/planning/api/`
- Comprehensive serialization
- Pagination support
- Clear error messages

## 🎯 Next Steps

The API layer is complete and ready for frontend integration. You can now:

1. **Build Modern Frontend Interface** (Phase 4)
   - Create responsive web interface with HTMX
   - Build modern UI components with real-time updates

2. **Implement AI Integration** (Phase 5)
   - Add smart task suggestions
   - Create project planning automation
   - Build productivity insights

3. **Add Advanced Features** (Phase 6)
   - Real-time notifications
   - Drag-and-drop functionality
   - Mobile responsiveness

The API provides a solid foundation for any frontend framework or mobile application to consume the Task & Project Planning functionality.