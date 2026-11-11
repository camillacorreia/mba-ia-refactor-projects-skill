from services import report_service
from models.user import User
from utils.errors import NotFoundError


def summary_report():
    return report_service.build_summary(), 200


def user_report(user_id):
    user = User.find(user_id)
    if not user:
        raise NotFoundError('Usuário não encontrado')
    return report_service.build_user_report(user), 200
