import copy
import dataclasses
import decimal
import functools
import inspect
import os
import sys
import typing
import warnings

try:
    import orjson as json
except ImportError:
    import json


__version__ = "0.0.5"


_DC = typing.TypeVar("_DC")


_MISSING = object()


def _bool(
    value: typing.Union[str, bool, int],
) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return bool(value)
    return value.lower().strip() in ("1", "t", "y", "true", "yes")


def _int(
    value: typing.Union[str, int],
    min_value: int = _MISSING,
    max_value: int = _MISSING,
    default: int = _MISSING,
) -> int:
    result = value
    if isinstance(result, str):
        try:
            result = int(result.lower().strip())
        except TypeError:
            if default is _MISSING:
                raise
            result = default

    if (min_value is not _MISSING) and (result < min_value):
        result = min_value
    if (max_value is not _MISSING) and (result > max_value):
        result = max_value

    return result


def _float(
    value: typing.Union[str, float],
    min_value: float = _MISSING,
    max_value: float = _MISSING,
    default: float = _MISSING,
) -> float:
    result = value
    if isinstance(result, str):
        try:
            result = result.lower().strip()
            if ("." not in result) and ("," in result):
                result = result.replace(",", ".", 1)
            result = float(result)
        except TypeError:
            if default is _MISSING:
                raise
            result = default

    if (min_value is not _MISSING) and (result < min_value):
        result = min_value
    if (max_value is not _MISSING) and (result > max_value):
        result = max_value

    return result


def _decimal(
    value: typing.Union[str, decimal.Decimal],
    min_value: decimal.Decimal = _MISSING,
    max_value: decimal.Decimal = _MISSING,
    default: decimal.Decimal = _MISSING,
) -> decimal.Decimal:
    result = value
    if isinstance(result, str):
        try:
            result = result.lower().strip()
            if ("." not in result) and ("," in result):
                result = result.replace(",", ".", 1)
            result = decimal.Decimal(result)
        except TypeError:
            if default is _MISSING:
                raise
            result = default

    if (min_value is not _MISSING) and (result < min_value):
        result = min_value
    if (max_value is not _MISSING) and (result > max_value):
        result = max_value

    return result


def _json(
    value: typing.Union[str, bytes],
):
    return json.loads(value)


class Field:
    __slots__ = (
        "_var",
        "_cast",
        "_default",
        "_default_factory",
    )

    def __init__(
        self,
        var: typing.Optional[str] = None,
        cast: typing.Callable[[str], typing.Any] = _MISSING,
        default: typing.Any = _MISSING,
        default_factory: typing.Any = _MISSING,
    ) -> None:
        self._var = var
        self._cast = cast
        self._default = default
        self._default_factory = default_factory

    @property
    def var(self):
        return self._var

    @property
    def cast(self):
        return self._cast

    @property
    def has_default(self):
        return (self._default is not _MISSING) or (self._default_factory is not _MISSING)

    def get_default(self):
        if self._default is not _MISSING:
            return copy.deepcopy(self._default)
        elif self._default_factory is not _MISSING:
            return copy.deepcopy(self._default_factory())
        raise EnvironmentError(f"{self.var} is not set")

    @classmethod
    def str_(
        cls,
        var: str,
        default: str = _MISSING,
    ) -> "Field":
        return cls(
            var=var,
            cast=str,
            default=default,
        )

    @classmethod
    def int_(
        cls,
        var: str,
        min_value: int = _MISSING,
        max_value: int = _MISSING,
        default: int = _MISSING,
    ) -> "Field":
        return cls(
            var=var,
            cast=functools.partial(
                _int,
                min_value=min_value,
                max_value=max_value,
                default=default,
            ),
            default=default,
        )

    @classmethod
    def float_(
        cls,
        var: str,
        min_value: float = _MISSING,
        max_value: float = _MISSING,
        default: float = _MISSING,
    ) -> "Field":
        return cls(
            var=var,
            cast=functools.partial(
                _float,
                min_value=min_value,
                max_value=max_value,
                default=default,
            ),
            default=default,
        )

    number = float_

    @classmethod
    def decimal_(
        cls,
        var: str,
        min_value: decimal.Decimal = _MISSING,
        max_value: decimal.Decimal = _MISSING,
        default: decimal.Decimal = _MISSING,
    ) -> "Field":
        return cls(
            var=var,
            cast=functools.partial(
                _decimal,
                min_value=min_value,
                max_value=max_value,
                default=default,
            ),
            default=default,
        )

    @classmethod
    def json_(
        cls,
        var: str,
        default: typing.Any = _MISSING,
    ) -> "Field":
        return cls(
            var=var,
            cast=_json,
            default=default,
        )

    @classmethod
    def bool_(
        cls,
        var: str,
        default: bool = _MISSING,
    ) -> "Field":
        return cls(
            var=var,
            cast=_bool,
            default=default,
        )

    @classmethod
    def list_(
        cls,
        var: str,
        sub_cast: typing.Callable[[typing.Any], typing.Any] = lambda x: str(x),
        default: typing.Sequence[typing.Any] = _MISSING,
    ) -> "Field":
        return cls(
            var=var,
            cast=lambda val: [sub_cast(x) for x in val.strip().split(",") if x.strip()],
            default=default,
        )

    @classmethod
    def str_list(
        cls,
        var: str,
        default: typing.Sequence[str] = _MISSING,
    ) -> "Field":
        return cls.list_(
            var=var,
            sub_cast=str,
            default=default,
        )

    @classmethod
    def int_list(
        cls,
        var: str,
        min_value: int = _MISSING,
        max_value: int = _MISSING,
        value_default: int = _MISSING,
        default: typing.Sequence[int] = _MISSING,
    ) -> "Field":
        return cls.list_(
            var=var,
            sub_cast=functools.partial(
                _int,
                min_value=min_value,
                max_value=max_value,
                default=value_default,
            ),
            default=default,
        )

    @classmethod
    def float_list(
        cls,
        var: str,
        min_value: float = _MISSING,
        max_value: float = _MISSING,
        value_default: float = _MISSING,
        default: typing.Sequence[float] = _MISSING,
    ) -> "Field":
        return cls.list_(
            var=var,
            sub_cast=functools.partial(
                _float,
                min_value=min_value,
                max_value=max_value,
                default=value_default,
            ),
            default=default,
        )

    number_list = float_list

    @classmethod
    def decimal_list(
        cls,
        var: str,
        min_value: decimal.Decimal = _MISSING,
        max_value: decimal.Decimal = _MISSING,
        value_default: decimal.Decimal = _MISSING,
        default: typing.Sequence[decimal.Decimal] = _MISSING,
    ) -> "Field":
        return cls.list_(
            var=var,
            sub_cast=functools.partial(
                _decimal,
                min_value=min_value,
                max_value=max_value,
                default=value_default,
            ),
            default=default,
        )

    str = str_
    int = int_
    float = float_
    decimal = decimal_
    bool = bool_
    json = json_
    list = list_


