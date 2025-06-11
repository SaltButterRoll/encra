from charm.toolbox.pairinggroup import G1, pair
from hashlib import sha256
from models.ibe_constants import PAIRING_GROUP
import importlib
import logging
import json
import os
from .constants import USER_KEYS_DIR
logger = logging.getLogger(__name__)

def get_current_public_params():
    """현재 PUBLIC_PARAMS 값을 동적으로 로드 (모듈 재로드 포함)"""
    import models.ibe_constants
    importlib.reload(models.ibe_constants)  # 모듈 재로드로 최신 값 가져오기
    
    public_params = models.ibe_constants.PUBLIC_PARAMS
    
    # 메일 인증이 아직 완료되지 않은 경우 체크
    if public_params["g"] is None or public_params["g^alpha"] is None:
        raise ValueError("메일 인증이 완료되지 않았습니다. 먼저 이메일 인증을 진행해주세요.")
    
    return public_params

def get_user_email_from_keys() -> str:
    """_keys 폴더의 user_info.json에서 사용자 이메일을 가져옴
    
    Returns:
        str: 사용자 이메일
        
    Raises:
        FileNotFoundError: user_info.json 파일이 없는 경우
        ValueError: 이메일 정보가 없거나 잘못된 형식인 경우
    """
    try:
        user_info_path = os.path.join(USER_KEYS_DIR, 'user_info.json')
        
        if not os.path.exists(user_info_path):
            raise FileNotFoundError(f"사용자 정보 파일을 찾을 수 없습니다: {user_info_path}")
            
        with open(user_info_path, 'r') as f:
            user_info = json.load(f)
            
        if 'email' not in user_info:
            raise ValueError("사용자 정보에 이메일이 없습니다")
            
        return user_info['email']
        
    except json.JSONDecodeError:
        raise ValueError("사용자 정보 파일이 잘못된 형식입니다")
    except Exception as e:
        logger.error(f"사용자 이메일 조회 중 오류 발생: {str(e)}")
        raise

def encrypt_aes_key(email: str, aes_key: bytes) -> bytes:
    """AES 키를 IBE로 암호화 (g^alpha 기반)"""
    try:
        # 최신 PUBLIC_PARAMS 동적 로드 (메일 인증 후 업데이트된 값 반영)
        public_params = get_current_public_params()
        
        # g, g^alpha 가져오기
        g = PAIRING_GROUP.deserialize(bytes.fromhex(public_params["g"]))
        g_alpha = PAIRING_GROUP.deserialize(bytes.fromhex(public_params["g^alpha"]))

        # 수신자 ID → Q_id 해시
        Q_id = PAIRING_GROUP.hash(email.encode(), G1)

        # 무작위 r 생성
        r = PAIRING_GROUP.random()

        # U = g^r
        U = g ** r

        # 공유 비밀키 k = e(Q_id, g^alpha)^r
        k = pair(Q_id, g_alpha) ** r
        k_bytes = PAIRING_GROUP.serialize(k)
        # 해시 후 XOR
        h = sha256(k_bytes).digest()
        V = bytes(a ^ b for a, b in zip(aes_key, h))

        # 직렬화된 U + V 반환
        serialized_U = PAIRING_GROUP.serialize(U)
        return V + serialized_U

    except Exception as e:
        raise ValueError("AES 키 암호화에 실패했습니다")


def decrypt_aes_key(encrypted_key: bytes, private_key: bytes) -> bytes:
    """IBE로 암호화된 AES 키를 복호화 (serialize(k) 방식)"""
    try:
        V = encrypted_key[:32]
        U = encrypted_key[32:]

        # 역직렬화
        try:
            U_elem = PAIRING_GROUP.deserialize(U)
            d_id = PAIRING_GROUP.deserialize(private_key)
        except Exception as e:
            raise ValueError("암호화된 키가 손상되었습니다")

        k = pair(d_id, U_elem)
        k_bytes = PAIRING_GROUP.serialize(k)

        h = sha256(k_bytes).digest()

        # V ⊕ H(k) = 복원된 AES 키
        aes_key = bytes(a ^ b for a, b in zip(V, h))

        return aes_key

    except Exception as e:
        raise ValueError("AES 키 복호화에 실패했습니다")
