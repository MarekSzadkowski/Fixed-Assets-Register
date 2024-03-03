# This file contains just two helper functions put here for avoiding
# circular imports :)

from os import _exit
from typing import overload


def exit_with_info(info: str) -> None:
    """
    Prints an error message and exits with code 1
    """
    print(info)
    _exit(1)

@overload
def user_input(entries: list[str], msg: str) -> int | None: ...
@overload
def user_input(entries: str, msg: str | None = None) -> str | None: ...

def user_input(entries: list[str] | str, msg: str) -> int | str | None:
    """
    Returns the user input depending on the input type
    """
    if isinstance(entries, list):
        for index, file in enumerate(entries, 1):
            print(f'[{index}] {file}')
        return int(input(f'{msg}: ')) - 1
    if isinstance(entries, str):
        return input(
            f'{msg}\n{entries}\n'
            + 'Press enter to confirm or choose another filename: '
        )
    return None
