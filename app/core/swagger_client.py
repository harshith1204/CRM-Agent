from __future__ import annotations

from typing import Any, Dict, Optional, Tuple
import json
import requests
from fastapi import HTTPException

from .config import CFG, logger


class SwaggerClient:
    def __init__(self, base_url: str, spec_url: str, auth_header: Optional[str] = None, auth_value: Optional[str] = None):
        self.base_url = base_url.rstrip("/")
        self.spec_url = spec_url
        self.session = requests.Session()
        if auth_header and auth_value:
            self.session.headers[auth_header] = auth_value
        self.spec: Dict[str, Any] = {}
        try:
            self._load_spec()
        except Exception as e:  # pragma: no cover - network dependent
            logger.warning(f"Unable to load OpenAPI spec at startup: {e}")

    def _load_spec(self):
        resp = self.session.get(self.spec_url, timeout=20)
        resp.raise_for_status()
        self.spec = resp.json()

    def call(
        self,
        *,
        path: Optional[str] = None,
        method: Optional[str] = None,
        operation_id: Optional[str] = None,
        path_params: Optional[Dict[str, Any]] = None,
        query: Optional[Dict[str, Any]] = None,
        body: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        if operation_id and not (path and method):
            path, method = self._resolve_operation_id(operation_id)
        if not path or not method:
            raise ValueError("Provide either (operation_id) or (path & method)")
        url = self._format_path(path, path_params or {})
        req_headers = {}
        if headers:
            req_headers.update(headers)
        url = f"{self.base_url}{url}"
        m = method.upper()
        data = json.dumps(body) if body is not None else None
        resp = self.session.request(
            m,
            url,
            params=query,
            data=data,
            headers={**req_headers, "Content-Type": "application/json"},
            timeout=30,
        )
        if not resp.ok:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        try:
            return resp.json()
        except Exception:
            return {"text": resp.text}

    def _resolve_operation_id(self, operation_id: str) -> Tuple[str, str]:
        paths = self.spec.get("paths", {})
        for p, methods in paths.items():
            for m, op in methods.items():
                if isinstance(op, dict) and op.get("operationId") == operation_id:
                    return p, m
        raise ValueError(f"operationId '{operation_id}' not found in spec")

    @staticmethod
    def _format_path(path: str, params: Dict[str, Any]) -> str:
        for k, v in params.items():
            path = path.replace("{" + k + "}", str(v))
        return path


swagger: Optional[SwaggerClient] = None
if CFG.SWAGGER_BASE_URL and CFG.SWAGGER_SPEC_URL:
    swagger = SwaggerClient(
        base_url=CFG.SWAGGER_BASE_URL,
        spec_url=CFG.SWAGGER_SPEC_URL,
        auth_header=CFG.SWAGGER_AUTH_HEADER,
        auth_value=CFG.SWAGGER_AUTH_VALUE,
    )

