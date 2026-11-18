# src/app.py
from flask import Flask
from flask_login import LoginManager
from web import web_bp
from routes import api_bp
from models import get_db_connection
from user import User

def create_app():
    app = Flask(__name__)
    app.secret_key = 'sua-chave-secreta-muito-segura-aqui-123456789'
    
    # Inicializa Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'web.login'
    login_manager.login_message = "Por favor, faça login para acessar esta página."
    login_manager.login_message_category = "info"
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.get(user_id)
    
    # Registra blueprints
    app.register_blueprint(web_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)