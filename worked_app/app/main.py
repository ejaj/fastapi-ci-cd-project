from enum import Enum
from pathlib import Path
from typing import Optional
from worked_app.app.database import Base, engine

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse

app = FastAPI(title="FastAPI Worked App")

from routers.items import router as item_router
from routers.query_demo import router as query_demo_router
from routers.path_demo import router as path_demo_router
from routers.query_models import router as query_model_router
from routers.body_params_demo import router as body_params_demo_router
from routers.body_fields import router as body_field_router
from routers.body_nested import router as body_nested_router
from routers.body_nested import router as body_nested_nested_router
from routers.body_extra_data_types import router as body_extra_data_type_router
from routers.body_request_examples import router as body_request_examples_router
from routers.cookie_params import router as cookie_params_router
from routers.header_params import router as header_params_router
from routers.cookie_model_demo import router as cookie_model_demo_router
from routers.header_model_demo import router as header_model_demo_router
from routers.response_models_demo import router as response_models_demo_router
from routers.extra_models_demo import router as extra_models_demo_router
from routers.status_codes_demo import router as status_codes_demo_router
from routers.form_data_demo import router as form_data_demo_router
from routers.form_models_demo import router as form_models_demo_router
from routers.file_uploads import router as form_file_uploads_router
from routers.forms_and_files import router as forms_and_files_router
from routers.handle_errors import router as handle_errors_router
from routers.path_operation_config import router as path_operation_config_router
from routers.json_encoder import router as json_encoder_router
from routers.body_update import router as body_update_router
from routers.dependencies_demo import router as dependencies_demo_router
from routers.classes_dependencies import router as classes_dependencies_router
from routers.sub_dependencies import router as sub_dependencies_router
from routers.dependencies_path_operation import router as dependencies_path_operation_router
from routers.global_dependencies import router as global_dependencies_router
from routers.dependencies_with_yield import router as dependencies_with_return_router


Base.metadata.create_all(bind=engine)


@app.get("/")
async def root():
    return {"message": "Hello from fastAPI worker-based app!!"}


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello, {name}!"}


# ─────────────────────────────────────────────────────────────
# 1) Basic path parameter (no type → string)
#    /items/foo  → {"item_id": "foo"}
# ─────────────────────────────────────────────────────────────

@app.get("items/{item_id}")
async def read_item_free(item_id):
    return {"item_id": item_id, "type": "str (implicit)"}


# ─────────────────────────────────────────────────────────────
# 2) Path parameter with type (int)
#    /items-typed/3  → {"item_id": 3}
#    /items-typed/foo → 422 validation error
# ─────────────────────────────────────────────────────────────
@app.get("/items-typed/{item_id}")
async def read_item_typed(item_id: int):
    return {"item_id": item_id, "type": "int (validated)"}


# ─────────────────────────────────────────────────────────────
# 3) Order matters
#    /users/me must come BEFORE /users/{user_id}
# ─────────────────────────────────────────────────────────────
@app.get("/users/me")
async def read_user_me():
    return {"user_id": "the current user"}


@app.get("/users/{user_id}")
async def read_user(user_id: str):
    return {"user_id": user_id}


# ─────────────────────────────────────────────────────────────
# 4) Enum-restricted path parameter
#    Allowed: /models/alexnet, /models/resnet, /models/lenet
# ─────────────────────────────────────────────────────────────
class ModelName(str, Enum):
    alexnet = "alexnet"
    resnet = "resnet"
    lenet = "lenet"


@app.get("/models/{model_name}")
async def get_model(model_name: ModelName):
    if model_name is ModelName.alexnet:
        return {"model_name": model_name, "message": "Deep Learning FTW!"}
    if model_name.value == "lenet":
        return {"model_name": model_name, "message": "LeCNN all the images"}
    return {"model_name": model_name, "message": "Have some residuals"}


# ─────────────────────────────────────────────────────────────
# 5) Path converter (:path) — can include slashes
#    /files/home/user/readme.txt → "home/user/readme.txt"
#    If you need a leading slash, call: /files//home/user/file.txt
# ─────────────────────────────────────────────────────────────

@app.get("/files/{file_path:path}")
async def echo_path(file_path: str, require_ext: Optional[bool] = None):
    """
    Echo the captured file_path. Optionally enforce an extension:
      /files/some/path?require_ext=true
    """
    if require_ext:
        if "." not in Path(file_path).name:
            raise HTTPException(status_code=400, detail="File extension required")
    return {"file_path": file_path}


# ─────────────────────────────────────────────────────────────
# 6) Optional: real file serving demo (from ./public)
#    - Put some test file under ./public (e.g., public/readme.txt)
#    - GET /serve/public/readme.txt
# ─────────────────────────────────────────────────────────────
PUBLIC_DIR = Path(__file__).parent / "public"
PUBLIC_DIR.mkdir(exist_ok=True)


@app.get("/serve/{file_path:path}")
async def serve_file(file_path: str):
    """
    Serve a file from the local ./public directory safely.
    Prevent path traversal and return 404 if not found.
    """
    requested = (PUBLIC_DIR / file_path).resolve()
    if not str(requested).startswith(str(PUBLIC_DIR.resolve())):
        raise HTTPException(status_code=400, detail="Invalid path")

    if not requested.exists() or not requested.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(requested)


# ─────────────────────────────────────────────────────────────
# 7) Fallback route for /files (exact path) to show behavior
#    /files → 404 by default; here we make it explicit.
# ─────────────────────────────────────────────────────────────
@app.get("/files")
async def files_root():
    return JSONResponse(
        {"message": "Please call /files/{file_path}. Example: /files/docs/readme.txt"}
    )


app.include_router(item_router)
app.include_router(query_demo_router)
app.include_router(path_demo_router)
app.include_router(query_model_router)
app.include_router(query_demo_router)
app.include_router(body_params_demo_router)
app.include_router(body_field_router)
app.include_router(body_nested_router)
app.include_router(body_request_examples_router)
app.include_router(body_nested_nested_router)
app.include_router(body_extra_data_type_router)
app.include_router(cookie_params_router)
app.include_router(header_params_router)
app.include_router(cookie_model_demo_router)
app.include_router(header_model_demo_router)
app.include_router(response_models_demo_router)
app.include_router(extra_models_demo_router)
app.include_router(status_codes_demo_router)
app.include_router(form_data_demo_router)
app.include_router(form_models_demo_router)
app.include_router(form_file_uploads_router)
app.include_router(forms_and_files_router)
app.include_router(handle_errors_router)
app.include_router(path_operation_config_router)
app.include_router(json_encoder_router)
app.include_router(body_update_router)
app.include_router(dependencies_demo_router)
app.include_router(classes_dependencies_router)
app.include_router(sub_dependencies_router)
app.include_router(dependencies_path_operation_router)
app.include_router(global_dependencies_router)
app.include_router(dependencies_with_return_router)
