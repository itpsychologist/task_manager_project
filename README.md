# Task Manager Project

A comprehensive Django-based task management system with team collaboration features, activity tracking, and real-time notifications.

## Features

### Core Functionality
- **Task Management**: Create, update, and track tasks with priorities, deadlines, and completion status
- **User Management**: Custom worker model with positions and role-based access control
- **Team Collaboration**: Organize workers into teams and assign tasks to multiple team members
- **Project Organization**: Group tasks and teams under projects for better organization
- **Tagging System**: Categorize tasks with custom tags for easy filtering and search

### Advanced Features
- **Activity Logging**: Automatic tracking of all task-related activities (creation, updates, assignments, completions)
- **Notifications**: Real-time notifications for task assignments, comments, and deadline reminders
- **Comments**: Threaded discussions on tasks with automatic notifications to assignees
- **Task Types**: Categorize tasks by custom types (bug, feature, enhancement, etc.)
- **Priority Levels**: Four priority levels (Urgent, High, Medium, Low) for task prioritization
- **Dashboard**: Comprehensive overview of tasks, statistics, and recent activities

## Technology Stack

- **Backend**: Django 5.2.7
- **Database**: SQLite (development) - easily configurable for PostgreSQL/MySQL in production
- **Authentication**: Django's built-in authentication with custom User model
- **Configuration**: python-decouple for environment variable management

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)
- Virtual environment (recommended)

### Setup Instructions

1. **Clone the repository** (or navigate to the project directory)
   ```bash
   cd c:\Users\VikTOR\PycharmProjects\task_manager_project
   ```

2. **Create and activate a virtual environment**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # On Windows
   # source .venv/bin/activate  # On macOS/Linux
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   - Copy the example environment file:
     ```bash
     copy .env.example .env  # On Windows
     # cp .env.example .env  # On macOS/Linux
     ```
   - Edit `.env` and set your SECRET_KEY:
     ```
     SECRET_KEY=your-secret-key-here
     DEBUG=True
     ```
   - To generate a new secret key, run:
     ```bash
     python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
     ```

5. **Run database migrations**
   ```bash
   python manage.py migrate
   ```

6. **Create a superuser** (for admin access)
   ```bash
   python manage.py createsuperuser
   ```

7. **Run the development server**
   ```bash
   python manage.py runserver
   ```

8. **Access the application**
   - Main application: http://127.0.0.1:8000/
   - Admin interface: http://127.0.0.1:8000/admin/

## Project Structure

```
task_manager_project/
├── task_manager_project/    # Project configuration
│   ├── settings.py          # Django settings
│   ├── urls.py              # Main URL configuration
│   ├── wsgi.py              # WSGI configuration
│   └── asgi.py              # ASGI configuration
├── tasks/                   # Main application
│   ├── models.py            # Database models
│   ├── views.py             # View functions and classes
│   ├── forms.py             # Form definitions
│   ├── urls.py              # URL patterns
│   ├── admin.py             # Admin interface configuration
│   ├── signals.py           # Signal handlers for notifications
│   ├── templates/           # HTML templates
│   ├── static/              # CSS, JavaScript, images
│   └── migrations/          # Database migrations
├── requirements.txt         # Python dependencies
├── .env.example             # Environment variables template
├── manage.py                # Django management script
└── db.sqlite3               # SQLite database (created after migrations)
```

## Database Models

### Core Models
- **Worker**: Extended user model with position and email
- **Position**: Job positions for workers
- **Task**: Main task model with assignees, priority, deadline, and status
- **TaskType**: Categories for tasks
- **Tag**: Labels for task organization
- **Project**: Container for related tasks and teams
- **Team**: Groups of workers assigned to projects

### Supporting Models
- **Comment**: Task comments with author tracking
- **ActivityLog**: Audit trail of all task activities
- **Notification**: User notifications for task events

## Usage

### Creating Tasks
1. Log in to the application
2. Navigate to "Tasks" → "Create Task"
3. Fill in task details (name, description, deadline, priority)
4. Assign workers, select tags, and choose a project
5. Submit to create the task

### Managing Teams
1. Access "Teams" from the navigation menu
2. Create a new team with members
3. Optionally assign the team to a project
4. Team members will have visibility of team tasks

### Viewing Notifications
- Click the notification bell icon in the navigation bar
- View unread notifications
- Click on a notification to mark it as read and navigate to the related task

### Admin Interface
- Access the Django admin at `/admin/`
- Manage all models with advanced filtering and search
- Bulk actions for notifications and activity logs
- Read-only access to activity logs to maintain audit integrity

## Configuration

### Environment Variables
The following environment variables can be configured in the `.env` file:

- `SECRET_KEY`: Django secret key (required)
- `DEBUG`: Debug mode (True/False)
- `ALLOWED_HOSTS`: Comma-separated list of allowed hosts (for production)

### Localization
- Language: Ukrainian (`LANGUAGE_CODE = 'uk'`)
- Timezone: Europe/Kiev (`TIME_ZONE = 'Europe/Kiev'`)

These can be modified in `task_manager_project/settings.py`.

## Development

### Running Tests
```bash
python manage.py test
```

### Code Style
The project follows PEP 8 guidelines. A `.flake8` configuration file is included.

### Making Migrations
After modifying models:
```bash
python manage.py makemigrations
python manage.py migrate
```

## Security Notes

- Never commit the `.env` file to version control
- Use strong SECRET_KEY in production
- Set `DEBUG = False` in production
- Configure `ALLOWED_HOSTS` properly for production deployment
- Use HTTPS in production environments

## License

This project is for educational/internal use.

## Support

For issues or questions, please contact the development team.

## Deployment

https://taskmanager-ze15.onrender.com/ 

user: testuser
password: test1234
