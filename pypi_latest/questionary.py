import logging
import os
import sys
from logging import Logger
from typing import List, Optional, Union

import questionary
from prompt_toolkit.styles import Style  # type: ignore
from rich.console import Console


def force_terminal_in_github_action() -> Console:
    """Check, whether the GITHUB_ACTIONS environment variable is set or not.

    If it is set, the process runs in a workflow file and we need to tell rich, in order to get colored output as well.

    Returns:
        Rich Console object
    """
    if "GITHUB_ACTIONS" in os.environ:
        return Console(file=sys.stderr, force_terminal=True)
    else:
        return Console(file=sys.stderr)


log: Logger = logging.getLogger(__name__)

ehrapy_style = Style(
    [
        ("qmark", "fg:#0000FF bold"),  # token in front of the question
        ("question", "bold"),  # question text
        ("answer", "fg:#008000 bold"),  # submitted answer text behind the question
        ("pointer", "fg:#0000FF bold"),  # pointer used in select and checkbox prompts
        ("highlighted", "fg:#0000FF bold"),  # pointed-at choice in select and checkbox prompts
        ("selected", "fg:#008000"),  # style for a selected item of a checkbox
        ("separator", "fg:#cc5454"),  # separator in lists
        ("instruction", ""),  # user instructions for select, rawselect, checkbox
        ("text", ""),  # plain text
        ("disabled", "fg:#FF0000 italic"),  # disabled choices for select and checkbox prompts
    ]
)

# the console used for printing with rich
console = force_terminal_in_github_action()


def custom_questionary(
    function: str,
    question: str,
    choices: Optional[List[str]] = None,
    default: Optional[str] = None,
) -> Union[str, bool]:
    """Custom selection based on Questionary. Handles keyboard interrupts and default values.

    Args:
        function: The function of questionary to call (e.g. select or text).
                  See https://github.com/tmbo/questionary for all available functions.
        question: List of all possible choices.
        choices: The question to prompt for. Should not include default values or colons.
        default: A set default value, which will be chosen if the user does not enter anything.

    Returns:
        The chosen answer.
    """
    answer: Optional[str] = ""
    try:
        if function == "select":
            if default not in choices:  # type: ignore
                log.debug(f"Default value {default} is not in the set of choices!")
            answer = getattr(questionary, function)(f"{question}: ", choices=choices, style=ehrapy_style).unsafe_ask()
        elif function == "password":
            while not answer or answer == "":
                answer = getattr(questionary, function)(f"{question}: ", style=ehrapy_style).unsafe_ask()
        elif function == "text":
            if not default:
                log.debug(
                    "Tried to utilize default value in questionary prompt, but is None! Please set a default value."
                )
                default = ""
            answer = getattr(questionary, function)(f"{question} [{default}]: ", style=ehrapy_style).unsafe_ask()
        elif function == "confirm":
            default_value_bool = True if default == "Yes" or default == "yes" else False
            answer = getattr(questionary, function)(
                f"{question} [{default}]: ", style=ehrapy_style, default=default_value_bool
            ).unsafe_ask()
        else:
            log.debug(f"Unsupported questionary function {function} used!")

    except KeyboardInterrupt:
        console.print("[bold red] Aborted!")
        sys.exit(1)
    if answer is None or answer == "":
        answer = default

    log.debug(f"User was asked the question: ||{question}|| as: {function}")
    log.debug(f"User selected {answer}")

    return answer  # type: ignore
