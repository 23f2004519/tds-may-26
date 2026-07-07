import os
from typing import Dict, Any, List

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

import yaml

app = FastAPI()

# CORS: allow exam origin (any origin is ok for this assignment)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or ["https://exam.sanand.workers.dev"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. Defaults (lowest precedence)
DEFAULTS: Dict[str, Any] = {
    "port": 8000,
    "workers": 1,
    "debug": False,
    "log_level": "info",
    "api_key": "default-secret-000",
}


def load_yaml_config() -> Dict[str, Any]:
    """
    Load config.development.yaml if present.
    """
    cfg: Dict[str, Any] = {}
    path = "config.development.yaml"
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                data = yaml.safe_load(f) or {}
                # expect keys like workers, log_level
                if isinstance(data, dict):
                    cfg.update(data)
        except Exception:
            pass
    return cfg


def load_dotenv_config() -> Dict[str, Any]:
    """
    Load .env values (APP_* and NUM_WORKERS alias).
    """
    cfg: Dict[str, Any] = {}

    # Read .env manually (simple parser)
    env_path = ".env"
    if os.path.exists(env_path):
        try:
            with open(env_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip()
                    # Save relevant keys
                    cfg[key] = value
        except Exception:
            pass

    # Map APP_* -> internal keys
    if "APP_PORT" in cfg:
        cfg["port"] = cfg["APP_PORT"]
    if "APP_DEBUG" in cfg:
        cfg["debug"] = cfg["APP_DEBUG"]
    if "APP_LOG_LEVEL" in cfg:
        cfg["log_level"] = cfg["APP_LOG_LEVEL"]

    # Alias: NUM_WORKERS -> workers
    if "NUM_WORKERS" in cfg:
        cfg["workers"] = cfg["NUM_WORKERS"]

    return cfg


def load_os_env_config() -> Dict[str, Any]:
    """
    Load OS environment vars with APP_* prefix.
    """
    cfg: Dict[str, Any] = {}

    app_port = os.getenv("APP_PORT")
    if app_port is not None:
        cfg["port"] = app_port

    app_workers = os.getenv("APP_WORKERS")
    if app_workers is not None:
        cfg["workers"] = app_workers

    app_debug = os.getenv("APP_DEBUG")
    if app_debug is not None:
        cfg["debug"] = app_debug

    app_log_level = os.getenv("APP_LOG_LEVEL")
    if app_log_level is not None:
        cfg["log_level"] = app_log_level

    # If there were other APP_* keys, we could add them too.
    return cfg


def apply_cli_overrides(base_cfg: Dict[str, Any], sets: List[str]) -> Dict[str, Any]:
    """
    Apply ?set=key=value overrides as highest precedence.
    """
    cfg = base_cfg.copy()
    for item in sets:
        if "=" not in item:
            continue
        key, value = item.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            continue
        cfg[key] = value
    return cfg


def coerce_types(cfg: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enforce types per assignment.
    port, workers: int
    debug: bool
    log_level and others: str
    """
    out: Dict[str, Any] = {}

    # port
    port_val = cfg.get("port")
    try:
        out["port"] = int(port_val)
    except Exception:
        out["port"] = 0

    # workers
    workers_val = cfg.get("workers")
    try:
        out["workers"] = int(workers_val)
    except Exception:
        out["workers"] = 0

    # debug
    debug_val = cfg.get("debug")
    if isinstance(debug_val, bool):
        out["debug"] = debug_val
    else:
        s = str(debug_val).lower().strip()
        out["debug"] = s in {"true", "1", "yes", "on"}

    # log_level
    log_val = cfg.get("log_level")
    out["log_level"] = str(log_val)

    # api_key: mask always
    out["api_key"] = "****"

    return out


@app.get("/effective-config")
async def effective_config(request: Request):
    """
    Merge config layers and apply ?set= overrides.
    """
    # 1. defaults
    cfg = DEFAULTS.copy()

    # 2. YAML
    yaml_cfg = load_yaml_config()
    cfg.update(yaml_cfg)

    # 3. .env
    dotenv_cfg = load_dotenv_config()
    cfg.update(dotenv_cfg)

    # 4. OS env
    os_cfg = load_os_env_config()
    cfg.update(os_cfg)

    # 5. CLI overrides via query ?set=key=value
    sets = request.query_params.getlist("set")
    cfg = apply_cli_overrides(cfg, sets)

    # Coerce types and mask api_key
    final_cfg = coerce_types(cfg)
    return final_cfg
