"""
IBE 시스템의 공개 파라미터

클라이언트에서 사용하는 IBE 시스템의 공개 파라미터를 저장합니다.
PKG 서버와의 통신을 최소화하기 위해 상수로 저장합니다.
"""
from charm.toolbox.pairinggroup import PairingGroup
# 페어링 그룹 설정
PAIRING_GROUP = PairingGroup('SS512')

# 공개 파라미터 (메일 인증 후 초기화됨)
PUBLIC_PARAMS = {
    "g": None,
    "g^alpha": None
}
