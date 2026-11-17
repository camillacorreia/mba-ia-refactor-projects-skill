"""Script para popular o banco com dados iniciais"""
from app import app, db
from models.task import Task
from models.user import User
from models.category import Category
from datetime import timedelta

from utils.helpers import utc_now

def seed_data():
    with app.app_context():

        Task.query.delete()
        User.query.delete()
        Category.query.delete()
        db.session.commit()

        admin_user = User()
        admin_user.name = 'João Silva'
        admin_user.email = 'joao@email.com'
        admin_user.set_password('1234')
        admin_user.role = 'admin'
        db.session.add(admin_user)

        regular_user = User()
        regular_user.name = 'Maria Santos'
        regular_user.email = 'maria@email.com'
        regular_user.set_password('abcd')
        regular_user.role = 'user'
        db.session.add(regular_user)

        manager_user = User()
        manager_user.name = 'Pedro Oliveira'
        manager_user.email = 'pedro@email.com'
        manager_user.set_password('pass')
        manager_user.role = 'manager'
        db.session.add(manager_user)

        db.session.commit()

        backend = Category()
        backend.name = 'Backend'
        backend.description = 'Tarefas de backend'
        backend.color = '#3498db'
        db.session.add(backend)

        frontend = Category()
        frontend.name = 'Frontend'
        frontend.description = 'Tarefas de frontend'
        frontend.color = '#2ecc71'
        db.session.add(frontend)

        devops = Category()
        devops.name = 'DevOps'
        devops.description = 'Tarefas de infraestrutura'
        devops.color = '#e74c3c'
        db.session.add(devops)

        bug = Category()
        bug.name = 'Bug'
        bug.description = 'Correção de bugs'
        bug.color = '#e67e22'
        db.session.add(bug)

        db.session.commit()

        tasks_data = [
            {'title': 'Implementar autenticação JWT', 'description': 'Adicionar autenticação real com JWT', 'status': 'pending', 'priority': 1, 'user_id': admin_user.id, 'category_id': backend.id, 'due_date': utc_now() - timedelta(days=3)},
            {'title': 'Criar tela de login', 'description': 'Tela de login responsiva', 'status': 'in_progress', 'priority': 2, 'user_id': regular_user.id, 'category_id': frontend.id, 'due_date': utc_now() + timedelta(days=5)},
            {'title': 'Configurar CI/CD', 'description': 'Pipeline com GitHub Actions', 'status': 'done', 'priority': 2, 'user_id': manager_user.id, 'category_id': devops.id, 'tags': 'devops,ci,github'},
            {'title': 'Corrigir bug no filtro de busca', 'description': 'Filtro não funciona com caracteres especiais', 'status': 'pending', 'priority': 1, 'user_id': admin_user.id, 'category_id': bug.id, 'due_date': utc_now() - timedelta(days=1)},
            {'title': 'Adicionar paginação na API', 'description': 'Endpoints retornam todos os registros', 'status': 'pending', 'priority': 3, 'user_id': admin_user.id, 'category_id': backend.id, 'due_date': utc_now() + timedelta(days=10)},
            {'title': 'Escrever testes unitários', 'description': 'Cobertura mínima de 80%', 'status': 'pending', 'priority': 2, 'user_id': regular_user.id, 'category_id': backend.id},
            {'title': 'Documentar API com Swagger', 'description': 'Gerar documentação automática', 'status': 'cancelled', 'priority': 4, 'user_id': manager_user.id, 'category_id': backend.id},
            {'title': 'Refatorar models', 'description': 'Melhorar organização dos models', 'status': 'in_progress', 'priority': 3, 'user_id': regular_user.id, 'category_id': backend.id, 'tags': 'refactor,tech-debt'},
            {'title': 'Configurar monitoramento', 'description': 'Prometheus + Grafana', 'status': 'pending', 'priority': 4, 'user_id': manager_user.id, 'category_id': devops.id, 'due_date': utc_now() + timedelta(days=20)},
            {'title': 'Melhorar validações de input', 'description': 'Usar marshmallow ou pydantic', 'status': 'pending', 'priority': 3, 'user_id': admin_user.id, 'category_id': backend.id, 'tags': 'improvement,validation'},
        ]

        for task_data in tasks_data:
            task = Task()
            task.title = task_data['title']
            task.description = task_data['description']
            task.status = task_data['status']
            task.priority = task_data['priority']
            task.user_id = task_data['user_id']
            task.category_id = task_data['category_id']
            if 'due_date' in task_data:
                task.due_date = task_data['due_date']
            if 'tags' in task_data:
                task.tags = task_data['tags']
            db.session.add(task)

        db.session.commit()
        print("Seed concluído com sucesso!")
        print(f"  {User.query.count()} usuários")
        print(f"  {Category.query.count()} categorias")
        print(f"  {Task.query.count()} tasks")

if __name__ == '__main__':
    seed_data()
