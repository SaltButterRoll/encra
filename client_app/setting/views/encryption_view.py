from flask import Blueprint, render_template, redirect
from models.auth_model import AuthModel

encryption_view_bp = Blueprint('encryption_view', __name__)
auth_model = AuthModel()

@encryption_view_bp.route('/encrypt', methods=['GET'])
def show_encrypt_page():
    # ✅ 개인키 존재 여부 확인
    if not auth_model.load_private_key():
        return redirect('/')
    return render_template('encrypt.html')
