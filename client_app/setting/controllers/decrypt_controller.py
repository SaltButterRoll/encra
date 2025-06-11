from flask import Blueprint, request, jsonify, send_file
from models.roi_handler import ROIHandler
import os
from werkzeug.utils import secure_filename
import tempfile
import cv2
from models.auth_model import AuthModel
from models.ibe_constants import PAIRING_GROUP
import shutil
import traceback
import base64
import io
from PIL import Image

decryption_bp = Blueprint('decryption', __name__)
roi_handler = ROIHandler()
auth_model = AuthModel()

@decryption_bp.route('/convert-pdf', methods=['POST'])
def convert_pdf():
    """
    PDF를 이미지로 변환하는 엔드포인트 (한글 주석: decrypt.html에서도 PDF 미리보기 지원)
    - PDF 파일을 받아서 각 페이지를 이미지로 변환
    - 변환된 이미지들을 base64로 인코딩하여 반환
    """
    try:
        # 1. 파일 검증
        if 'file' not in request.files:
            return jsonify({'error': 'PDF 파일이 없습니다.'}), 400
        
        pdf_file = request.files['file']
        if not pdf_file.filename:
            return jsonify({'error': '파일이 선택되지 않았습니다.'}), 400
            
        # 2. 임시 파일 저장
        temp_dir = tempfile.mkdtemp()
        pdf_path = os.path.join(temp_dir, secure_filename(pdf_file.filename))
        pdf_file.save(pdf_path)
        
        # 3. PDF를 이미지로 변환
        images = roi_handler.pdf_to_images(pdf_path)
        
        # 4. 이미지를 base64로 인코딩
        encoded_pages = []
        for img in images:
            # OpenCV BGR -> RGB 변환
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            # PIL Image로 변환
            pil_img = Image.fromarray(img_rgb)
            # 메모리에 이미지 저장
            img_byte_arr = io.BytesIO()
            pil_img.save(img_byte_arr, format='PNG')
            img_byte_arr = img_byte_arr.getvalue()
            # base64로 인코딩
            encoded = base64.b64encode(img_byte_arr).decode('utf-8')
            encoded_pages.append(f'data:image/png;base64,{encoded}')
        
        return jsonify({'pages': encoded_pages})
        
    except Exception as e:
        # PDF 변환 중 오류 발생
        return jsonify({
            'error': str(e),
            'details': traceback.format_exc()
        }), 500
        
    finally:
        # 임시 파일 정리
        try:
            if pdf_path and os.path.exists(pdf_path):
                os.remove(pdf_path)
            if temp_dir and os.path.exists(temp_dir):
                os.rmdir(temp_dir)
        except Exception as e:
            # 임시 파일 정리 중 오류 발생
            pass

@decryption_bp.route('/decrypt', methods=['POST'])
def decrypt_image():
    try:
        # 1. 파일 검증
        if 'image' not in request.files:
            return jsonify({'error': '파일이 없습니다.'}), 400
        
        file = request.files['image']
        if not file.filename:
            return jsonify({'error': '파일이 선택되지 않았습니다.'}), 400
        
        # 파일 형식 확인 (한글 주석: PDF 또는 이미지 파일 지원)
        file_type = file.content_type
        is_pdf = file_type == 'application/pdf'
        
        # 2. 임시 파일 저장
        temp_dir = tempfile.mkdtemp()
        file_path = os.path.join(temp_dir, secure_filename(file.filename))
        file.save(file_path)
        
        try:
            # 3. 현재 사용자 이메일 가져오기
            current_user_email = auth_model.get_current_user_email()
            if not current_user_email:
                return jsonify({'error': '사용자 정보를 찾을 수 없습니다. 이메일 인증을 진행해주세요.'}), 404

            # 4. IBE 복호화를 위한 개인키 로드
            private_key = auth_model.load_private_key()
            if not private_key:
                return jsonify({'error': '개인키를 찾을 수 없습니다. 이메일 인증을 다시 진행해주세요.'}), 404
            
            # 5. 파일 형식에 따른 복호화 수행
            if is_pdf:
                # PDF 복호화 (한글 주석: PDF 메타데이터에서 암호화 정보 추출 및 복원)
                try:
                    # 원본 파일 크기 기록
                    original_size = os.path.getsize(file_path)
                    
                    decrypted_path = roi_handler.decrypt_pdf_roi(
                        pdf_path=file_path,
                        private_key=private_key,
                        pairing_group=PAIRING_GROUP,
                        user_email=current_user_email
                    )
                    
                    # PDF 파일 반환
                    return send_file(
                        decrypted_path,
                        mimetype='application/pdf',
                        as_attachment=True,
                        download_name='decrypted_document.pdf'
                    )
                    
                except Exception as e:
                    raise ValueError(f"{str(e)}")
            else:
                # 이미지 복호화 (한글 주석: 단일/다중 ROI 자동 감지 및 처리)
                try:
                    # 원본 파일 크기 기록
                    original_size = os.path.getsize(file_path)
                    
                    # 먼저 다중 ROI 복호화 시도 (한글 주석: 현재 암호화 방식이 다중 ROI이므로)
                    try:
                        decrypted_image = roi_handler.decrypt_multiple_roi(
                            image_path=file_path,
                            private_key=private_key,
                            pairing_group=PAIRING_GROUP,
                            user_email=current_user_email
                        )
                    except Exception as multi_error:
                        # 다중 ROI 실패 시 단일 ROI 복호화 시도 (한글 주석: 하위 호환성)
                        decrypted_image = roi_handler.decrypt_roi(
                            image_path=file_path,
                            private_key=private_key,
                            pairing_group=PAIRING_GROUP,
                            user_email=current_user_email
                        )
                        
                except Exception as e:
                    raise ValueError(f"\n{str(e)}")
                
                # 6. 복호화된 이미지 저장
                output_path = os.path.join(temp_dir, 'decrypted_image.jpg')
                success = cv2.imwrite(output_path, decrypted_image, [cv2.IMWRITE_JPEG_QUALITY, 95])
                
                if not success:
                    raise ValueError("복호화된 이미지 저장에 실패했습니다.")

                # 7. 복호화된 이미지 반환
                return send_file(
                    output_path,
                    mimetype='image/jpeg',
                    as_attachment=True,
                    download_name='decrypted_image.jpg'
                )
            
        finally:
            # 임시 파일 정리
            if os.path.exists(file_path):
                os.remove(file_path)
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir) 
                
    except Exception as e:
        return jsonify({'error': str(e)}), 500
