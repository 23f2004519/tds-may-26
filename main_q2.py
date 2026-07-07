from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from jose import jwt, JWTError
from datetime import datetime, timezone

app = FastAPI()


PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA2okOHspNjgA+2rTLbeuY
cxiP/hG8C6Sb9iwg3yiLAA4HCnpITcbWCSelbvbYGuc3EbNy4xFyf5Cbj5DHJMID
EkryOgyd2giIIIBOUBj8S63uGcnRpOBh9NFatfNwheKuzsPuVNldu6A9cNteNpXc
WyJjG2axVfmq7i6SuKr1JoWYG7xTTAvKPujSl4OtsQfO3h5NepzdfXpr28oNnzfW
ed+zclR6BcmNNo/WVfJ4xyCLSf0BCOgdTgW6PdaChd1l9VDetJZVEgC5tkyvXsfI
SI6iyrYbKR0NEBSqq4XkadEjsCs4F1RncsS4LlgniT7GlkL9Mce3b0wGLs9/7ZIX
dQIDAQAB
-----END PUBLIC KEY-----"""

ISS = "https://idp.exam.local"
AUD = "tds-ja9wj9j2.apps.exam.local"
ALGO = "RS256"


class VerifyRequest(BaseModel):
    token: str


class VerifyResponse(BaseModel):
    valid: bool
    email: str | None = None
    sub: str | None = None
    aud: str | None = None


@app.post("/verify", response_model=VerifyResponse)
def verify(req: VerifyRequest):
    try:
        # Decode + verify signature, issuer, audience
        payload = jwt.decode(
            req.token,
            PUBLIC_KEY,
            algorithms=[ALGO],
            audience=AUD,
            issuer=ISS,
        )

        # Extra expiry check (library already checks exp, but keep it explicit)
        exp = payload.get("exp")
        if exp is None or exp < datetime.now(timezone.utc).timestamp():
            # Expired token
            return VerifyResponse(valid=False)

        return VerifyResponse(
            valid=True,
            email=payload.get("email"),
            sub=payload.get("sub"),
            aud=payload.get("aud"),
        )
    except (JWTError, Exception):
        # Any failure: invalid token
        return VerifyResponse(valid=False)
