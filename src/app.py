# src/app.py
from flask import Flask
from routes import api_bp  # ❌ cuidado: era "api_bp", não "api_protobuf"
from web import web_bp           # ✅ sem "src."

def create_app():
    app = Flask(__name__, template_folder='../templates')
    app.register_blueprint(web_bp)
    app.register_blueprint(api_bp, url_prefix='/api')  # ← nome correto da variável
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)