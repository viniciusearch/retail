# src/user.py
from flask_login import UserMixin
from models import get_db_connection

class User(UserMixin):
    def __init__(self, id, nome_completo, email, perfil, status):
        self.id = id
        self.nome_completo = nome_completo
        self.email = email
        self.perfil = perfil
        self.status = status
    
    @staticmethod
    def get(user_id):
        """Busca usuário pelo ID"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT u.id, u.nome_completo, u.email, p.nome as perfil, u.status
                FROM usuarios u
                JOIN perfis_usuario p ON u.perfil_id = p.id
                WHERE u.id = ?
            """, (user_id,))
            user_data = cursor.fetchone()
            
            if user_data:
                return User(
                    id=user_data['id'],
                    nome_completo=user_data['nome_completo'],
                    email=user_data['email'],
                    perfil=user_data['perfil'],
                    status=user_data['status']
                )
        return None