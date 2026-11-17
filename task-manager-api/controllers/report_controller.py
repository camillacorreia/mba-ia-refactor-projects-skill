from controllers.common import get_or_404
from models.user import User
from services import report_service


def summary():
    return report_service.summary()


def user_report(user_id):
    user = get_or_404(User, user_id, 'Usuário não encontrado')
    return report_service.user_report(user)
