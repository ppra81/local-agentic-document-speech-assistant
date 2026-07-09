from assistant.adapters.base import OptionalDependencyAdapter


class MissingAdapter(OptionalDependencyAdapter):
    name = "missing"
    task = "test"
    dependency_name = "definitely_missing_optional_ai_dependency"

    def predict(self, input_data):
        if not self.dependency_available():
            return {"warning": self.fallback_message()}
        return {}


def test_missing_optional_dependencies_are_handled_gracefully():
    output = MissingAdapter().predict({})
    assert output["warning"] == "Optional dependency not installed. Falling back to mock adapter."

