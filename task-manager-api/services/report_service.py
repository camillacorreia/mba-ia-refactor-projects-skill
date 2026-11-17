"""Relatórios agregados: consultas com GROUP BY no lugar de uma consulta por item."""
from datetime import timedelta

from database import db
from models.category import Category
from models.task import PRIORITY_LABELS, STATUS_DONE, VALID_STATUSES, Task
from models.user import User
from utils.helpers import calculate_percentage, utc_now

RECENT_ACTIVITY_DAYS = 7


def count_by_status():
    rows = db.session.execute(db.select(Task.status, db.func.count(Task.id)).group_by(Task.status)).all()
    counts = dict(rows)
    return {status: counts.get(status, 0) for status in VALID_STATUSES}


def count_by_priority():
    rows = db.session.execute(db.select(Task.priority, db.func.count(Task.id)).group_by(Task.priority)).all()
    counts = dict(rows)
    return {label: counts.get(priority, 0) for priority, label in PRIORITY_LABELS.items()}


def count_overdue(now=None):
    return db.session.scalar(db.select(db.func.count(Task.id)).where(Task.overdue_filter(now)))


def count_all(model):
    return db.session.scalar(db.select(db.func.count(model.id)))


def task_stats():
    total = count_all(Task)
    by_status = count_by_status()
    return {
        'total': total,
        **by_status,
        'overdue': count_overdue(),
        'completion_rate': calculate_percentage(by_status[STATUS_DONE], total),
    }


def summary():
    now = utc_now()
    since = now - timedelta(days=RECENT_ACTIVITY_DAYS)

    overdue_tasks = db.session.execute(
        db.select(Task).where(Task.overdue_filter(now)).order_by(Task.id)
    ).scalars().all()

    recent_created = db.session.scalar(
        db.select(db.func.count(Task.id)).where(Task.created_at >= since)
    )
    recent_done = db.session.scalar(
        db.select(db.func.count(Task.id)).where(Task.status == STATUS_DONE, Task.updated_at >= since)
    )

    return {
        'generated_at': str(now),
        'overview': {
            'total_tasks': count_all(Task),
            'total_users': count_all(User),
            'total_categories': count_all(Category),
        },
        'tasks_by_status': count_by_status(),
        'tasks_by_priority': count_by_priority(),
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
            'tasks_created_last_7_days': recent_created,
            'tasks_completed_last_7_days': recent_done,
        },
        'user_productivity': user_productivity(),
    }


def user_productivity():
    done_count = db.func.sum(db.case((Task.status == STATUS_DONE, 1), else_=0))
    rows = db.session.execute(
        db.select(User.id, User.name, db.func.count(Task.id), done_count)
        .outerjoin(Task, Task.user_id == User.id)
        .group_by(User.id)
        .order_by(User.id)
    ).all()
    return [
        {
            'user_id': user_id,
            'user_name': user_name,
            'total_tasks': total,
            'completed_tasks': completed or 0,
            'completion_rate': calculate_percentage(completed or 0, total),
        }
        for user_id, user_name, total, completed in rows
    ]


def user_report(user):
    tasks = db.session.execute(db.select(Task).where(Task.user_id == user.id)).scalars().all()
    now = utc_now()
    by_status = {status: 0 for status in VALID_STATUSES}
    for task in tasks:
        if task.status in by_status:
            by_status[task.status] += 1
    total = len(tasks)
    return {
        'user': {'id': user.id, 'name': user.name, 'email': user.email},
        'statistics': {
            'total_tasks': total,
            **by_status,
            'overdue': sum(1 for task in tasks if task.is_overdue(now)),
            'high_priority': sum(1 for task in tasks if task.is_high_priority()),
            'completion_rate': calculate_percentage(by_status[STATUS_DONE], total),
        },
    }
