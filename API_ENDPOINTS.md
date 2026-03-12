# API Endpoints - Task Status Updates

Base URL: `https://ops-backend-production-e8ce.up.railway.app`

## 🔥 Quick Status Update

**Endpoint:** `PATCH /api/v1/tasks/{task_id}/status`

Optimized endpoint for fast task status updates with automatic state transition validation.

### Request

```bash
curl -X PATCH "https://ops-backend-production-e8ce.up.railway.app/api/v1/tasks/123/status" \
  -H "Content-Type: application/json" \
  -d '{"status": "in_progress"}'
```

### Request Body

```json
{
  "status": "backlog" | "in_progress" | "done" | "blocked"
}
```

### Response

```json
{
  "id": 123,
  "title": "Task title",
  "status": "in_progress",
  "priority": "high",
  "assigned_to": "Shosanna",
  "project_id": 1,
  "created_at": "2026-03-12T18:00:00Z",
  "updated_at": "2026-03-12T18:30:00Z"
}
```

### Valid State Transitions

- **backlog** → `in_progress`, `blocked`, `done`
- **in_progress** → `done`, `blocked`, `backlog`
- **done** → `backlog`, `in_progress`
- **blocked** → `backlog`, `in_progress`

### Error Responses

**404 Not Found**
```json
{"detail": "Task not found"}
```

**400 Bad Request** (Invalid transition)
```json
{"detail": "Invalid status transition: done → blocked"}
```

---

## 🎯 Bulk Update Tasks

**Endpoint:** `PATCH /api/v1/tasks/bulk-update`

Update multiple tasks at once. Perfect for batch operations.

### Request

```bash
curl -X PATCH "https://ops-backend-production-e8ce.up.railway.app/api/v1/tasks/bulk-update" \
  -H "Content-Type: application/json" \
  -d '{
    "task_ids": [123, 124, 125],
    "status": "in_progress",
    "assigned_to": "Shosanna"
  }'
```

### Request Body

```json
{
  "task_ids": [123, 124, 125],
  "status": "in_progress",        // Optional
  "priority": "high",             // Optional
  "assigned_to": "Shosanna"       // Optional
}
```

### Response

```json
{
  "updated_count": 3,
  "total_requested": 3,
  "errors": null
}
```

**With Errors** (partial success)
```json
{
  "updated_count": 2,
  "total_requested": 3,
  "errors": [
    {
      "task_id": 125,
      "error": "Invalid transition: done → blocked"
    }
  ]
}
```

### Error Responses

**400 Bad Request**
```json
{"detail": "task_ids cannot be empty"}
```

**404 Not Found**
```json
{"detail": "No tasks found with provided IDs"}
```

---

## ⚡ Features

- **State Validation:** Automatic validation of status transitions
- **Timestamps:** `updated_at` automatically updated on every change
- **Bulk Operations:** Update multiple tasks in a single request
- **Error Handling:** Detailed error messages for invalid transitions
- **Partial Success:** Bulk updates continue processing valid tasks even if some fail

---

## 🧪 Testing Examples

### Test Quick Status Update

```bash
# Move task to in_progress
curl -X PATCH "https://ops-backend-production-e8ce.up.railway.app/api/v1/tasks/1/status" \
  -H "Content-Type: application/json" \
  -d '{"status": "in_progress"}'

# Mark as done
curl -X PATCH "https://ops-backend-production-e8ce.up.railway.app/api/v1/tasks/1/status" \
  -H "Content-Type: application/json" \
  -d '{"status": "done"}'
```

### Test Bulk Update

```bash
# Update multiple tasks to in_progress
curl -X PATCH "https://ops-backend-production-e8ce.up.railway.app/api/v1/tasks/bulk-update" \
  -H "Content-Type: application/json" \
  -d '{
    "task_ids": [1, 2, 3],
    "status": "in_progress",
    "priority": "high"
  }'
```

---

**Deployed:** Railway  
**Last Updated:** 2026-03-12  
**Author:** Shosanna 🔥
