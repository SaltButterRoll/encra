import os
import json
from charm.toolbox.pairinggroup import PairingGroup, G1, ZR
from typing import Dict, Any

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PKG_DIR = os.path.join(BASE_DIR, "..", "pkg_keys")
MASTER_FILE = os.path.join(PKG_DIR, "ibe_ctx.json")
PUBLIC_PARAMS_FILE = os.path.join(PKG_DIR, "public_params.json")

group = PairingGroup('SS512')

def _ensure_pkg_dir():
    os.makedirs(PKG_DIR, exist_ok=True)

def _save_public_params(g, g_alpha):
    with open(PUBLIC_PARAMS_FILE, "w") as f:
        json.dump({
            "g": group.serialize(g).hex(),
            "g^alpha": group.serialize(g_alpha).hex()
        }, f)

def generate_master_keys() -> None:
    _ensure_pkg_dir()
    if os.path.exists(MASTER_FILE):
        return

    g = group.random(G1)
    alpha = group.random(ZR)
    g_alpha = g ** alpha

    with open(MASTER_FILE, "w") as f:
        json.dump({
            "mpk": {
                "g": group.serialize(g).hex(),
                "g^alpha": group.serialize(g_alpha).hex()
            },
            "msk": {
                "alpha": group.serialize(alpha).hex()
            }
        }, f)
    
    _save_public_params(g, g_alpha)

def load_master_keys() -> tuple:
    with open(MASTER_FILE, "r") as f:
        data = json.load(f)
        g = group.deserialize(bytes.fromhex(data["mpk"]["g"]))
        g_alpha = group.deserialize(bytes.fromhex(data["mpk"]["g^alpha"]))
        alpha = group.deserialize(bytes.fromhex(data["msk"]["alpha"]))

    mpk = { "g": g, "g^alpha": g_alpha }
    msk = { "alpha": alpha }
    return mpk, msk

def get_public_params() -> Dict[str, Any]:
    try:
        with open(PUBLIC_PARAMS_FILE, "r") as f:
            data = json.load(f)
            return {
                'g': bytes.fromhex(data['g']),
                'g^alpha': bytes.fromhex(data['g^alpha'])
            }
    except Exception as e:
        raise Exception(f"공개 파라미터 로드 중 오류: {str(e)}")

def extract_user_private_key(email: str) -> bytes:
    try:
        _, msk = load_master_keys()
        
        Q_id = group.hash(email, G1)
        sk = Q_id ** msk['alpha']
        
        return group.serialize(sk)
        
    except Exception as e:
        raise Exception(f"개인키 생성 중 오류: {str(e)}")
