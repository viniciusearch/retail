# src/app.py
from flask import Flask
from flask_login import LoginManager
from web import web_bp
from routes import api_bp

def create_app():
    app = Flask(__name__)
    app.secret_key = 'sua-chave-secreta-muito-segura-aqui-123456789'
    
    # Inicializa Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'web.login'
    login_manager.login_message = "Por favor, faça login para acessar esta página."
    login_manager.login_message_category = "info"
    
    # Função para carregar usuário
    from web import get_db_connection
    @login_manager.user_loader
    def load_user(user_id):
        from flask_login import UserMixin
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
                class User(UserMixin):
                    def __init__(self, id, nome_completo, email, perfil, status):
                        self.id = id
                        self.nome_completo = nome_completo
                        self.email = email
                        self.perfil = perfil
                        self.status = status
                
                return User(
                    id=user_data['id'],
                    nome_completo=user_data['nome_completo'],
                    email=user_data['email'],
                    perfil=user_data['perfil'],
                    status=user_data['status']
                )
        return None
    
    # Registra blueprints
    app.register_blueprint(web_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)