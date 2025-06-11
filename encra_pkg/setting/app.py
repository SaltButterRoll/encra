from flask import Flask
from controllers.auth_controller import auth_bp
from models.pkg_model import generate_master_keys, load_master_keys
from flask_mail import Mail
from dotenv import load_dotenv
import os

load_dotenv()

def create_app():
    app = Flask(__name__)

    app.config.update(
        SECRET_KEY=os.getenv('SECRET_KEY'),
        MAIL_SERVER='smtp.gmail.com',
        MAIL_PORT=587,
        MAIL_USE_TLS=True,
        MAIL_USERNAME=os.getenv('MAIL_USERNAME'),
        MAIL_PASSWORD=os.getenv('MAIL_PASSWORD'),
        MAIL_DEFAULT_SENDER=os.getenv('MAIL_USERNAME')
    )

    mail = Mail(app)

    try:
        if not os.path.exists(os.path.join("pkg_keys", "ibe_ctx.json")):
            generate_master_keys()
        else:
            load_master_keys()
    except Exception as e:
        raise

    app.register_blueprint(auth_bp)

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=6543)
