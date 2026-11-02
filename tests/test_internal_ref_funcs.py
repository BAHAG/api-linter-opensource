import json
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

workspace_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(workspace_root / "local_dev"))
sys.path.insert(0, str(workspace_root / "package"))
import internal_ref_funcs
original_argv = sys.argv
sys.argv = sys.argv[:1]
try:
    import linter.internal_ref_funcs as packaged_internal_ref_funcs
finally:
    sys.argv = original_argv


class FakeLogger:
    def __init__(self):
        self.logs = []

    def log_internal_references(self, line, message, key, value):
        self.logs.append({
            "num_line": line,
            "message": message,
            "key": key,
            "value": value,
        })


class ExternalReferenceTests(unittest.TestCase):
    def setUp(self):
        internal_ref_funcs.EXTERNAL_DATA.clear()
        self.logger = FakeLogger()
        self.api_key = patch.object(internal_ref_funcs, "API_KEY", "test-key")
        self.headers = patch.object(internal_ref_funcs, "SWAGGER_HEADERS", {"Authorization": "test-key"})
        self.api_key.start()
        self.headers.start()
        self.addCleanup(self.api_key.stop)
        self.addCleanup(self.headers.stop)

    def check_reference(self, url, response=None, request_error=None):
        reference = f"{url}#/components/schemas/Foo"
        version = url.rsplit("/", 1)[-1]
        metadata = self.response(
            200,
            json.dumps({
                "totalCount": 1,
                "offset": 0,
                "apis": [{
                    "properties": [
                        {"type": "X-Version", "value": version},
                        {"type": "X-Published", "value": "true"},
                    ]
                }],
            }),
        )
        responses = [metadata]
        if request_error:
            responses.append(request_error)
        else:
            responses.append(response)
        request = Mock(side_effect=responses)
        with patch.object(internal_ref_funcs.requests, "get", request), patch.object(
            internal_ref_funcs, "get_line_number_key", return_value=12
        ), patch.object(internal_ref_funcs, "extract_external_metadata"):
            internal_ref_funcs.deep_check_refs(
                {"$ref": reference}, {}, "", self.logger, "Reference does not exist"
            )
        return reference, request

    def response(self, status, body="", content_type="application/json"):
        result = Mock()
        result.status_code = status
        result.text = body
        result.content = body.encode()
        result.headers = {"content-type": content_type}
        result.json.side_effect = lambda: json.loads(body)
        return result

    def test_missing_api_or_domain_logs_error(self):
        cases = (
            ("https://api.swaggerhub.com/apis/acme/catalog/1.0.0", "API not found"),
            ("https://api.swaggerhub.com/domains/acme/common/1.0.0", "Domain not found"),
        )
        for url, body in cases:
            with self.subTest(url=url):
                internal_ref_funcs.EXTERNAL_DATA.clear()
                self.logger.logs.clear()
                reference, _ = self.check_reference(url, self.response(404, body))
                self.assertEqual(len(self.logger.logs), 1)
                log = self.logger.logs[0]
                self.assertEqual(log["message"], f"SwaggerHub API/domain or version does not exist: {url}")
                self.assertEqual(log["num_line"], 12)
                self.assertEqual(log["key"], '."$ref"')
                self.assertEqual(log["value"], reference)

    def test_explicit_version_and_unpublished_responses_are_classified(self):
        cases = (
            ("Version not found", "SwaggerHub version does not exist"),
            ("This version is unpublished", "SwaggerHub API/domain version is unpublished"),
        )
        for body, message in cases:
            with self.subTest(body=body):
                internal_ref_funcs.EXTERNAL_DATA.clear()
                self.logger.logs.clear()
                url = "https://api.swaggerhub.com/apis/acme/catalog/1.0.0"
                self.check_reference(url, self.response(404, body))
                self.assertEqual(self.logger.logs[0]["message"], f"{message}: {url}")

        internal_ref_funcs.EXTERNAL_DATA.clear()
        self.logger.logs.clear()
        url = "https://api.swaggerhub.com/domains/acme/common/1.0.0"
        self.check_reference(url, self.response(200, '{"published": false}'))
        self.assertEqual(
            self.logger.logs[0]["message"],
            f"SwaggerHub API/domain version is unpublished: {url}",
        )

    def test_unpublished_domain_version_is_checked_through_registry_metadata(self):
        version_url = "https://api.swaggerhub.com/domains/BAHAG/api-customer-domain/3.0.15"
        metadata_url = "https://api.swaggerhub.com/domains/BAHAG/api-customer-domain"
        metadata = self.response(
            200,
            json.dumps({
                "totalCount": 1,
                "offset": 0,
                "apis": [{
                    "properties": [
                        {"type": "X-Version", "value": "3.0.15"},
                        {"type": "X-Published", "value": "false"},
                    ]
                }],
            }),
        )
        reference = f"{version_url}#/components/schemas/Foo"
        with patch.object(internal_ref_funcs.requests, "get", return_value=metadata) as request, patch.object(
            internal_ref_funcs, "get_line_number_key", return_value=12
        ):
            internal_ref_funcs.deep_check_refs(
                {"$ref": reference}, {}, "", self.logger, "Reference does not exist"
            )

        request.assert_called_once()
        self.assertEqual(request.call_args_list[0].args[0], metadata_url)
        self.assertEqual(len(self.logger.logs), 1)
        self.assertEqual(
            self.logger.logs[0]["message"],
            f"SwaggerHub API/domain version is unpublished: {version_url}",
        )
        self.assertEqual(self.logger.logs[0]["value"], reference)

    def test_repeated_refs_reuse_unpublished_metadata_but_log_each_location(self):
        version_url = "https://api.swaggerhub.com/domains/BAHAG/api-customer-domain/3.0.15"
        metadata_url = "https://api.swaggerhub.com/domains/BAHAG/api-customer-domain"
        metadata = self.response(
            200,
            json.dumps({
                "totalCount": 1,
                "offset": 0,
                "apis": [{
                    "properties": [
                        {"type": "X-Version", "value": "3.0.15"},
                        {"type": "X-Published", "value": "false"},
                    ]
                }],
            }),
        )
        spec = {
            "first": {"$ref": f"{version_url}#/components/schemas/Foo"},
            "second": {"$ref": f"{version_url}#/components/schemas/Bar"},
        }
        with patch.object(internal_ref_funcs.requests, "get", return_value=metadata) as request, patch.object(
            internal_ref_funcs, "get_line_number_key", side_effect=(12, 18)
        ):
            internal_ref_funcs.deep_check_refs(spec, {}, "", self.logger, "Reference does not exist")

        request.assert_called_once()
        self.assertEqual(request.call_args.args[0], metadata_url)
        self.assertEqual([log["num_line"] for log in self.logger.logs], [12, 18])
        self.assertTrue(all("unpublished" in log["message"] for log in self.logger.logs))

    def test_packaged_resolver_checks_api_publication_metadata(self):
        packaged_internal_ref_funcs.EXTERNAL_DATA.clear()
        version_url = "https://api.swaggerhub.com/apis/acme/catalog/1.0.0"
        metadata_url = "https://api.swaggerhub.com/apis/acme/catalog"
        metadata = self.response(
            200,
            json.dumps({
                "totalCount": 1,
                "offset": 0,
                "apis": [{
                    "properties": [
                        {"type": "X-Version", "value": "1.0.0"},
                        {"type": "X-Published", "value": "false"},
                    ]
                }],
            }),
        )
        reference = f"{version_url}#/components/schemas/Foo"
        with patch.object(packaged_internal_ref_funcs, "API_KEY", "test-key"), patch.object(
            packaged_internal_ref_funcs,
            "SWAGGER_METADATA_HEADERS",
            {"Authorization": "test-key", "Accept": "application/json"},
        ), patch.object(packaged_internal_ref_funcs.requests, "get", return_value=metadata) as request, patch.object(
            packaged_internal_ref_funcs, "get_line_number_key", return_value=9
        ):
            packaged_internal_ref_funcs.deep_check_refs(
                {"$ref": reference}, {}, "", self.logger, "Reference does not exist"
            )

        request.assert_called_once()
        self.assertEqual(request.call_args.args[0], metadata_url)
        self.assertEqual(self.logger.logs[-1]["num_line"], 9)
        self.assertEqual(
            self.logger.logs[-1]["message"],
            f"SwaggerHub API/domain version is unpublished: {version_url}",
        )

    def test_auth_rate_limit_server_and_network_failures_are_not_target_errors(self):
        for status in (400, 401, 403, 429, 500):
            with self.subTest(status=status):
                internal_ref_funcs.EXTERNAL_DATA.clear()
                self.logger.logs.clear()
                self.check_reference(
                    "https://api.swaggerhub.com/apis/acme/catalog/1.0.0",
                    self.response(status),
                )
                self.assertEqual(self.logger.logs, [])

        internal_ref_funcs.EXTERNAL_DATA.clear()
        self.check_reference(
            "https://api.swaggerhub.com/apis/acme/catalog/1.0.0",
            request_error=internal_ref_funcs.RequestException("offline"),
        )
        self.assertEqual(self.logger.logs, [])

    def test_successful_external_fragment_and_missing_fragment(self):
        url = "https://api.swaggerhub.com/apis/acme/catalog/1.0.0"
        body = "components:\n  schemas:\n    Foo:\n      type: string\n"
        reference, _ = self.check_reference(url, self.response(200, body, "application/yaml"))
        self.assertEqual(self.logger.logs, [])

        internal_ref_funcs.EXTERNAL_DATA.clear()
        self.logger.logs.clear()
        reference = f"{url}#/components/schemas/Missing"
        response = self.response(200, body, "application/yaml")
        with patch.object(internal_ref_funcs.requests, "get", return_value=response), patch.object(
            internal_ref_funcs, "get_line_number_key", return_value=12
        ), patch.object(internal_ref_funcs, "extract_external_metadata"):
            internal_ref_funcs.deep_check_refs(
                {"$ref": reference}, {}, "", self.logger, "Reference does not exist"
            )
        self.assertEqual(self.logger.logs[0]["message"], "Reference does not exist")

    def test_local_reference_resolution_is_unchanged(self):
        with patch.object(internal_ref_funcs.requests, "get") as request:
            internal_ref_funcs.deep_check_refs(
                {"$ref": "#/components/schemas/Foo"},
                {"components": {"schemas": {"Foo": {"type": "string"}}}},
                "",
                self.logger,
                "Reference does not exist",
            )
        request.assert_not_called()
        self.assertEqual(self.logger.logs, [])


if __name__ == "__main__":
    unittest.main()
