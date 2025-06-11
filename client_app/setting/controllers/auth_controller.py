from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models.auth_model import AuthModel
import re

auth_bp = Blueprint('auth', __name__)
auth_model = AuthModel()

def is_valid_email(email: str) -> bool:
    """이메일 형식 검증"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

@auth_bp.route('/auth/request', methods=['GET', 'POST'])
def request_auth():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        if not email:
            flash('이메일 주소를 입력해주세요.', 'error')
            return redirect(url_for('auth.request_auth'))
        
        if not is_valid_email(email):
            flash('유효하지 않은 이메일 주소입니다.', 'error')
            return redirect(url_for('auth.request_auth'))
        
        success, message = auth_model.request_email_auth(email)
        if success:
            flash(message, 'success')
            session['pending_email'] = email
            return redirect(url_for('index', email_sent='true'))
        else:
            flash(message, 'error')
            return redirect(url_for('auth.request_auth'))
    
    return render_template('auth/request.html')

@auth_bp.route('/auth/confirm/<token>')
def confirm_auth(token):
    success, message, jwt_token = auth_model.confirm_email_auth(token)
    if success and jwt_token:
        session['jwt_token'] = jwt_token
        success, key_message = auth_model.request_private_key(jwt_token)
        if success:
            flash('인증이 완료되고 개인키가 발급되었습니다.', 'success')
        else:
            flash(f'인증은 완료되었으나 개인키 발급에 실패했습니다: {key_message}', 'error')
    else:
        flash(message, 'error')
    
    return redirect(url_for('index'))

@auth_bp.route('/auth/check')
def check_auth():
    """현재 인증 상태 확인"""
    has_key = auth_model.load_private_key() is not None
    email = auth_model.get_current_user_email()
    return {'has_key': has_key, 'email': email} 