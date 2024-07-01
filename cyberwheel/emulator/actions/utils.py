"""
Utilit funcions for emulator actions.
"""

def stdout_to_list(output: str) -> list[str]:
    """
    Convert standard output from subprocess to list of strings.
    Empty strings are also filtered from list.
    """
    return ' '.join(list(output.split('\n'))).split()
