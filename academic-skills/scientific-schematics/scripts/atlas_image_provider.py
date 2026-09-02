"""Atlas Cloud image generation for the scientific schematics skill."""

from __future__ import annotations

import time
from typing import Any

import requests


API_BASE_URL = "https://api.atlascloud.ai"
CATALOG_URL = f"{API_BASE_URL}/api/v1/models"
DEFAULT_MODEL = "google/nano-banana-2/text-to-image"
TERMINAL_FAILURES = {"failed", "canceled", "cancelled"}
TRANSIENT_STATUS_CODES = {408, 429, 500, 502, 503, 504}


def _unwrap(payload: Any) -> Any:
    if isinstance(payload, dict) and isinstance(payload.get("data"), (dict, list)):
        return payload["data"]
    return payload


class AtlasImageProvider:
    """Generate one image per call through Atlas Cloud's async image API."""

    def __init__(
        self,
        api_key: str,
        *,
        model: str = DEFAULT_MODEL,
        http: Any = requests,
        sleep: Any = time.sleep,
    ) -> None:
        if not api_key:
            raise ValueError("ATLASCLOUD_API_KEY is required for the Atlas provider")
        self.api_key = api_key
        self.model = model
        self.http = http
        self.sleep = sleep

    @property
    def headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
            "User-Agent": "academic-skills-scientific-schematics/1.0",
        }

    def _discover(self, timeout: float) -> tuple[str, str, dict[str, Any]]:
        catalog_response = self.http.get(
            CATALOG_URL,
            headers={"Accept": "application/json", "User-Agent": self.headers["User-Agent"]},
            timeout=timeout,
        )
        catalog_response.raise_for_status()
        catalog = _unwrap(catalog_response.json())
        model_info = next(
            (item for item in catalog if item.get("model") == self.model),
            None,
        )
        if not model_info:
            raise ValueError(f"Atlas Cloud model is not available: {self.model}")

        schema_response = self.http.get(
            model_info["schema"],
            headers={"Accept": "application/json", "User-Agent": self.headers["User-Agent"]},
            timeout=timeout,
        )
        schema_response.raise_for_status()
        schema = schema_response.json()

        run_path = None
        result_path = None
        for path, operations in schema.get("paths", {}).items():
            if operations.get("x-api-name") == "model_run":
                run_path = path
            elif operations.get("x-api-name") == "model_result":
                result_path = path
        if not run_path or not result_path:
            raise ValueError("Atlas Cloud schema is missing model_run or model_result")
        return run_path, result_path, schema

    @staticmethod
    def _validate(schema: dict[str, Any], payload: dict[str, Any]) -> None:
        input_schema = schema.get("components", {}).get("schemas", {}).get("Input", {})
        properties = input_schema.get("properties", {})
        unsupported = sorted(set(payload) - set(properties))
        if unsupported:
            raise ValueError(f"Unsupported Atlas input fields: {', '.join(unsupported)}")
        missing = [field for field in input_schema.get("required", []) if field not in payload]
        if missing:
            raise ValueError(f"Missing Atlas input fields: {', '.join(missing)}")
        for field, value in payload.items():
            choices = properties.get(field, {}).get("enum")
            if choices and value not in choices:
                raise ValueError(f"Invalid {field!r}; expected one of: {', '.join(choices)}")

    def _poll(
        self,
        url: str,
        *,
        poll_interval: float,
        max_polls: int,
        timeout: float,
    ) -> dict[str, Any]:
        last_error = None
        for attempt in range(max_polls):
            response = None
            try:
                response = self.http.get(url, headers=self.headers, timeout=timeout)
                if response.status_code in TRANSIENT_STATUS_CODES:
                    raise requests.HTTPError(f"Transient HTTP {response.status_code}")
                response.raise_for_status()
                prediction = _unwrap(response.json())
                last_error = None
            except requests.HTTPError as error:
                status_code = response.status_code if response is not None else None
                if status_code not in TRANSIENT_STATUS_CODES:
                    raise
                last_error = error
                if attempt + 1 >= max_polls:
                    raise
                self.sleep(min(poll_interval * (2**attempt), 10.0))
                continue
            except (requests.ConnectionError, requests.Timeout) as error:
                last_error = error
                if attempt + 1 >= max_polls:
                    raise
                self.sleep(min(poll_interval * (2**attempt), 10.0))
                continue

            status = str(prediction.get("status") or "").lower()
            if status == "completed":
                return prediction
            if status in TERMINAL_FAILURES:
                detail = prediction.get("error") or prediction.get("message") or status
                raise RuntimeError(f"Atlas Cloud generation failed: {detail}")
            if attempt + 1 < max_polls:
                self.sleep(min(poll_interval * (2**attempt), 10.0))

        detail = f": {last_error}" if last_error else ""
        raise TimeoutError(f"Atlas prediction did not complete after {max_polls} polls{detail}")

    def generate(
        self,
        prompt: str,
        *,
        aspect_ratio: str = "4:3",
        resolution: str = "2k",
        output_format: str = "jpeg",
        poll_interval: float = 1.0,
        max_polls: int = 30,
        timeout: float = 60,
    ) -> bytes:
        """Submit one paid generation POST, then poll and download its output."""
        run_path, result_path, schema = self._discover(timeout)
        payload = {
            "model": self.model,
            "prompt": prompt,
            "aspect_ratio": aspect_ratio,
            "resolution": resolution,
            "output_format": output_format,
        }
        self._validate(schema, payload)

        # This paid generation request is deliberately submitted exactly once.
        response = self.http.post(
            f"{API_BASE_URL}{run_path}",
            headers={**self.headers, "Content-Type": "application/json"},
            json=payload,
            timeout=timeout,
        )
        response.raise_for_status()
        prediction = _unwrap(response.json())
        prediction_id = prediction.get("id")
        if not prediction_id:
            raise RuntimeError("Atlas Cloud response did not include a prediction id")

        if str(prediction.get("status") or "").lower() != "completed":
            result_url = f"{API_BASE_URL}{result_path.replace('{request_id}', prediction_id)}"
            prediction = self._poll(
                result_url,
                poll_interval=poll_interval,
                max_polls=max_polls,
                timeout=timeout,
            )

        outputs = prediction.get("outputs") or []
        if not outputs or not isinstance(outputs[0], str) or not outputs[0].startswith("https://"):
            raise RuntimeError("Atlas Cloud completed without an HTTPS image output")

        image_response = self.http.get(outputs[0], timeout=timeout)
        image_response.raise_for_status()
        if not image_response.content:
            raise RuntimeError("Atlas Cloud returned an empty image")
        if output_format == "png" and not image_response.content.startswith(b"\x89PNG\r\n\x1a\n"):
            raise RuntimeError("Atlas Cloud returned a non-PNG image")
        if output_format == "jpeg" and not image_response.content.startswith(b"\xff\xd8\xff"):
            raise RuntimeError("Atlas Cloud returned a non-JPEG image")
        return image_response.content
