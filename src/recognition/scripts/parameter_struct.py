

class ScriptParameter(object):
    def __init__(self, name: str, value_type: type, default_value, description: str):
        if not isinstance(name, str):
            raise TypeError("name must be str")
        if not isinstance(description, str):
            raise TypeError("description must be str")
        if value_type not in [int, float, str, bool]:
            raise TypeError("type must be int, float, str or bool")
        if name == "":
            raise ValueError("name cannot be empty")
        self._name = name
        self._value_type = value_type
        self._default_value = default_value
        self._value = default_value
        self._description = description

    def set_value(self, value):
        if not isinstance(value, self._value_type):
            self._value = self._default_value
        self._value = value

    @property
    def name(self):
        return self._name

    @property
    def value_type(self):
        return self._value_type

    @property
    def default_value(self):
        return self._default_value

    @property
    def value(self):
        return self._value

    @property
    def description(self):
        return self._description

    def __eq__(self, o: object) -> bool:
        if isinstance(o, ScriptParameter):
            return self._name == o._name
        return False

    def __hash__(self) -> int:
        return hash(self._name)
