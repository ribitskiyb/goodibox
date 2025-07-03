import hashlib
import json
import logging
import re
import time
import warnings
from collections import OrderedDict
from datetime import date, datetime, timedelta
from functools import wraps
from os import PathLike
from types import FunctionType, MappingProxyType
from typing import (
    Any,
    Callable,
    Hashable,
    Iterable,
    Iterator,
    Mapping,
    Optional,
    Sequence,
    TypeVar,
    Union,
)

_JsonValue = Union[None, int, float, bool, list, dict[str, Any]]
_TCallable = TypeVar("_TCallable", bound=Callable)
_TDecorator = Callable[[_TCallable], _TCallable]
_K = TypeVar("_K", bound=Hashable)
_THashable = TypeVar("_THashable", bound=Hashable)
_V = TypeVar("_V")


EMPTY_DICT: Mapping = MappingProxyType({})
_BLANK_LINE_RE = re.compile(r"^[ \t]*$")


def to_date(iso_string: str) -> date:
    return datetime.strptime(iso_string, "%Y-%m-%d").date()


def date_to_datetime(d: date, hour: int = 0, minute: int = 0, second: int = 0) -> datetime:
    return datetime(d.year, d.month, d.day, hour, minute, second)


def days_ago(n: int) -> date:
    return date.today() - timedelta(days=n)


def daterange(start_date: date, end_date: date, include_end: bool = False) -> Iterator[date]:
    period_len = (end_date - start_date).days + include_end
    for n in range(period_len):
        yield start_date + timedelta(n)


def hex_hash(value: str) -> str:
    return hashlib.md5(value.encode("utf-8")).hexdigest()


def inverse_mapping(mapp: Mapping[_K, _THashable]) -> dict[_THashable, _K]:
    return {v: k for k, v in mapp.items()}


def get_mapping_without_key(mapp: Mapping[_K, _V], key_to_remove: _K) -> dict[_K, _V]:
    return {k: v for k, v in mapp.items() if k != key_to_remove}


def get_any_key_with_this_value(
    mapp: Mapping[_K, _V],
    value: _V,
    default: Optional[_K] = None,
) -> Optional[_K]:
    return next((k for k, v in mapp.items() if v == value), default)


def filter_by_keys(
    mapp: Mapping[_K, _V],
    condition: Callable[[_K], bool],
    negate_condition: bool = False,
) -> Iterator[tuple[_K, _V]]:
    if negate_condition:
        return (kv for kv in mapp.items() if not condition(kv[0]))
    else:
        return (kv for kv in mapp.items() if condition(kv[0]))


def filter_by_values(
    mapp: Mapping[_K, _V],
    condition: Callable[[_V], bool],
    negate_condition: bool = False,
) -> Iterator[tuple[_K, _V]]:
    if negate_condition:
        return (kv for kv in mapp.items() if not condition(kv[1]))
    else:
        return (kv for kv in mapp.items() if condition(kv[1]))


def copy_and_update(mapp: Mapping[str, Any], **kwargs: Any) -> dict[str, Any]:
    new = dict(mapp)
    new.update(kwargs)  # type: ignore[arg-type]
    return new


def ordered_dict(k: _K, v: _V, /, *args) -> OrderedDict[_K, _V]:
    """
    Examples
    --------
    >>> ordered_dict(
    >>>     2, "b",
    >>>     1, "a",
    >>>     3, "c",
    >>> )
    OrderedDict([(2, 'b'), (1, 'a'), (3, 'c')])

    >>> ordered_dict(
    >>>     lambda x: x + y, "closure",  # noqa
    >>>     lambda x: x + 1,
    >>> )
    ValueError: odd number of arguments
    """

    if len(args) % 2 == 1:
        raise ValueError("odd number of arguments")
    odi = OrderedDict()
    odi[k] = v
    next_arg = iter(args).__next__
    try:
        while True:
            k, v = next_arg(), next_arg()
            odi[k] = v
    except StopIteration:
        pass
    return odi


def log_arguments(func: _TCallable) -> _TCallable:
    """Debugging decorator to conveniently log the arguments wrapped function was called with,
    including default values that weren't explicitly provided

    Disabled when the interpreter is run with "optimize" flag. Correctly handles functions with
    default argument values, positional-only and keyword-only arguments.
    """
    if not __debug__:
        return func

    # noinspection PyUnreachableCode
    total_args: int = func.__code__.co_argcount
    argnames: tuple[str, ...] = func.__code__.co_varnames[:total_args]
    positional_default_values: tuple = func.__defaults__ or ()
    kwonly_defaults: dict[str, Any] = func.__kwdefaults__
    names_of_positional_w_defaults: Sequence[str] = (
        argnames[len(positional_default_values) :] if positional_default_values else ()
    )

    # Note: currently if argument w/o default value wasn't provided,
    # the log message will say it was None, which might be misleading
    default_args_state = dict.fromkeys(argnames)
    default_args_state.update(zip(names_of_positional_w_defaults, positional_default_values))
    if kwonly_defaults:
        default_args_state.update(kwonly_defaults)
    default_args_state = MappingProxyType(default_args_state)  # type: ignore[assignment]

    @wraps(func)
    def wrapper(*args, **kwargs):
        arguments = dict(default_args_state)
        for pos, value in enumerate(args):
            arguments[argnames[pos]] = value
        arguments.update(kwargs)
        log_on_behalf_of_func(
            func=func,
            level=logging.DEBUG,
            message="Called with %s",
            message_args=(arguments,),
        )
        return func(*args, **kwargs)

    return wrapper  # type: ignore[return-value]


