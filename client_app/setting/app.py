from flask import Flask, render_template
from controllers.encrypt_controller import encryption_bp
from controllers.decrypt_controller import decryption_bp
from controllers.auth_controller import auth_bp
from views.encryption_view import encryption_view_bp
from views.decryption_view import decryption_view_bp
from dotenv import load_dotenv
import os

# app.py
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'setting', '.env'))

def create_app():
    app = Flask(__name__)

    # 기본값 제공 + .env 오버라이드
    app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")
    if not app.config['SECRET_KEY']:
        raise ValueError("SECRET_KEY 환경 변수가 설정되지 않았습니다.")

    # 블루프린트 등록
    app.register_blueprint(auth_bp)
    app.register_blueprint(encryption_bp)
    app.register_blueprint(decryption_bp)
    app.register_blueprint(encryption_view_bp)
    app.register_blueprint(decryption_view_bp)

    @app.route('/')
    def index():
        return render_template("index.html")

    return app

if __name__ == '__main__':
    app = create_app()
    port = int(os.getenv('PORT', 5000))  # 기본값 5000
    app.run(host='0.0.0.0', port=port)
