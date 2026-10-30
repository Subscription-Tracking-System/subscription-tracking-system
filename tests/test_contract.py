"""Contract acceptance checks; these are not tests of an implemented API server."""

import copy
import unittest

import yaml

from scripts.validate_contract import (
    ROOT, ContractError, StrictLoader, load_document, make_validator, validate_document,
)


class ContractAcceptanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = load_document(ROOT / "api" / "openapi.yaml")
        cls.new_subscription = {
            "name": "Netflix", "price": 15.99, "currency": "USD",
            "billingCycle": "MONTHLY", "renewalDate": "2026-11-01T09:00:00Z",
        }

    def assert_payload(self, name, value, *, valid):
        validator = make_validator(self.document, {"$ref": f"#/components/schemas/{name}"})
        errors = list(validator.iter_errors(value))
        self.assertEqual(not errors, valid, [error.message for error in errors])

    def test_contract_and_all_documented_examples_validate(self):
        result = validate_document(self.document)
        self.assertEqual(result["result"], "passed")

    def test_first_release_operations_match_the_agreed_scope(self):
        result = validate_document(self.document)
        self.assertEqual(set(result["operations"]), {
            "GET /subscriptions", "POST /subscriptions", "GET /subscriptions/{id}",
            "PATCH /subscriptions/{id}", "DELETE /subscriptions/{id}", "GET /dashboard/summary",
        })

    def test_all_supported_original_currencies_are_accepted(self):
        for currency in ["TRY", "USD", "EUR"]:
            with self.subTest(currency=currency):
                self.assert_payload("NewSubscription", {**self.new_subscription, "currency": currency}, valid=True)

    def test_unsupported_currency_is_rejected(self):
        self.assert_payload("NewSubscription", {**self.new_subscription, "currency": "GBP"}, valid=False)

    def test_negative_price_is_rejected(self):
        self.assert_payload("NewSubscription", {**self.new_subscription, "price": -0.01}, valid=False)

    def test_free_subscription_is_accepted(self):
        self.assert_payload("NewSubscription", {**self.new_subscription, "price": 0}, valid=True)

    def test_formatted_price_string_is_rejected(self):
        self.assert_payload("NewSubscription", {**self.new_subscription, "price": "1.250,00"}, valid=False)

    def test_blank_name_is_rejected(self):
        for name in ["", "   ", "\n\t"]:
            with self.subTest(name=repr(name)):
                self.assert_payload("NewSubscription", {**self.new_subscription, "name": name}, valid=False)

    def test_each_required_create_field_is_enforced(self):
        for field in self.new_subscription:
            with self.subTest(field=field):
                value = dict(self.new_subscription)
                del value[field]
                self.assert_payload("NewSubscription", value, valid=False)

    def test_client_cannot_supply_resource_owner(self):
        self.assert_payload("NewSubscription", {**self.new_subscription, "userId": "another-user"}, valid=False)

    def test_client_cannot_set_creation_status(self):
        self.assert_payload("NewSubscription", {**self.new_subscription, "status": "CANCELLED"}, valid=False)

    def test_both_agreed_billing_cycles_are_accepted(self):
        for cycle in ["MONTHLY", "YEARLY"]:
            with self.subTest(cycle=cycle):
                self.assert_payload("NewSubscription", {**self.new_subscription, "billingCycle": cycle}, valid=True)

    def test_weekly_cycle_is_outside_the_first_release(self):
        self.assert_payload("NewSubscription", {**self.new_subscription, "billingCycle": "WEEKLY"}, valid=False)

    def test_invalid_or_ambiguous_timestamps_are_rejected(self):
        for timestamp in ["tomorrow", "2026-02-30T09:00:00Z", "2026-11-01", "2026-11-01T09:00:00"]:
            with self.subTest(timestamp=timestamp):
                self.assert_payload("NewSubscription", {**self.new_subscription, "renewalDate": timestamp}, valid=False)

    def test_timestamp_with_explicit_offset_is_accepted(self):
        value = {**self.new_subscription, "renewalDate": "2026-11-01T12:00:00+03:00"}
        self.assert_payload("NewSubscription", value, valid=True)

    def test_empty_patch_is_rejected(self):
        self.assert_payload("UpdateSubscription", {}, valid=False)

    def test_unknown_patch_field_is_rejected(self):
        self.assert_payload("UpdateSubscription", {"userId": "another-user"}, valid=False)

    def test_all_lifecycle_states_can_be_patched(self):
        for status in ["ACTIVE", "PAUSED", "CANCELLED"]:
            with self.subTest(status=status):
                self.assert_payload("UpdateSubscription", {"status": status}, valid=True)

    def test_unknown_state_is_rejected(self):
        self.assert_payload("UpdateSubscription", {"status": "DELETED"}, valid=False)

    def test_null_does_not_clear_a_patch_field(self):
        self.assert_payload("UpdateSubscription", {"price": None}, valid=False)

    def test_empty_dashboard_is_a_valid_result(self):
        self.assert_payload("DashboardSummary", {
            "totalMonthlyExpense": 0, "baseCurrency": "TRY", "activeSubscriptionsCount": 0,
        }, valid=True)

    def test_dashboard_count_cannot_be_negative_or_fractional(self):
        for count in [-1, 1.5]:
            with self.subTest(count=count):
                self.assert_payload("DashboardSummary", {
                    "totalMonthlyExpense": 0, "baseCurrency": "TRY", "activeSubscriptionsCount": count,
                }, valid=False)

    def test_unsupported_dashboard_currency_is_rejected(self):
        self.assert_payload("BaseCurrency", "GBP", valid=False)

    def test_duplicate_yaml_keys_fail_instead_of_overwriting(self):
        with self.assertRaisesRegex(ContractError, "Duplicate YAML key"):
            yaml.load("openapi: 3.1.0\nopenapi: 3.0.0\n", Loader=StrictLoader)

    def test_missing_reference_is_reported(self):
        document = copy.deepcopy(self.document)
        document["paths"]["/subscriptions"]["post"]["requestBody"]["content"]["application/json"]["schema"] = {
            "$ref": "#/components/schemas/MissingSchema",
        }
        with self.assertRaisesRegex(ContractError, "Unresolved reference"):
            validate_document(document)

    def test_invalid_documented_response_is_reported(self):
        document = copy.deepcopy(self.document)
        document["components"]["examples"]["ActiveSubscription"]["value"]["price"] = -1
        with self.assertRaises(ContractError):
            validate_document(document)

    def test_problem_example_status_matches_http_status(self):
        document = copy.deepcopy(self.document)
        document["components"]["responses"]["Unauthorized"]["content"]["application/problem+json"]["examples"]["unauthorized"]["value"]["status"] = 404
        with self.assertRaisesRegex(ContractError, "problem status must equal HTTP 401"):
            validate_document(document)

    def test_no_content_response_cannot_advertise_a_body(self):
        document = copy.deepcopy(self.document)
        document["paths"]["/subscriptions/{id}"]["delete"]["responses"]["204"]["content"] = {
            "application/json": {"schema": {"type": "object"}},
        }
        with self.assertRaisesRegex(ContractError, "204 must have no response body"):
            validate_document(document)


if __name__ == "__main__":
    unittest.main()
