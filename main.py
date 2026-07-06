from fastapi import FastAPI, Request, Response
import config
import time
import uuid

app = FastAPI()


# ---------------------------
# Middleware
# ---------------------------
@app.middleware("http")
async def add_headers(request: Request, call_next):
    start_time = time.time()

    # Handle OPTIONS request (Preflight)
    if request.method == "OPTIONS":
        response = Response(status_code=204)
    else:
        response = await call_next(request)

    process_time = time.time() - start_time

    # Required Headers
    response.headers["X-Request-ID"] = str(uuid.uuid4())
    response.headers["X-Process-Time"] = f"{process_time:.6f}"

    # CORS
    origin = request.headers.get("origin")

    if origin in [
        config.Q1_ALLOWED_ORIGIN,
        config.EXAM_PORTAL_ORIGIN
    ]:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "*"

    return response


# ---------------------------
# Home
# ---------------------------
@app.get("/")
def home():
    return {
        "message": "TDS Assignment Q1"
    }


# ---------------------------
# Question 1
# ---------------------------
@app.get("/stats")
def stats(values: str):

    numbers = [int(x) for x in values.split(",") if x.strip()]

    return {
        "email": config.EMAIL,
        "count": len(numbers),
        "sum": sum(numbers),
        "min": min(numbers),
        "max": max(numbers),
        "mean": round(sum(numbers) / len(numbers), 6)
    }