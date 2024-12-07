import pytest
from translator import ConfigConverter, ExpressionEvaluator, ConfigLanguageError


def test_variables_conversion():
    variables = {
        'var1': 10,
        'var2': 20
    }

    expected = [
        "var1 = 10",
        "var2 = 20"
    ]

    converter = ConfigConverter(variables, {})
    result = converter.convert()
    assert result == "\n".join(expected)


def test_arrays_conversion():
    arrays_example = {
        'array1': [1, 2, 3, 4, 5],
        'array2': ["one", "two", "three"]
    }

    expected = [
        "array1 = ( 1 2 3 4 5 )\n"
        "array2 = ( one two three )"
    ]

    converter = ConfigConverter(arrays_example, {})
    result = converter.convert()
    assert result == "\n".join(expected)


def test_dictionaries_conversion():
    dictionaries_example = {
        'settings': {
            'hostname': "server01",
            'ip': "192.168.1.1",
            'ports': [80, 443, 22],
            'config': {
                'retries': 5,
                'timeout': 30
            }
        }
    }

    expected = [
        "( {",
        "settings {",
        "  hostname = server01",
        "  ip = \"192.168.1.1\"",
        "  ports = ( 80 443 22 )",
        "  config {",
        "    retries = 5",
        "    timeout = 30",
        "  }",
        "}",
        "} )"
    ]

    converter = ConfigConverter([dictionaries_example], {})
    result = converter.convert()
    assert result == "\n".join(expected)


def test_expressions_evaluation():
    constants = {
        'var1': 10,
        'var2': 20
    }
    expressions = {
        'calculation': "?[var1 + 2]",
        'subtraction': "?[var2 - 6]",
        'multiplication': "?[var2 * var1]",
        'mod_example': "?[mod(var2, 3)]",
        'concat_example': "?[concat('Hello', ' ', 'World!')]"
    }

    evaluator = ExpressionEvaluator(constants)

    expected_results = {
        'calculation': '12',
        'subtraction': '14',
        'multiplication': '200',
        'mod_example': '2',
        'concat_example': 'Hello World!'
    }

    for name, expr in expressions.items():
        expected_result = expected_results[name]
        assert evaluator.evaluate(expr) == expected_result


def test_string_conversion():
    strings = {
        "stringExample": "Hello, world!"
    }

    expected = [
        "stringExample = Hello, world!"
    ]

    converter = ConfigConverter(strings, {})
    result = converter.convert()
    assert result == "\n".join(expected)


def test_invalid_expression():
    evaluator = ExpressionEvaluator({'x': 5})

    with pytest.raises(ConfigLanguageError):
        evaluator.evaluate("?[invalid_expression(x)]")

