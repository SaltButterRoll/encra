from flask import Blueprint, render_template, redirect
from models.auth_model import AuthModel

decryption_view_bp = Blueprint('decryption_view', __name__)
auth_model = AuthModel()

@decryption_view_bp.route('/decrypt', methods=['GET'])
def show_decrypt_page():
    # ✅ 개인키 존재 여부 확인
    if not auth_model.load_private_key():
        return redirect('/')
    return render_template('decrypt.html')