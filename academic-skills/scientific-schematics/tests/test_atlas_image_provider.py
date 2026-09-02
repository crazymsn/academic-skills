import sys
import unittest
from pathlib import Path
from unittest import mock

import requests


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from atlas_image_provider import AtlasImageProvider, DEFAULT_MODEL  # noqa: E402
from generate_schematic_ai import ScientificSchematicGenerator  # noqa: E402


SCHEMA = {
    "paths": {
        "/api/v1/model/generateImage": {"x-api-name": "model_run"},
        "/api/v1/model/prediction/{request_id}": {"x-api-name": "model_result"},
    },
    "components": {
        "schemas": {
            "Input": {
                "required": ["model", "prompt"],
                "properties": {
                    "model": {"type": "string"},
                    "prompt": {"type": "string"},
                    "aspect_ratio": {"enum": ["4:3"]},
                    "resolution": {"enum": ["2k"]},
                    "output_format": {"enum": ["jpeg"]},
                },
            }
        }
    },
}


class FakeResponse:
    def __init__(self, payload=None, *, content=b"", status_code=200):
        self.payload = payload
        self.content = content
        self.status_code = status_code

    def json(self):
        return self.payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")


class FakeHTTP:
    def __init__(self, *, gets, posts):
        self.gets = list(gets)
        self.posts = list(posts)
        self.get_calls = []
        self.post_calls = []

    def get(self, url, **kwargs):
        self.get_calls.append((url, kwargs))
        response = self.gets.pop(0)
        if isinstance(response, Exception):
            raise response
        return response

    def post(self, url, **kwargs):
        self.post_calls.append((url, kwargs))
        response = self.posts.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def discovery_gets(*remaining):
    return [
        FakeResponse({"data": [{"model": DEFAULT_MODEL, "schema": "https://schema.test/model.json"}]}),
        FakeResponse(SCHEMA),
        *remaining,
    ]


class AtlasImageProviderTests(unittest.TestCase):
    def test_discovers_submits_once_polls_and_downloads(self):
        http = FakeHTTP(
            gets=discovery_gets(
                FakeResponse({"data": {"id": "pred-1", "status": "completed", "outputs": ["https://cdn.test/image.png"]}}),
                FakeResponse(content=b"\xff\xd8\xffjpeg-data"),
            ),
            posts=[FakeResponse({"data": {"id": "pred-1", "status": "processing"}})],
        )
        provider = AtlasImageProvider("test-key", http=http, sleep=lambda _: None)

        image = provider.generate("scientific flowchart")

        self.assertEqual(image, b"\xff\xd8\xffjpeg-data")
        self.assertEqual(len(http.post_calls), 1)
        self.assertEqual(http.post_calls[0][1]["json"]["model"], DEFAULT_MODEL)

    def test_post_network_failure_is_not_retried(self):
        http = FakeHTTP(
            gets=discovery_gets(),
            posts=[requests.ConnectionError("connection lost")],
        )
        provider = AtlasImageProvider("test-key", http=http)

        with self.assertRaises(requests.ConnectionError):
            provider.generate("scientific flowchart")

        self.assertEqual(len(http.post_calls), 1)

    def test_retries_only_transient_prediction_get(self):
        http = FakeHTTP(
            gets=discovery_gets(
                FakeResponse(status_code=503),
                FakeResponse({"data": {"id": "pred-2", "status": "completed", "outputs": ["https://cdn.test/image.png"]}}),
                FakeResponse(content=b"\xff\xd8\xffjpeg-data"),
            ),
            posts=[FakeResponse({"data": {"id": "pred-2", "status": "processing"}})],
        )
        sleep = mock.Mock()
        provider = AtlasImageProvider("test-key", http=http, sleep=sleep)

        self.assertEqual(provider.generate("scientific flowchart"), b"\xff\xd8\xffjpeg-data")
        sleep.assert_called_once_with(1.0)
        self.assertEqual(len(http.post_calls), 1)

    def test_does_not_retry_permanent_prediction_error(self):
        http = FakeHTTP(
            gets=discovery_gets(FakeResponse(status_code=401)),
            posts=[FakeResponse({"data": {"id": "pred-3", "status": "processing"}})],
        )
        sleep = mock.Mock()
        provider = AtlasImageProvider("test-key", http=http, sleep=sleep)

        with self.assertRaises(requests.HTTPError):
            provider.generate("scientific flowchart")

        sleep.assert_not_called()
        self.assertEqual(len(http.get_calls), 3)
        self.assertEqual(len(http.post_calls), 1)

    def test_rejects_invalid_input_before_paid_request(self):
        http = FakeHTTP(gets=discovery_gets(), posts=[])
        provider = AtlasImageProvider("test-key", http=http)

        with self.assertRaisesRegex(ValueError, "Invalid 'aspect_ratio'"):
            provider.generate("scientific flowchart", aspect_ratio="16:9")

        self.assertEqual(http.post_calls, [])


class ScientificSchematicGeneratorTests(unittest.TestCase):
    def test_openrouter_remains_the_default_image_provider(self):
        generator = ScientificSchematicGenerator(api_key="openrouter-test")

        self.assertEqual(generator.provider, "openrouter")
        self.assertIsNone(generator.atlas_provider)

    @mock.patch("generate_schematic_ai.AtlasImageProvider")
    def test_atlas_provider_is_explicit_and_routes_image_generation(self, provider_class):
        provider_class.return_value.generate.return_value = b"\xff\xd8\xffjpeg-data"
        generator = ScientificSchematicGenerator(
            api_key="openrouter-test",
            provider="atlas",
            atlas_api_key="atlas-test",
        )

        self.assertEqual(generator.generate_image("scientific flowchart"), b"\xff\xd8\xffjpeg-data")
        provider_class.assert_called_once_with("atlas-test")
        provider_class.return_value.generate.assert_called_once_with("scientific flowchart")

        with self.assertRaisesRegex(ValueError, "requires a .jpg or .jpeg"):
            generator.generate_iterative("scientific flowchart", "diagram.png")


if __name__ == "__main__":
    unittest.main()
