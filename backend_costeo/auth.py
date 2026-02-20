import os
import httpx
from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")

security = HTTPBearer()

def verificar_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    token = credentials.credentials
    
    # Intentar primero con ES256 usando la JWKS de Supabase
    try:
        jwks_url = f"{SUPABASE_URL}/auth/v1/.well-known/jwks.json"
        import urllib.request, json as json_lib
        with urllib.request.urlopen(jwks_url) as response:
            jwks = json_lib.loads(response.read())
        
        from jose import jwk
        from jose.utils import base64url_decode
        
        # Tomar la primera clave del JWKS
        key = jwks["keys"][0]
        public_key = jwk.construct(key)
        
        payload = jwt.decode(
            token,
            public_key.to_pem().decode(),
            algorithms=["ES256", "RS256"],
            options={"verify_aud": False}
        )
        return payload
    except Exception:
        pass
    
    # Fallback: intentar con HS256 y el legacy secret
    try:
        payload = jwt.decode(
            token,
            SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            options={"verify_aud": False}
        )
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")

def get_usuario_actual(payload: dict = Depends(verificar_token)):
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Token sin usuario")
    return user_id

async def get_rol_usuario(user_id: str = Depends(get_usuario_actual)) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{SUPABASE_URL}/rest/v1/usuarios?id=eq.{user_id}&select=rol,email,nombre,apellido,activo",
            headers={
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}"
            }
        )
    data = response.json()
    if not data:
        raise HTTPException(status_code=403, detail="Usuario no encontrado")
    usuario = data[0]
    if not usuario.get("activo"):
        raise HTTPException(status_code=403, detail="Usuario inactivo")
    return usuario

def solo_admin(usuario: dict = Depends(get_rol_usuario)):
    if usuario.get("rol") != "admin":
        raise HTTPException(status_code=403, detail="Se requiere rol de administrador")
    return usuario

def admin_o_vendedor(usuario: dict = Depends(get_rol_usuario)):
    if usuario.get("rol") not in ("admin", "vendedor"):
        raise HTTPException(status_code=403, detail="Acceso no autorizado")
    return usuario