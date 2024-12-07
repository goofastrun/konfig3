import yaml
import re
import argparse
import operator


class ConfigLanguageError(Exception):
    pass


class ExpressionEvaluator:
    """Класс для вычисления константных выражений."""
    def __init__(self, variables=None):
        self.variables = variables or {}

    def evaluate(self, expression):
        try:

            # Убираем маркеры, если они есть
            if expression.startswith("?[") and expression.endswith("]"):
                expression = expression[2:-1]

            # Заменяем переменные на их значения
            for var, value in self.variables.items():
                expression = re.sub(rf'\b{re.escape(var)}\b', str(value), expression)

            # Определяем доступные функции в глобальном контексте eval
            functions = {
                'mod': self._mod,
                'concat': self._concat
            }

            # Пробуем вычислить выражение с использованием функции eval
            result = eval(expression, {"__builtins__": None}, functions)

            # Возвращаем строковое представление результата
            return str(result)  # Преобразуем в строку
        except Exception as e:
            raise ConfigLanguageError(f"Ошибка вычисления выражения: {expression}, {e}")

    def _mod(self, a, b):
        """Реализация функции mod."""
        return operator.mod(a, b)

    def _concat(self, *args):
        """Реализация функции concat для строк и списков."""
        return "".join(map(str, args)) if isinstance(args[0], str) else sum(args, [])


class ConfigConverter:
    def __init__(self, input_data, variables=None):
        self.data = input_data
        self.variables = variables or {}

    def convert(self):
        """Конвертирует YAML данные в учебный конфигурационный язык."""
        return self._process(self.data, 0, is_top_level=True)

    def _process(self, node, indent_level, is_top_level=False):
        indent = "  " * indent_level
        inner_indent = "  " * (indent_level)
        result = []

        if isinstance(node, dict):
            if is_top_level:
                result.append(self._process_dict(node, indent_level, is_top_level=True))
            else:
                result.append(self._process_dict(node, indent_level))
        elif isinstance(node, list):
            result.append(self._process_list(node, indent_level))
        elif isinstance(node, (int, float)):
            result.append(str(node))
        elif isinstance(node, str):
            result.append(self._process_string(node))
        else:
            raise ConfigLanguageError(f"Неподдерживаемый тип данных: {type(node)}")
        return "\n".join(result)

    def _process_dict(self, node, indent_level, is_top_level=False):
        indent = "  " * (indent_level - 1)
        inner_indent = "  " * (indent_level)
        lines = []

        if is_top_level:
            for key, value in node.items():
                if not re.match(r"[_a-zA-Z][_a-zA-Z0-9]*", key):
                    raise ConfigLanguageError(f"Некорректное имя: {key}")
                if isinstance(value, dict):
                    processed_value = self._process(value, indent_level + 1, is_top_level=False)
                    lines.append(f"{key} {processed_value}")
                else:
                    processed_value = self._process(value, indent_level + 1, is_top_level=False)
                    lines.append(f"{key} = {processed_value}")
        else:
            lines.append(f"{{")
            for key, value in node.items():
                if not re.match(r"[_a-zA-Z][_a-zA-Z0-9]*", key):
                    raise ConfigLanguageError(f"Некорректное имя: {key}")
                if isinstance(value, dict):
                    processed_value = self._process(value, indent_level + 1, is_top_level=False)
                    lines.append(f"{inner_indent}{key} {processed_value}")
                else:
                    processed_value = self._process(value, indent_level + 1, is_top_level=False)
                    lines.append(f"{inner_indent}{key} = {processed_value}")
            lines.append(f"{indent}}}")

        return "\n".join(lines)

    def _process_list(self, node, indent_level):
        return f"( {' '.join(self._process(item, indent_level) for item in node)} )"

    def _process_string(self, node):
        evaluator = ExpressionEvaluator(self.variables)  # Используем текущие переменные
        if node.startswith("?[") and node.endswith("]"):  # Проверяем, является ли это выражением
            return evaluator.evaluate(node)  # Вычисляем выражение
        elif re.match(r"[_a-zA-Z][_a-zA-Z0-9]*", node):  # Имя переменной
            return node
        else:
            return f'"{node}"'  # Обработка строк как литералов


def main():
    parser = argparse.ArgumentParser(description="YAML to Config Language Converter")
    parser.add_argument("input", help="Путь к входному YAML файлу")
    parser.add_argument("output", help="Путь к выходному cfg файлу")
    args = parser.parse_args()

    try:
        with open(args.input, "r") as yaml_file:
            data = yaml.safe_load(yaml_file)

        variables = {key: value for key, value in data.items() if isinstance(value, (int, float, str))}
        converter = ConfigConverter(data, variables=variables)
        output_data = converter.convert()

        with open(args.output, "w") as cfg_file:
            cfg_file.write(output_data)

        print(f"Конфигурация успешно сохранена в {args.output}")
    except Exception as e:
        print(f"Ошибка: {e}")


if __name__ == "__main__":
    main()