field = Field


def populate(
    cls: typing.Type[_DC],
    env: typing.Mapping = os.environ,
) -> _DC:
    """
    Creates an instance of passed settings class.
    :param cls: Settings class
    :param env: Env storage
    :return: Instance of the passed class
    """
    params = {}
    for fld in dataclasses.fields(cls):
        if dataclasses.is_dataclass(fld.type):
            if isinstance(fld.default, Field):
                if fld.default.cast is not _MISSING:
                    warnings.warn(
                        "\"cast\" can not be used on sub-settings. "
                        f"Please check the \"{fld.type.__name__}\" at the \"{cls.__name__}\"."
                    )
                if fld.default.has_default:
                    warnings.warn(
                        "Neither \"default\" nor \"default_factory\" "
                        "can not be used on sub-settings. "
                        f"Please check the \"{fld.type.__name__}\" at the \"{cls.__name__}\"."
                    )

            params[fld.name] = populate(
                cls=fld.type,
                env=env,
            )
            continue

        if not isinstance(fld.default, Field):
            continue

        if fld.default.cast is _MISSING:
            raise EnvironmentError(f"\"{cls.__name__}\" has no cast for \"{fld.name}\".")

        value = env.get(fld.default.var, _MISSING)
        if value is not _MISSING:
            value = fld.default.cast(value)
        else:
            value = fld.default.get_default()

        params[fld.name] = value
    return cls(**params)


def show(
    cls: typing.Type[_DC],
) -> None:
    """
    Shows a list of environment variables used by the passed class.
    :param cls: Settings class
    :return:
    """
    for fld in dataclasses.fields(cls):
        if dataclasses.is_dataclass(fld.type):
            show(fld.type)
            continue

        if not isinstance(fld.default, Field):
            continue

        line_ = f"{fld.default.var}="
        if fld.default.has_default:
            line_ += str(fld.default.get_default())

        print(line_)


def _get_caller_path() -> str:
    caller_code = inspect.currentframe().f_back.f_back.f_code
    caller_file = caller_code.co_filename
    return os.path.abspath(os.path.dirname(caller_file))


def _get_parent_dir_file_path(
    file_path: str,
) -> str:
    file_path, filename = os.path.split(file_path)
    return os.path.join(os.path.abspath(os.path.dirname(file_path)), filename)


def read_envfile(
    file_path: str = None,
    env: typing.MutableMapping = os.environ,
) -> None:
    """
    Populates the variables from the env file to env storage.
    :param file_path: Path to the env file
    :param env: Env storage
    :return:
    """
    if file_path is None:
        file_path = os.path.join(_get_caller_path(), ".env")

    while True:
        try:
            with open(file_path, "r") as f:
                content = f.readlines()
        except Exception:  # noqa
            new_path = _get_parent_dir_file_path(file_path)
            if new_path == file_path:
                return
            file_path = new_path
        else:
            break

    for line_ in content:
        pieces = line_.split("=", 1)
        if len(pieces) < 2:
            continue

        key, value = pieces
        value = value.rstrip("\n")

        env[key.strip().upper()] = value


if sys.version_info[:2] < (3, 10):
    settings = dataclasses.dataclass(
        frozen=True,
    )
else:
    settings = dataclasses.dataclass(
        slots=True,
        frozen=True,
    )
