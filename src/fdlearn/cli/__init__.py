import argparse
import sys
import os
import textwrap
import importlib.metadata


DISTRIBUTION_NAME = 'fandango-learn'

def version():
    """Return the Fandango version number"""
    return importlib.metadata.version(DISTRIBUTION_NAME)



def get_parser(in_command_line=True):
    # Main parser
    if in_command_line:
        prog = "fdlearn"
        epilog = textwrap.dedent("""\
            Use `%(prog)s help` to get a list of commands.
            Use `%(prog)s help COMMAND` to learn more about COMMAND.""")
    else:
        prog = ""
        epilog = textwrap.dedent("""\
            Use `help` to get a list of commands.
            Use `help COMMAND` to learn more about COMMAND.
            Use TAB to complete commands.""")
    epilog += f"\nSee GitHub for more information."

    main_parser = argparse.ArgumentParser(
        prog=prog,
        description="The access point to the fdlearn framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=in_command_line,
        epilog=textwrap.dedent(epilog),
    )

    if in_command_line:
        main_parser.add_argument(
            "--version",
            action="version",
            version=f"fandango-learn {version()}",
            help="show version number",
        )

        verbosity_option = main_parser.add_mutually_exclusive_group()
        verbosity_option.add_argument(
            "--verbose",
            "-v",
            dest="verbose",
            action="count",
            help="increase verbosity. Can be given multiple times (-vv)",
        )
        verbosity_option.add_argument(
            "--quiet",
            "-q",
            dest="quiet",
            action="count",
            help="decrease verbosity. Can be given multiple times (-qq)",
        )

    return main_parser


def main(*argv: str, stdout=sys.stdout, stderr=sys.stderr):
    if "-O" in sys.argv:
        sys.argv.remove("-O")
        os.execl(sys.executable, sys.executable, "-O", *sys.argv)

    if stdout is not None:
        sys.stdout = stdout
    if stderr is not None:
        sys.stderr = stderr

    parser = get_parser(in_command_line=True)

    args = parser.parse_args(argv or sys.argv[1:])



