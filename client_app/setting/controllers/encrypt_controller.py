from flask import Blueprint, request, jsonify, send_file
from models.roi_handler import ROIHandler
import os
import json
from werkzeug.utils import secure_filename
import tempfile
import traceback
import base64
import io
from PIL import Image
import cv2

encryption_bp = Blueprint('encryption', __name__)
roi_handler = ROIHandler()

@encryption_bp.route('/convert-pdf', methods=['POST'])
def convert_pdf():
    """
    PDF를 이미지로 변환하는 엔드포인트
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
            
        # 2. 임시 파일 저장 (한글 주석: PDF 확장자 보장)
        temp_dir = tempfile.mkdtemp()
        
        # 파일명에서 확장자 보장
        original_filename = secure_filename(pdf_file.filename) or 'document'
        name, ext = os.path.splitext(original_filename)
        if not ext or ext.lower() != '.pdf':
            ext = '.pdf'
        
        safe_filename = f"{name}{ext}"
        pdf_path = os.path.join(temp_dir, safe_filename)
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

@encryption_bp.route('/encrypt', methods=['POST'])
def encrypt_file():
    """
    파일 암호화 엔드포인트
    - 이미지 또는 PDF 파일을 받아서 암호화
    - 여러 ROI 영역을 암호화하고 결과물 반환
    """
    temp_dir = None
    file_path = None
    encrypted_path = None
    
    try:
        # 1. 파일 및 데이터 검증
        if 'file' not in request.files:
            return jsonify({'error': '파일이 없습니다.'}), 400
        
        file = request.files['file']
        if not file.filename:
            return jsonify({'error': '파일이 선택되지 않았습니다.'}), 400
            
        try:
            roi_list = json.loads(request.form.get('roiList', '[]'))
        except json.JSONDecodeError:
            return jsonify({'error': 'ROI 데이터가 올바르지 않습니다.'}), 400
            
        if 'recipients' not in request.form:
            return jsonify({'error': '수신자 목록이 없습니다.'}), 400
            
        recipients = json.loads(request.form['recipients'])
        file_type = request.form.get('fileType', '')
        
        # 수신자 목록 확인됨
        # 파일 타입 확인됨
        
        if not recipients:
            return jsonify({'error': '수신자 이메일이 필요합니다.'}), 400
            
        if not roi_list:
            return jsonify({'error': '암호화할 영역이 없습니다.'}), 400
        
        # 2. 임시 파일 저장 (한글 주석: 확장자 보장)
        temp_dir = tempfile.mkdtemp()
        
        # 원본 파일명에서 확장자 추출
        original_filename = secure_filename(file.filename) or 'file'
        name, ext = os.path.splitext(original_filename)
        
        # 확장자가 없으면 MIME 타입으로 추정
        if not ext:
            if file_type == 'application/pdf':
                ext = '.pdf'
            elif file_type.startswith('image/'):
                if 'png' in file_type:
                    ext = '.png'
                elif 'jpeg' in file_type or 'jpg' in file_type:
                    ext = '.jpg'
                else:
                    ext = '.jpg'  # 기본값
            else:
                ext = '.jpg'  # 기본값
        
        # 확장자가 포함된 파일명으로 저장
        safe_filename = f"{name}{ext}"
        file_path = os.path.join(temp_dir, safe_filename)
        file.save(file_path)
        
        # 파일 저장됨
        
        try:
            # 3. ROI 암호화 수행
            if file_type == 'application/pdf':
                # PDF인 경우: 품질 스케일을 받아서 이미지처리 방식으로 암호화
                quality_scale = float(request.form.get('qualityScale', '1.7'))  # 품질 스케일 (1.0~2.0, 기본: 1.7)
                # PDF 이미지처리 방식 암호화 시작
                
                encrypted_path = roi_handler.encrypt_pdf_roi(
                    file_path,
                    roi_list,  # 페이지별 ROI 데이터 구조
                    recipients,
                    quality_scale  # 품질 스케일 전달
                )
                
                # PDF 파일로 반환
                return send_file(
                    encrypted_path,
                    mimetype='application/pdf',
                    as_attachment=True,
                    download_name='encrypted_document.pdf'
                )
            else:
                # 이미지 파일 암호화 (ROI 좌표를 int로 변환)
                for roi in roi_list:
                    roi['x'] = int(roi['x'])
                    roi['y'] = int(roi['y'])
                    roi['width'] = int(roi['width'])
                    roi['height'] = int(roi['height'])

                encrypted_path = roi_handler.encrypt_multiple_roi(
                    file_path, 
                    roi_list,
                    recipients
                )

                # 이미지 파일로 반환
                return send_file(
                    encrypted_path,
                    mimetype='image/jpeg',
                    as_attachment=True,
                    download_name='encrypted_image.jpg'
                )
            
        except Exception as e:
            # 암호화 중 오류 발생
            raise
            
    except Exception as e:
        # 처리 중 오류 발생
        return jsonify({
            'error': str(e),
            'details': traceback.format_exc()
        }), 500
        
    finally:
        # 임시 파일 정리
        try:
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
            if encrypted_path and os.path.exists(encrypted_path):
                os.remove(encrypted_path)
            if temp_dir and os.path.exists(temp_dir):
                os.rmdir(temp_dir)
        except Exception as e:
            # 임시 파일 정리 중 오류 발생
            pass
