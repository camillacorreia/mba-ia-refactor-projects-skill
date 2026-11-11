"""Relatórios que agregam tasks, usuários e categorias."""
from datetime import timedelta

from database import db
from models.category import Category
from models.task import (
    HIGH_PRIORITY_MAX,
    PRIORITY_LABELS,
    STATUS_CANCELLED,
    STATUS_DONE,
    STATUS_IN_PROGRESS,
    STATUS_PENDING,
    Task,
)
from models.user import User
from utils.helpers import calculate_percentage, utcnow

RECENT_ACTIVITY_DAYS = 7


def _user_productivity():
    done_flag = db.case((Task.status == STATUS_DONE, 1), else_=0)
    rows = db.session.execute(
        db.select(Task.user_id, db.func.count(Task.id), db.func.sum(done_flag)).group_by(Task.user_id)
    ).all()
    totals = {user_id: (total, completed or 0) for user_id, total, completed in rows}

    stats = []
    for user in User.list_all():
        total, completed = totals.get(user.id, (0, 0))
        stats.append({
            'user_id': user.id,
            'user_name': user.name,
            'total_tasks': total,
            'completed_tasks': completed,
            'completion_rate': calculate_percentage(completed, total),
        })
    return stats


def build_summary():
    now = utcnow()
    since = now - timedelta(days=RECENT_ACTIVITY_DAYS)
    by_status = Task.count_by(Task.status)
    by_priority = Task.count_by(Task.priority)
    overdue_tasks = Task.list_overdue(now)

    recent_created = db.session.execute(
        db.select(db.func.count(Task.id)).where(Task.created_at >= since)
    ).scalar_one()
    recent_done = db.session.execute(
        db.select(db.func.count(Task.id)).where(Task.status == STATUS_DONE, Task.updated_at >= since)
    ).scalar_one()

    return {
        'generated_at': str(now),
        'overview': {
            'total_tasks': Task.count(),
            'total_users': User.count(),
            'total_categories': Category.count(),
        },
        'tasks_by_status': {
            status: by_status.get(status, 0)
            for status in (STATUS_PENDING, STATUS_IN_PROGRESS, STATUS_DONE, STATUS_CANCELLED)
        },
        'tasks_by_priority': {label: by_priority.get(level, 0) for level, label in PRIORITY_LABELS.items()},
        'overdue': {
            'count': len(overdue_tasks),
            'tasks': [
                {
                    'id': task.id,
                    'title': task.title,
                    'due_date': str(task.due_date),
                    'days_overdue': (now - task.due_date).days,
                }
                for task in overdue_tasks
            ],
        },
        'recent_activity': {
            f'tasks_created_last_{RECENT_ACTIVITY_DAYS}_days': recent_created,
            f'tasks_completed_last_{RECENT_ACTIVITY_DAYS}_days': recent_done,
        },
        'user_productivity': _user_productivity(),
    }


def build_user_report(user):
    tasks = Task.list_by_user(user.id)
    now = utcnow()
    counts = {status: 0 for status in (STATUS_DONE, STATUS_PENDING, STATUS_IN_PROGRESS, STATUS_CANCELLED)}
    for task in tasks:
        if task.status in counts:
            counts[task.status] += 1

    return {
        'user': {'id': user.id, 'name': user.name, 'email': user.email},
        'statistics': {
            'total_tasks': len(tasks),
            **counts,
            'overdue': sum(1 for task in tasks if task.is_overdue(now)),
            'high_priority': sum(1 for task in tasks if task.priority <= HIGH_PRIORITY_MAX),
            'completion_rate': calculate_percentage(counts[STATUS_DONE], len(tasks)),
        },
    }
