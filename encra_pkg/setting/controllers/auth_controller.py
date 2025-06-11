from flask import Blueprint, request, current_app
from flask_mail import Message, Mail
from itsdangerous import URLSafeTimedSerializer
import jwt
from datetime import datetime, timedelta
from typing import Tuple, Dict
from models.email_manager import EmailManager
from models.pkg_model import extract_user_private_key, get_public_params
from functools import wraps
import os
auth_bp = Blueprint('auth', __name__)
email_manager = EmailManager()

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return {'error': '인증 토큰이 필요합니다.'}, 401
            
        try:
            token = token.split(' ')[1]  # Bearer 제거
            data = jwt.decode(
                token,
                current_app.config['SECRET_KEY'],
                algorithms=['HS256']
            )
            return f(data['email'], *args, **kwargs)
        except jwt.ExpiredSignatureError:
            return {'error': '만료된 토큰입니다.'}, 401
        except (jwt.InvalidTokenError, IndexError):
            return {'error': '유효하지 않은 토큰입니다.'}, 401
            
    return decorated

def generate_confirmation_token(email: str) -> str:
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return serializer.dumps(email, salt='email-confirm')

def verify_confirmation_token(token: str, expiration: int = 3600) -> str:
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return serializer.loads(token, salt='email-confirm', max_age=expiration)

@auth_bp.route('/auth/request', methods=['POST'])
def request_verification() -> Tuple[Dict, int]:
    try:
        email = request.json.get('email')
        if not email:
            return {'error': '이메일 주소가 필요합니다.'}, 400
            
        try:
            email_manager.register_email(email)
        except ValueError as e:
            return {'error': str(e)}, 400
            
        token = generate_confirmation_token(email)
        
        client_app_url = request.json.get('client_app_url')
        confirm_url = f"{client_app_url}/auth/confirm/{token}"

        mail = Mail(current_app)
        msg = Message('[Encra] 이메일 인증',
                     sender=current_app.config['MAIL_USERNAME'],
                     recipients=[email])
        msg.html = f'''
        <div style="max-width:480px;margin:40px auto;padding:32px 24px;background:#fff;border-radius:12px;box-shadow:0 4px 24px rgba(0,0,0,0.08);font-family:'Segoe UI',Arial,sans-serif;">
          <div style="text-align:center;margin-bottom:24px;">
            
            <h2 style="margin:0;color:#2d3748;font-weight:700;">Encra 이메일 인증</h2>
          </div>
          <p style="font-size:16px;color:#444;margin-bottom:24px;">
            안녕하세요,<br>
            Encra 서비스를 이용해주셔서 감사합니다.<br>
            아래 버튼을 클릭하여 이메일 인증을 완료해주세요.
          </p>
          <div style="text-align:center;margin-bottom:32px;">
            <a href="{confirm_url}" style="display:inline-block;padding:14px 32px;background:#4CAF50;color:#fff;font-size:18px;font-weight:600;border-radius:6px;text-decoration:none;box-shadow:0 2px 8px rgba(76,175,80,0.15);transition:background 0.2s;">
              이메일 인증하기
            </a>
          </div>
          <p style="font-size:13px;color:#888;text-align:center;margin-bottom:0;">
            인증 링크는 1시간 동안만 유효합니다.<br>
            만약 본인이 요청하지 않았다면 이 메일을 무시해주세요.
          </p>
          <hr style="margin:32px 0 16px 0;border:none;border-top:1px solid #eee;">
          <div style="font-size:12px;color:#aaa;text-align:center;">
            문의: <a href="mailto:encra2025@gmail.com" style="color:#4CAF50;text-decoration:none;">encra2025@gmail.com</a><br>
            &copy; 2024 Encra. All rights reserved.
          </div>
        </div>
        '''
        mail.send(msg)
        
        return {'message': '인증 메일이 발송되었습니다.'}, 200
        
    except Exception as e:
        return {'error': '인증 메일 발송 중 오류가 발생했습니다.'}, 500

@auth_bp.route('/auth/confirm/<token>')
def confirm_email(token: str) -> Tuple[Dict, int]:
    try:
        email = verify_confirmation_token(token)
        
        email_manager.verify_email(email)
        
        jwt_token = jwt.encode(
            {
                'email': email,
                'exp': datetime.utcnow() + timedelta(minutes=5)
            },
            current_app.config['SECRET_KEY'],
            algorithm='HS256'
        )

        if request.args.get('source') == 'email':
            return {
                'message': '이메일이 성공적으로 인증되었습니다.',
                'redirect_url': '/?auth=success'
            }, 200
        
        return {
            'message': '이메일이 성공적으로 인증되었습니다.',
            'token': jwt_token
        }, 200
        
    except Exception as e:
        return {'error': '유효하지 않거나 만료된 인증 링크입니다.'}, 400

@auth_bp.route('/auth/generate-key', methods=['POST'])
@token_required
def generate_private_key(email: str) -> Tuple[Dict, int]:
    try:
        if not email_manager.is_verified(email):
            return {'error': '인증되지 않은 이메일입니다.'}, 403
        private_key = extract_user_private_key(email)

        public_params = get_public_params()
        g = public_params['g']
        g_alpha = public_params['g^alpha']

        return {
            'message': '개인키가 발급되었습니다.',
            'private_key': private_key.hex(),
            'g': g.hex(),
            'g^alpha': g_alpha.hex()
        }, 200

    except Exception as e:
        return {'error': '개인키 발급 중 오류가 발생했습니다.'}, 500