def log_on_behalf_of_func(
    func: FunctionType,
    level: int,
    message: str,
    message_args: Union[tuple, dict[str, Any]] = (),
    proj_logger: logging.Logger = logging.getLogger(),
) -> None:
    """Logging helper for cases when we want to log in a wrapper (e.g. a decorator), but make it
    look like the function itself is logging

    Helps where `functools.wraps` doesn't help.
    """
    proj_logger.handle(
        # Making the LogRecord manually to be able to control what "funcName" will appear in
        # log message. Otherwise it prints "wrapper" instead of wrapped function name and
        # `functools.wraps` doesn't help.
        logging.LogRecord(
            name=func.__module__,
            level=level,
            pathname=__file__,
            lineno=0,
            msg=message,
            args=message_args,
            exc_info=None,
            func=func.__name__,
        )
    )


class ExecutionTimeLogger:
    """Decorator that logs before and after the function executes + adding the time it took

    TO-DO
    """

    _KEY_SECONDS: str = "secs"
    _KEY_FUNC_NAME: str = "func"

    def __init__(
        self,
        pre_msg: str = "Started",
        post_msg: str = f"Finished, time elapsed: {{{_KEY_SECONDS}}}",
    ):
        old_to_new_placeholders = {
            key: f"%({key})s" for key in (self._KEY_FUNC_NAME, self._KEY_SECONDS)
        }
        self._pre_msg = pre_msg.format(**old_to_new_placeholders)
        self._post_msg = post_msg.format(**old_to_new_placeholders)

    def __call__(self, level: int = logging.DEBUG) -> _TDecorator:
        def decorator(func: _TCallable) -> _TCallable:
            @wraps(func)
            def inner(*args, **kwargs):
                func_name = func.__name__
                log_on_behalf_of_func(
                    func=func,
                    level=level,
                    message=self._pre_msg,
                    message_args={self._KEY_FUNC_NAME: func_name},
                )
                start_time = time.time()
                result = func(*args, **kwargs)
                exec_time = timedelta(seconds=time.time() - start_time)
                log_on_behalf_of_func(
                    func=func,
                    level=level,
                    message=self._post_msg,
                    message_args={
                        self._KEY_FUNC_NAME: func_name,
                        self._KEY_SECONDS: exec_time,
                    },
                )
                return result

            return inner  # type: ignore

        return decorator


def suppress_warnings(func: _TCallable) -> _TCallable:
    @wraps(func)
    def inner(*args, **kwargs):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            return func(*args, **kwargs)

    return inner  # type: ignore


def join_format(joiner: str, template: str, strings: Iterable[str]) -> str:
    return joiner.join(template.format(s) for s in strings)


def quoted_comma_separated(strings: Iterable[str], quote: str = "'") -> str:
    """Renders a comma-separated list

    Examples
    --------
    >>> quoted_comma_separated("abc")
    "'a', 'b', 'c'"
    """
    return ", ".join(f"{quote}{s}{quote}" for s in strings)


def format_if(maybe_str: Optional[str], template: str, alt: str = "") -> str:
    if maybe_str is None:
        return alt
    return template.format(maybe_str)


def remove_blank_lines(multine_string: str, line_sep: str = "\n") -> str:
    return line_sep.join(
        # fmt: off
        line
        for line in multine_string.split(line_sep)
        if line and not _BLANK_LINE_RE.match(line)
        # fmt: on
    )


def read_string_from_file(path: Union[str, PathLike[str]]) -> str:
    with open(path, "r") as f:
        return f.read()


def read_json_from_file(path: Union[str, PathLike[str]]) -> _JsonValue:
    with open(path, "r") as f:
        return json.load(f)


def read_jsonlines_from_file(path: Union[str, PathLike[str]]) -> list[_JsonValue]:
    with open(path, "r") as f:
        return [json.loads(line) for line in f]


def suppress(thunk: Callable[[], _V], *exceptions: Exception) -> Optional[_V]:
    """TO-DO"""
    try:
        return thunk()
    except exceptions or Exception:  # type: ignore[misc]
        return None


def append_if(
    value: _V,
    iterable: Iterable[_V],
    cond: Callable[[_V], bool] = bool,
) -> Iterator[_V]:
    yield from iterable
    if cond(value):
        yield value


def prepend_if(
    value: _V,
    iterable: Iterable[_V],
    cond: Callable[[_V], bool] = bool,
) -> Iterator[_V]:
    if cond(value):
        yield value
    yield from iterable
