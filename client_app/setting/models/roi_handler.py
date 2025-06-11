from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from PIL import Image
import json
import os
import cv2
import numpy as np
import zlib
import io
from models.ibe_model import encrypt_aes_key, decrypt_aes_key, get_user_email_from_keys
from typing import Tuple, List, Union
import fitz  # PyMuPDF
import tempfile
import base64

class ROIHandler:
    def __init__(self):
        # 파일 크기 제한 설정
        self.MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
        
        self.PDF_FRONTEND_SCALE = 1.0    # 프론트엔드 PDF 렌더링 스케일 (1.0 = 원본 크기)  
        self.PDF_PROCESSING_SCALE = 1.0  # 이미지처리 방식 PDF 스케일 (1.0 = 원본 크기)
        
        # 지원 포맷 설정
        self.SUPPORTED_FORMATS = ['.jpg', '.jpeg', '.png', '.pdf']
        # 암호화 관련 상수
        self.AES_KEY_SIZE = 32  # AES-256
        self.IBE_U_SIZE = 128   # IBE U 값 크기
        self.MIN_ENCRYPTED_SIZE = 32  # 최소 암호화 데이터 크기

    def validate_file(self, file_path: str) -> None:
        if not os.path.exists(file_path):
            raise ValueError(f"파일이 존재하지 않습니다: {file_path}")
        
        if os.path.getsize(file_path) > self.MAX_FILE_SIZE:
            raise ValueError(f"파일 크기가 제한({self.MAX_FILE_SIZE/1024/1024:.1f}MB)을 초과합니다.")
        
        # 확장자 확인
        ext = os.path.splitext(file_path)[1].lower()
        
        # 확장자가 없거나 지원하지 않는 확장자인 경우 파일 내용으로 판단
        if not ext or ext not in self.SUPPORTED_FORMATS:
            try:
                # 파일 헤더로 실제 형식 확인
                with open(file_path, 'rb') as f:
                    header = f.read(16)
                
                # PDF 파일 확인
                if header.startswith(b'%PDF'):
                    if '.pdf' not in self.SUPPORTED_FORMATS:
                        raise ValueError(f"지원하지 않는 파일 형식입니다. 지원 형식: {', '.join(self.SUPPORTED_FORMATS)}")
                # PNG 파일 확인
                elif header.startswith(b'\x89PNG\r\n\x1a\n'):
                    if '.png' not in self.SUPPORTED_FORMATS:
                        raise ValueError(f"지원하지 않는 파일 형식입니다. 지원 형식: {', '.join(self.SUPPORTED_FORMATS)}")
                # JPEG 파일 확인
                elif header.startswith(b'\xff\xd8\xff'):
                    if '.jpg' not in self.SUPPORTED_FORMATS and '.jpeg' not in self.SUPPORTED_FORMATS:
                        raise ValueError(f"지원하지 않는 파일 형식입니다. 지원 형식: {', '.join(self.SUPPORTED_FORMATS)}")
                else:
                    raise ValueError(f"지원하지 않는 파일 형식입니다. 지원 형식: {', '.join(self.SUPPORTED_FORMATS)}")
                    
            except IOError:
                raise ValueError(f"파일을 읽을 수 없습니다: {file_path}")
        
        # 확장자가 있고 지원하는 형식인 경우 통과
        # 파일 검증 통과

    def validate_image(self, image_path):
        if not os.path.exists(image_path):
            raise ValueError(f"이미지 파일이 존재하지 않습니다: {image_path}")
        
        if os.path.getsize(image_path) > self.MAX_FILE_SIZE:
            raise ValueError(f"파일 크기가 제한({self.MAX_FILE_SIZE/1024/1024:.1f}MB)을 초과합니다.")
        
        ext = os.path.splitext(image_path)[1].lower()
        if ext not in self.SUPPORTED_FORMATS:
            raise ValueError(f"지원하지 않는 파일 형식입니다. 지원 형식: {', '.join(self.SUPPORTED_FORMATS)}")

    def validate_roi_coords(self, image_shape, roi_coords):
        x1, y1, x2, y2 = roi_coords
        h, w = image_shape[:2]
        
        # 좌표가 음수인 경우 0으로 조정
        x1 = max(0, x1)
        y1 = max(0, y1)
        
        # 좌표가 이미지 크기를 초과하는 경우 이미지 크기로 조정
        x2 = min(w, x2)
        y2 = min(h, y2)
        
        if x1 >= x2 or y1 >= y2:
            raise ValueError(f"잘못된 ROI 좌표입니다: {roi_coords}")
            
        return (x1, y1, x2, y2)

    def apply_mask(self, image, roi_rect, mask_type="Pattern"):
        # ROI 좌표 검증 및 조정
        roi_rect = self.validate_roi_coords(image.shape, roi_rect)
        x1, y1, x2, y2 = roi_rect
        w, h = x2 - x1, y2 - y1

        if mask_type == "Solid":
            # 고정된 색상 설정 (한글 주석: 어두운 회색 배경에 흰색 텍스트로 세련된 마스킹 효과)
            bg_color = (64, 64, 64)      # 어두운 회색 배경
            border_color = (128, 128, 128)  # 중간 회색 테두리
            text_color = (255, 255, 255)    # 흰색 텍스트

            image[y1:y2, x1:x2] = bg_color

            border_thickness = 2
            image[y1:y1+border_thickness, x1:x2] = border_color  # top
            image[y2-border_thickness:y2, x1:x2] = border_color  # bottom
            image[y1:y2, x1:x1+border_thickness] = border_color  # left
            image[y1:y2, x2-border_thickness:x2] = border_color  # right

            # ROI 크기에 따른 적응형 텍스트 표시 (한글 주석: 작은 ROI에서도 안전한 텍스트 처리)
            min_roi_size_for_text = 40  # 최소 가로 또는 세로 크기 (픽셀) - 더 작은 ROI도 지원
            
            if min(w, h) >= min_roi_size_for_text:
                # 텍스트 크기를 ROI 크기에 정확히 맞추기 (한글 주석: ROI 경계 벗어남 방지)
                font = cv2.FONT_HERSHEY_SIMPLEX
                
                # 텍스트 후보 목록 (크기 순으로 시도)
                text_candidates = ["ENCRYPTED", "ENC"]
                
                best_text = None
                best_font_scale = 0
                best_text_size = (0, 0)
                
                # ROI 크기에 맞는 텍스트와 폰트 크기 찾기
                for text_candidate in text_candidates:
                    # 폰트 크기를 ROI 크기의 비율로 계산 (더 보수적으로)
                    for scale_factor in [0.3, 0.25, 0.2, 0.15, 0.1, 0.08, 0.06]:
                        font_scale = min(w, h) * scale_factor / 10  # 더 작게 계산
                        font_scale = max(0.3, font_scale)  # 최소 크기 제한
                        
                        thickness = max(1, int(font_scale * 2))  # 폰트 크기에 비례한 두께
                        text_size = cv2.getTextSize(text_candidate, font, font_scale, thickness)[0]
                        
                        # 텍스트가 ROI 크기의 80% 이내에 들어가는지 확인 (여백 확보)
                        if (text_size[0] <= w * 0.8 and text_size[1] <= h * 0.8):
                            best_text = text_candidate
                            best_font_scale = font_scale
                            best_text_size = text_size
                            break
                    
                    if best_text:
                        break
                
                # 적합한 텍스트를 찾은 경우에만 표시
                if best_text:
                    thickness = max(1, int(best_font_scale * 2))
                    
                    # 텍스트 위치 계산 (중앙 정렬, 여백 확보)
                    text_x = x1 + (w - best_text_size[0]) // 2
                    text_y = y1 + (h + best_text_size[1]) // 2
                    
                    # 텍스트가 ROI 경계를 벗어나지 않도록 최종 검증 및 보정
                    text_x = max(x1 + 2, min(text_x, x2 - best_text_size[0] - 2))  # 2픽셀 여백
                    text_y = max(y1 + best_text_size[1] + 2, min(text_y, y2 - 2))  # 2픽셀 여백
                    
                    # ROI 영역에만 클리핑하여 텍스트 그리기 (한글 주석: 경계 벗어남 완전 방지)
                    # 임시 이미지 생성하여 텍스트 그리기
                    temp_roi = image[y1:y2, x1:x2].copy()
                    
                    # 상대 좌표로 텍스트 그리기
                    relative_text_x = text_x - x1
                    relative_text_y = text_y - y1
                    
                    cv2.putText(temp_roi, best_text, (relative_text_x, relative_text_y), 
                              font, best_font_scale, text_color, thickness, cv2.LINE_AA)
                    
                    # 원본 이미지에 다시 복사
                    image[y1:y2, x1:x2] = temp_roi
                    
                    # 텍스트 표시 완료
                    pass
                else:
                    # ROI 크기가 너무 작아 텍스트 생략
                    pass
        else:
            base_pattern = np.array([[0, 255], [255, 0]], dtype=np.uint8)
            tile_x = (w + 1) // 2
            tile_y = (h + 1) // 2
            pattern = np.tile(base_pattern, (tile_y, tile_x))[:h, :w]
            if image.shape[2] == 3:
                pattern = np.stack([pattern] * 3, axis=2)
            image[y1:y2, x1:x2] = pattern

        return image

    def _aes_encrypt_bytes(self, data: bytes, key: bytes) -> bytes:
        try:
            # PKCS7 패딩
            pad_len = 16 - (len(data) % 16)
            padded = data + bytes([pad_len] * pad_len)
            
            # 패딩 검증
            if len(padded) % 16 != 0:
                raise ValueError("패딩 후 데이터 길이가 16의 배수가 아닙니다")
            
            # 암호화
            cipher = AES.new(key, AES.MODE_CBC)
            encrypted = cipher.encrypt(padded)
            
            # IV + 암호화된 데이터 반환
            return cipher.iv + encrypted
            
        except ValueError as e:
            # AES 암호화 실패
            raise ValueError("데이터 암호화에 실패했습니다")
        except Exception as e:
            # 예기치 않은 오류
            raise ValueError("데이터 암호화 중 오류가 발생했습니다")

    def _aes_decrypt_bytes(self, encrypted_data: bytes, key: bytes) -> bytes:
        if len(encrypted_data) < 32:  # IV(16) + 최소 1블록(16)
            raise ValueError("암호화된 데이터가 너무 짧습니다")
            
        if len(encrypted_data) % 16 != 0:
            raise ValueError("암호화된 데이터 길이가 16의 배수가 아닙니다")
            
        try:
            # IV 분리 및 복호화
            iv = encrypted_data[:16]
            cipher = AES.new(key, AES.MODE_CBC, iv)
            decrypted = cipher.decrypt(encrypted_data[16:])
            
            # PKCS7 패딩 검증 및 제거
            pad_len = decrypted[-1]
            
            if not (1 <= pad_len <= 16):
                raise ValueError("잘못된 패딩 길이")
                
            # 모든 패딩 바이트가 같은 값인지 검증
            padding = decrypted[-pad_len:]
            if not all(x == pad_len for x in padding):
                raise ValueError("잘못된 패딩 값")
                
            return decrypted[:-pad_len]
            
        except ValueError as e:
            # AES 복호화 실패
            raise ValueError("데이터 복호화에 실패했습니다")
        except Exception as e:
            # 예기치 않은 오류
            raise ValueError("데이터 복호화 중 오류가 발생했습니다")

    def _extract_app13_data(self, image_path: str) -> Tuple[dict, bytes, bytes]:
        try:
            with open(image_path, 'rb') as f:
                data = f.read()
            
            # 이미지 파일 크기 확인됨
            
            # 디버깅을 위한 파일 끝부분 확인
            tail_data = data[-100:] if len(data) >= 100 else data
            # 파일 끝부분 확인됨
            
            # 1. 모든 APP13 마커 위치 찾기
            app13_positions = []
            for i in range(len(data)-1):
                if data[i:i+2] == b'\xFF\xED':
                    app13_positions.append(i)
            
            if not app13_positions:
                # APP13 마커를 찾을 수 없음
                raise ValueError("암호화 데이터를 찾을 수 없습니다.")
            
            # 발견된 APP13 마커 위치들 확인됨
            
            # 2. 각 APP13 마커에서 유효한 ENCRA_META 찾기
            for marker_pos in app13_positions:
                try:
                    # ENCRA_META 마커 확인
                    meta_marker_pos = marker_pos + 2
                    if meta_marker_pos + 10 > len(data):
                        continue
                        
                    meta_marker = data[meta_marker_pos:meta_marker_pos+10]
                    if meta_marker != b'ENCRA_META':
                        continue
                    
                    # 수신자 수 읽기
                    num_recipients_pos = meta_marker_pos + 10
                    if num_recipients_pos + 4 > len(data):
                        continue
                        
                    num_recipients = int.from_bytes(data[num_recipients_pos:num_recipients_pos+4], 'big')
                    
                    if num_recipients <= 0 or num_recipients > 100:  # 합리적인 범위 체크
                        continue
                        
                    # 각 수신자의 암호화된 키 읽기
                    current_pos = num_recipients_pos + 4
                    encrypted_keys = []
                        
                    valid_structure = True
                    for i in range(num_recipients):
                        # 이메일 길이 + 이메일
                        if current_pos + 4 > len(data):
                            valid_structure = False
                            break
                            
                        email_len = int.from_bytes(data[current_pos:current_pos+4], 'big')
                        current_pos += 4
                        
                        if email_len <= 0 or email_len > 200:  # 합리적인 이메일 길이
                            valid_structure = False
                            break
                            
                        if current_pos + email_len > len(data):
                            valid_structure = False
                            break
                            
                        email = data[current_pos:current_pos+email_len].decode('utf-8', errors='ignore')
                        current_pos += email_len
                        
                        # 암호화된 키 길이 + 암호화된 키
                        if current_pos + 4 > len(data):
                            valid_structure = False
                            break
                            
                        key_len = int.from_bytes(data[current_pos:current_pos+4], 'big')
                        current_pos += 4
                        
                        if key_len <= 0 or key_len > 10000:  # 합리적인 키 길이
                            valid_structure = False
                            break
                            
                        if current_pos + key_len > len(data):
                            valid_structure = False
                            break
                            
                        encrypted_key = data[current_pos:current_pos+key_len]
                        current_pos += key_len
                            
                        encrypted_keys.append({
                            "email": email,
                            "key": encrypted_key
                        })
                    
                    if not valid_structure:
                        continue
                    
                    # 현재 사용자의 이메일 가져오기
                    current_email = get_user_email_from_keys()
                        
                    # 현재 사용자의 암호화된 키 찾기
                    current_key = None
                    for key_data in encrypted_keys:
                        if key_data["email"] == current_email:
                            current_key = key_data["key"]
                            break
                        
                    # 나머지 데이터를 암호화된 데이터로 간주
                    encrypted_data = data[current_pos:]
                    
                    return {}, current_key, encrypted_data
                    
                except Exception as e:
                    continue
            
            # 모든 APP13 위치에서 유효한 데이터를 찾지 못함
            # 유효한 ENCRA APP13 세그먼트를 찾을 수 없음
            raise ValueError("유효한 암호화 데이터를 찾을 수 없습니다")
            
        except Exception as e:
            # APP13 데이터 추출 실패
            raise

    def pdf_to_images(self, pdf_path: str) -> List[np.ndarray]:
        try:
            doc = fitz.open(pdf_path)
            images = []
            
            for page in doc:
                # 프론트엔드 스케일로 렌더링 (한글 주석: 백엔드와 통일된 스케일 사용)
                pix = page.get_pixmap(matrix=fitz.Matrix(self.PDF_FRONTEND_SCALE, self.PDF_FRONTEND_SCALE))
                # PNG 형식으로 변환
                img_data = pix.tobytes("png")
                # numpy array로 변환
                nparr = np.frombuffer(img_data, np.uint8)
                img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                images.append(img)
            
            doc.close()
            return images
        except Exception as e:
            raise ValueError("PDF를 이미지로 변환하는데 실패했습니다.")

    def decrypt_multiple_roi(self, image_path: str, private_key: bytes, pairing_group, user_email: str) -> np.ndarray:
        # 1. 개인키 검증
        if not private_key or len(private_key) < self.AES_KEY_SIZE:
            raise ValueError("개인키가 올바르지 않습니다.")
            
        try:
            # 개인키가 올바른 형식인지 검증
            d_id = pairing_group.deserialize(private_key)
            if not d_id:
                raise ValueError("개인키 형식이 올바르지 않습니다.")
        except Exception as e:
            raise ValueError("개인키가 손상되었습니다. 이메일 인증을 다시 진행해주세요.")
        
        # 2. 이미지 파일 검증
        self.validate_image(image_path)
        
        try:
            # 3. APP13 데이터 추출 (초기 방식)
            metadata, encrypted_aes_key, encrypted_data = self._extract_app13_data(image_path)
            
            # 4. IBE로 AES 키 복호화
            try:
                aes_key = decrypt_aes_key(encrypted_aes_key, private_key)
            except Exception as e:
                raise ValueError("개인키가 올바르지 않습니다. 이메일 인증을 다시 진행해주세요.")
            
            # 5. AES로 데이터 복호화 (초기 방식)
            try:
                decrypted = self._aes_decrypt_bytes(encrypted_data, aes_key)
                decompressed = zlib.decompress(decrypted)
                meta_json, all_roi_bytes = decompressed.split(b'<<ROI>>', 1)
                meta = json.loads(meta_json.decode())
                
                # 수신자 목록 확인
                if user_email not in meta.get("recipients", []):
                    raise ValueError("이 이미지의 수신자가 아닙니다.")
                
            except zlib.error:
                raise ValueError("이미지 데이터가 손상되었습니다.")
            except json.JSONDecodeError:
                raise ValueError("메타데이터가 손상되었습니다.")
            except Exception as e:
                raise ValueError("이미지 데이터 복호화에 실패했습니다.")
            
            # 6. 원본 이미지에 다중 ROI 복원
            try:
                # 이미지 로드
                image = cv2.imread(image_path)
                if image is None:
                    raise ValueError("이미지 파일을 읽을 수 없습니다.")
                
                roi_list = meta.get("roi_list", [])
                roi_count = meta.get("roi_count", len(roi_list))
                
                # 모든 ROI 바이트 데이터를 분리하여 복원
                current_pos = 0
                for i, roi_info in enumerate(roi_list):
                    try:
                        # ROI 크기 계산 (이미지 크기 추정)
                        width = int(roi_info["width"])
                        height = int(roi_info["height"])
                        
                        # JPEG 헤더를 찾아 실제 ROI 데이터 크기 확인
                        # JPEG 시작 마커 (FFD8) 찾기
                        jpeg_start = all_roi_bytes.find(b'\xFF\xD8', current_pos)
                            
                        # JPEG 종료 마커 (FFD9) 찾기
                        jpeg_end = all_roi_bytes.find(b'\xFF\xD9', jpeg_start)
                            
                        roi_bytes = all_roi_bytes[jpeg_start:jpeg_end+2]
                        current_pos = jpeg_end + 2
                        
                        # ROI 이미지 디코딩
                        roi_img = cv2.imdecode(np.frombuffer(roi_bytes, np.uint8), cv2.IMREAD_COLOR)
                        if roi_img is None:
                            continue
                        
                        # ROI 위치 정보
                        x = int(roi_info["x"])
                        y = int(roi_info["y"])
                        h, w = roi_img.shape[:2]
                        
                        # 좌표 검증 및 clamp
                        x1, y1, x2, y2 = self.validate_roi_coords(image.shape, (x, y, x + w, y + h))
                        
                        # ROI 복원
                        image[y1:y2, x1:x2] = roi_img[:y2-y1, :x2-x1]
                        
                    except Exception as roi_error:
                        continue
                
                return image
                
            except ValueError as e:
                raise
            except Exception as e:
                raise ValueError("이미지 복원에 실패했습니다.")
                
        except Exception as e:
            raise 

    def encrypt_multiple_roi(self, image_data: Union[str, np.ndarray], roi_list: List[dict], recipients: List[str]) -> str:
        try:
            # 이미지 데이터 처리
            if isinstance(image_data, str):
                self.validate_file(image_data)
                image = cv2.imread(image_data)
                if image is None:
                    raise ValueError(f"이미지를 로드할 수 없습니다: {image_data}")
                image_path = image_data
            else:
                image = image_data
                # numpy 배열인 경우 임시 파일로 저장
                temp_dir = tempfile.mkdtemp()
                image_path = os.path.join(temp_dir, 'temp_input.jpg')
                cv2.imwrite(image_path, image, [cv2.IMWRITE_JPEG_QUALITY, 95])

            # 모든 ROI에 마스킹 적용
            masked_image = image.copy()
            all_roi_data = []
            
            for i, roi in enumerate(roi_list):
                # ROI 좌표를 int로 변환 및 검증
                x1 = int(roi['x'])
                y1 = int(roi['y'])
                x2 = int(x1 + roi['width'])
                y2 = int(y1 + roi['height'])
                
                # ROI 좌표 검증 및 클램핑
                x1, y1, x2, y2 = self.validate_roi_coords(image.shape, (x1, y1, x2, y2))
                
                # 마스킹 적용
                masked_image = self.apply_mask(masked_image, (x1, y1, x2, y2), "Solid")
                
                # ROI 영역 추출 및 JPEG 압축 (초기 방식과 동일)
                roi_img = image[y1:y2, x1:x2]
                if roi_img.size == 0:
                    raise ValueError(f"ROI {i+1} 영역이 비어있습니다")
                
                roi_pil = Image.fromarray(cv2.cvtColor(roi_img, cv2.COLOR_BGR2RGB))
                buffer = io.BytesIO()
                roi_pil.save(buffer, format="JPEG", quality=90)
                roi_bytes = buffer.getvalue()
                
                # ROI 데이터 저장 (초기 방식 구조)
                roi_data = {
                    "roi_id": i,
                    "x": x1, "y": y1,
                    "width": x2 - x1,
                    "height": y2 - y1,
                    "roi_format": "JPEG"
                }
                
                # ROI 바이트 데이터 추가 (메타데이터와 분리)
                all_roi_data.append((roi_data, roi_bytes))
            
            # 초기 방식: 메타데이터 구조
            meta = {
                "roi_count": len(roi_list),
                "roi_list": [roi_data for roi_data, _ in all_roi_data],
                "recipients": recipients
            }
            
            # 모든 ROI 바이트 데이터 결합
            combined_roi_bytes = b"".join([roi_bytes for _, roi_bytes in all_roi_data])
            
            # 초기 방식: 메타데이터 + ROI 데이터 결합
            meta_json = json.dumps(meta).encode()
            combined_data = meta_json + b"<<ROI>>" + combined_roi_bytes
            compressed = zlib.compress(combined_data)
            
            # AES-256 키 생성 및 데이터 암호화
            aes_key = get_random_bytes(32)
            encrypted_data = self._aes_encrypt_bytes(compressed, aes_key)
            
            # 각 수신자별로 AES 키를 IBE로 암호화
            encrypted_keys = []
            for recipient in recipients:
                encrypted_key = encrypt_aes_key(recipient, aes_key)
                encrypted_keys.append({
                    "email": recipient,
                    "key": encrypted_key
                })

            # PNG→JPEG 변환으로 용량 최적화 (한글 주석: 모든 이미지를 JPEG로 통일)
            temp_dir = tempfile.mkdtemp()  
            temp_path = os.path.join(temp_dir, 'encrypted_multiple.jpg')
            
            # JPEG 품질을 원본 형식에 따라 조정
            original_ext = os.path.splitext(image_path)[1].lower()
            jpeg_quality = 95
            cv2.imwrite(temp_path, masked_image, [cv2.IMWRITE_JPEG_QUALITY, jpeg_quality])
            
            # 초기 방식: APP13 세그먼트 직접 추가
            with open(temp_path, 'ab') as f:
                f.write(b'\xFF\xED')  # APP13 마커
                f.write(b'ENCRA_META')  # 메타데이터 마커
                # 수신자 수 저장 (4바이트)
                f.write(len(recipients).to_bytes(4, 'big'))
                for key_data in encrypted_keys:
                    # 이메일 길이 (4바이트) + 이메일
                    email_bytes = key_data["email"].encode()
                    f.write(len(email_bytes).to_bytes(4, 'big'))
                    f.write(email_bytes)
                        
                    # 암호화된 키 길이 (4바이트) + 암호화된 키
                    key_bytes = key_data["key"]
                    f.write(len(key_bytes).to_bytes(4, 'big'))
                    f.write(key_bytes)
                f.write(encrypted_data)  # 암호화된 ROI 데이터
            
            # APP13 검증
            with open(temp_path, 'rb') as f:
                verify_data = f.read()
                app13_count = verify_data.count(b'\xFF\xED')
            
            return temp_path
            
        except Exception as e:
            raise 

    def _store_in_app13(self, image, encrypted_keys, encrypted_data, recipients):
        # 임시 파일에 이미지 저장
        temp_dir = tempfile.mkdtemp()
        temp_path = os.path.join(temp_dir, 'temp_image.jpg')
        
        success = cv2.imwrite(temp_path, image, [cv2.IMWRITE_JPEG_QUALITY, 95])
        if not success:
            raise ValueError("임시 이미지 저장 실패")
            
        clean_size = os.path.getsize(temp_path)
        
        with open(temp_path, 'rb') as f:
            check_data = f.read()
            existing_app13_count = check_data.count(b'\xFF\xED')
            
            if existing_app13_count > 0:
                # 기존 APP13 제거
                jpeg_end_pos = -1
                for i in range(len(check_data) - 1):
                    if check_data[i:i+2] == b'\xFF\xD9':
                        jpeg_end_pos = i + 2
                        break
                
                if jpeg_end_pos > 0:
                    clean_jpeg_data = check_data[:jpeg_end_pos]
                    with open(temp_path, 'wb') as clean_f:
                        clean_f.write(clean_jpeg_data)
                    
                    clean_size = os.path.getsize(temp_path)

        with open(temp_path, 'ab') as f:
            f.write(b'\xFF\xED')  # APP13 마커
            f.write(b'ENCRA_META')  # 메타데이터 마커
            # 수신자 수 저장 (4바이트)
            f.write(len(recipients).to_bytes(4, 'big'))
            for i, recipient in enumerate(recipients):
                # 이메일 길이 (4바이트) + 이메일
                email_bytes = recipient.encode()
                f.write(len(email_bytes).to_bytes(4, 'big'))
                f.write(email_bytes)
                    
                # 암호화된 키 길이 (4바이트) + 암호화된 키
                key_bytes = encrypted_keys[i]["key"] if isinstance(encrypted_keys[i], dict) else encrypted_keys[i]
                f.write(len(key_bytes).to_bytes(4, 'big'))
                f.write(key_bytes)
            f.write(encrypted_data)  # 암호화된 ROI 데이터


        import shutil
        output_temp_dir = tempfile.mkdtemp()
        output_path = os.path.join(output_temp_dir, 'image_with_app13.jpg')
        shutil.copy2(temp_path, output_path)
        
        os.remove(temp_path)
        os.rmdir(temp_dir)
        
        return output_path 



    def encrypt_pdf_roi(self, pdf_path: str, roi_data_by_page: List[dict], recipients: List[str], quality_scale: float = 1.0) -> str:
        try:
            # 1. PDF 파일 검증
            self.validate_file(pdf_path)
            
            # 2. PDF 문서 열기
            doc = fitz.open(pdf_path)
            
            aes_key = get_random_bytes(self.AES_KEY_SIZE)
            
            # 4. 각 수신자별로 AES 키를 IBE로 암호화 (한글 주석: 한 번만 수행)
            encrypted_keys = []
            for recipient in recipients:
                encrypted_key = encrypt_aes_key(recipient, aes_key)
                encrypted_keys.append({
                    "email": recipient,
                    "key": base64.b64encode(encrypted_key).decode('utf-8')
                })
            
            # 5. 모든 암호화된 ROI 데이터 저장할 리스트
            all_encrypted_rois = []
            
            # 4. 각 페이지별로 고품질 처리
            for page_data in roi_data_by_page:
                page_num = page_data["page"] - 1  # 0부터 시작하는 인덱스로 변환
                rois = page_data["rois"]
                
                if page_num >= len(doc) or not rois:
                    continue
                    
                page = doc[page_num]
                
                # 페이지 이미지 생성 (한글 주석: 품질 스케일로 품질과 용량 조절)
                matrix = fitz.Matrix(quality_scale, quality_scale)
                pix = page.get_pixmap(matrix=matrix)
                img_data = pix.tobytes("png")
                nparr = np.frombuffer(img_data, np.uint8)
                page_image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                
                roi_coords_list = []  # 마스킹용 좌표 저장
                for roi_idx, roi in enumerate(rois):
                    conversion_factor = quality_scale / self.PDF_FRONTEND_SCALE  # quality_scale / 1.0
                    
                    x1 = round(roi['x'] * conversion_factor)  # 반올림으로 정확한 정수
                    y1 = round(roi['y'] * conversion_factor)  # 반올림으로 정확한 정수
                    x2 = round((roi['x'] + roi['width']) * conversion_factor)  # 반올림으로 정확한 정수
                    y2 = round((roi['y'] + roi['height']) * conversion_factor)  # 반올림으로 정확한 정수
                    
                    x1 = max(0, min(x1, page_image.shape[1]))
                    y1 = max(0, min(y1, page_image.shape[0]))
                    x2 = max(x1, min(x2, page_image.shape[1]))
                    y2 = max(y1, min(y2, page_image.shape[0]))
                    
                    if x2 > x1 and y2 > y1:
                        roi_image = page_image[y1:y2, x1:x2].copy()
                    else:
                        continue
                    
                    # JPEG 고압축 인코딩 (용량 최적화)
                    encode_param = [cv2.IMWRITE_JPEG_QUALITY, 90]  # 90% 품질
                    success, encoded_img = cv2.imencode('.jpg', roi_image, encode_param)
                    if not success:
                        continue
                        
                    roi_bytes = encoded_img.tobytes()
                    compressed = zlib.compress(roi_bytes, level=9)  # 최대 압축
                    encrypted_data = self._aes_encrypt_bytes(compressed, aes_key)  # 공통 AES 키 사용
                    
                    # 암호화된 ROI 정보 저장
                    all_encrypted_rois.append({
                        "page": page_num + 1,
                        "roi_index": roi_idx,
                        "x": x1,
                        "y": y1,
                        "width": x2 - x1,
                        "height": y2 - y1,
                        "conversion_factor": conversion_factor,  # 복원 시 필요
                        "processing_scale": quality_scale,  # 선택된 품질 스케일
                        "frontend_scale": self.PDF_FRONTEND_SCALE,  # 프론트엔드 스케일 (1.0)
                        "encrypted_data": base64.b64encode(encrypted_data).decode('utf-8')
                    })
                    
                    # 마스킹을 위한 좌표 저장
                    roi_coords_list.append((x1, y1, x2, y2))
                    
                
                # 모든 ROI 데이터 추출 완료 후 마스킹 적용
                for roi_idx, roi_coords in enumerate(roi_coords_list):
                    x1, y1, x2, y2 = roi_coords
                    
                    # 이미지 마스킹 적용
                    page_image = self.apply_mask(page_image, (x1, y1, x2, y2), "Solid")
                        
                # 이미지를 임시 파일로 저장
                temp_img_path = os.path.join(tempfile.gettempdir(), f"page_{page_num}.jpg")  # PNG → JPEG 변경
                # JPEG 고압축으로 페이지 이미지 저장 (용량 최적화)
                cv2.imwrite(temp_img_path, page_image, [cv2.IMWRITE_JPEG_QUALITY, 85])  # 85% 품질
                
                # 현재 페이지 크기와 회전 정보 저장
                page_rect = page.rect
                page_rotation = page.rotation
                
                # 기존 페이지 삭제
                doc.delete_page(page_num)
                
                # 새 빈 페이지 생성
                new_page = doc.new_page(page_num, width=page_rect.width, height=page_rect.height)
                if page_rotation != 0:
                    new_page.set_rotation(page_rotation)
                
                # 새 페이지에 이미지만 삽입
                new_page.insert_image(page_rect, filename=temp_img_path)
                
                # 임시 파일 삭제
                os.remove(temp_img_path)
            
            # 6. 암호화된 ROI 데이터를 PDF Attachment로 저장
            metadata = {
                "encra_version": "1.0",
                "mode": "imageprocessing",  # 이미지처리 방식 표시
                "quality_scale": quality_scale,  # 사용된 품질 스케일
                "recipients": recipients,
                "encrypted_keys": encrypted_keys,  # 공통 AES 키 (수신자별 IBE 암호화)
                "encrypted_rois": all_encrypted_rois
            }
            
            metadata_bytes = json.dumps(metadata).encode('utf-8')
            doc.embfile_add("encra_data.json", metadata_bytes, desc="ENCRA image-processing encryption data")
            
            # 7. 결과 PDF 저장
            temp_dir = tempfile.mkdtemp()
            output_path = os.path.join(temp_dir, 'encrypted.pdf')
            
            # 용량 최적화 옵션으로 PDF 저장 (한글 주석: 파일 크기 최소화)
            doc.save(output_path,
                    garbage=4,           # 최대 가비지 컬렉션
                    clean=True,          # 불필요한 객체 제거
                    deflate=True,        # 스트림 압축
                    deflate_images=True, # 이미지 압축
                    deflate_fonts=True)  # 폰트 압축
            doc.close()
            
            return output_path
            
        except Exception as e:
            raise

    def decrypt_pdf_roi(self, pdf_path: str, private_key: bytes, pairing_group, user_email: str) -> str:
        """
        암호화된 PDF의 ROI 복원
        
        Args:
            pdf_path (str): 암호화된 PDF 경로
            private_key (bytes): IBE 개인키
            pairing_group: IBE 페어링 그룹  
            user_email (str): 사용자 이메일
            
        Returns:
            str: 복호화된 PDF 파일 경로
        """
        try:
            # 1. PDF 파일 검증
            self.validate_file(pdf_path)
            
            # 2. PDF 문서 열기
            doc = fitz.open(pdf_path)
            
            # 3. PDF Attachment에서 암호화 정보 추출 (한글 주석: 첨부파일에서 암호화 데이터 로드)
            embedded_files = doc.embfile_names()
            if "encra_data.json" not in embedded_files:
                raise ValueError("암호화된 PDF가 아닙니다.")
                
            # 첨부된 암호화 데이터 읽기
            metadata_bytes = doc.embfile_get("encra_data.json")
            encra_data = json.loads(metadata_bytes.decode('utf-8'))
            recipients = encra_data["recipients"]
            encrypted_rois = encra_data["encrypted_rois"]
            
            # 암호화 모드 확인 (한글 주석: 표준/이미지처리 모드 감지)
            encryption_mode = encra_data.get("mode", "normal")
            
            # 4. 사용자가 수신자인지 확인
            if user_email not in recipients:
                raise ValueError("이 PDF의 수신자가 아닙니다.")
            
            # 5. 공통 AES 키 복호화 (한글 주석: 파일당 하나의 키만 복호화)
            encrypted_keys = encra_data.get("encrypted_keys", [])
            user_encrypted_key = None
            for key_info in encrypted_keys:
                if key_info["email"] == user_email:
                    user_encrypted_key = base64.b64decode(key_info["key"])
                    break
                    
            if not user_encrypted_key:
                raise ValueError("사용자의 암호화 키를 찾을 수 없습니다.")
                
            # IBE로 공통 AES 키 복호화
            aes_key = decrypt_aes_key(user_encrypted_key, private_key)
            
            # 6. 각 ROI 복호화 및 복원 (한글 주석: 공통 키로 모든 ROI 복호화)
            for roi_data in encrypted_rois:
                page_num = roi_data["page"] - 1
                page = doc[page_num]
                
                # ROI 데이터 복호화
                encrypted_data = base64.b64decode(roi_data["encrypted_data"])
                decrypted = self._aes_decrypt_bytes(encrypted_data, aes_key)
                decompressed = zlib.decompress(decrypted)
                
                # ROI 이미지 복원
                roi_img = cv2.imdecode(np.frombuffer(decompressed, np.uint8), cv2.IMREAD_COLOR)
                
                # 복호화된 ROI를 PDF에 고품질 이미지로 삽입 (한글 주석: 좌표 정확도 및 품질 개선)
                try:
                    # 1. 고품질 이미지 저장 (한글 주석: JPEG 압축으로 용량 최적화)
                    temp_img_path = os.path.join(tempfile.gettempdir(), f"roi_{page_num}_{roi_data['roi_index']}.jpg")  # PNG → JPEG
                    
                    # JPEG 고품질 저장 설정 (용량 최적화)
                    jpeg_params = [cv2.IMWRITE_JPEG_QUALITY, 95]  # 95% 품질로 용량과 품질 균형
                    cv2.imwrite(temp_img_path, roi_img, jpeg_params)
                    
                    # 2. 암호화 모드에 따른 좌표 계산 (한글 주석: 표준/이미지처리 모드별 좌표 변환)
                    if encryption_mode in ["highquality", "imageprocessing"]:
                        # 이미지처리 모드: 스케일 통일로 단순화
                        processing_scale = roi_data.get("processing_scale", 1.0)
                        
                        # 이미지 좌표에서 PDF 좌표로 역변환 (스케일 통일로 단순화)
                        pdf_x1 = roi_data["x"] / processing_scale
                        pdf_y1 = roi_data["y"] / processing_scale
                        pdf_x2 = (roi_data["x"] + roi_data["width"]) / processing_scale
                        pdf_y2 = (roi_data["y"] + roi_data["height"]) / processing_scale
                    else:
                        # 표준 모드: 1배 스케일 기준 (한글 주석: 여백 없이 정확한 좌표 사용)
                        page_image_width = page.rect.width   # 1배 스케일
                        page_image_height = page.rect.height # 1배 스케일
                        
                        pdf_scale_x = page.rect.width / page_image_width   # 1.0
                        pdf_scale_y = page.rect.height / page_image_height # 1.0
                        
                        # 여백 없이 정확한 좌표 사용
                        pdf_x1 = roi_data["x"] * pdf_scale_x
                        pdf_y1 = roi_data["y"] * pdf_scale_y
                        pdf_x2 = (roi_data["x"] + roi_data["width"]) * pdf_scale_x
                        pdf_y2 = (roi_data["y"] + roi_data["height"]) * pdf_scale_y
                    
                    # 3. PDF에 고품질 이미지 삽입 (한글 주석: 품질 유지 옵션 적용)
                    img_rect = fitz.Rect(pdf_x1, pdf_y1, pdf_x2, pdf_y2)
                    
                    # 이미지 삽입 시 품질 옵션 설정
                    page.insert_image(
                        img_rect, 
                        filename=temp_img_path,
                        keep_proportion=True,  # 비율 유지
                        overlay=True          # 덮어쓰기 모드
                    )
                    
                    # 임시 파일 삭제
                    os.remove(temp_img_path)
                    
                except Exception as e:
                    continue
            
            # 암호화 데이터 첨부파일 제거 (한글 주석: 복호화 후 암호화 정보 삭제)
            try:
                doc.embfile_del("encra_data.json")
            except:
                pass  # 파일이 없어도 무시
            
            # 7. 복호화된 PDF 저장
            temp_dir = tempfile.mkdtemp()
            output_path = os.path.join(temp_dir, 'decrypted.pdf')
            
            # 용량 최적화 옵션으로 PDF 저장 (한글 주석: 파일 크기 최소화)
            doc.save(output_path, 
                    garbage=4,           # 최대 가비지 컬렉션
                    clean=True,          # 불필요한 객체 제거
                    deflate=True,        # 스트림 압축
                    deflate_images=True, # 이미지 압축
                    deflate_fonts=True)  # 폰트 압축
            doc.close()
            
            return output_path
            
        except Exception as e:
            self.logger.error(f"PDF ROI 복호화 실패: {str(e)}")
            raise 