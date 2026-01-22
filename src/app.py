# src/app.py
from flask import Flask
from web import web_bp
from routes import api_bp

def create_app():
    app = Flask(__name__)
    app.secret_key = 'sua-chave-secreta-aqui'  # Necessário para flash messages
    
    # Registra blueprints
    app.register_blueprint(web_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)