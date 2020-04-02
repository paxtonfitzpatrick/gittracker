# handles command, sub-command, and argument parsing
import sys
from argparse import ArgumentParser
from gittracker import __version__ as pkg_version
from gittracker.gittracker import gittracker
from gittracker.util.util import LOG_DIR


def _show_logdir():
    return LOG_DIR



BASE_OPTIONS = {
    '--version': {
        'py_function': None,
        'aliases': '-V',
        'action': 'version',
        'version': f'GitTracker verserion: {pkg_version}',
        'help': 'show the installed GitTracker version'
    },

    '--log-dir': {
        'py_function': _show_logdir,
        'action': 'store_true',
        'help': 'show directory containing logs of errors and tracked repos'
    }

    # TODO: maybe add option to show python interpreter used?
}

COMMANDS = {
    'status': {
        'py_function': gittracker,
        'aliases': 'track',
        'description': 'show "git-status"-like information for each tracked repository',
        'arguments': {
            '--verbose': {
                'aliases': '-v',
                'action': 'count',
                'default': 0
            },
            ''
        }

    }
}

















class Command:
    def __init__(self, py_function, arg_parser):
        self.py_function = py_function
        self.arg_parser = arg_parser

    @classmethod
    def from_dict(cls, command_dict):
        py_function = command_dict.pop('py_function')
        arguments = command_dict.pop('arguments')
        parser = ArgumentParser(**command_dict)
        if arguments is not None:
            for arg_name, arg_info in arguments.items():




    def __call__(self, raw_args):
        args = self.arg_parser.parse_args(raw_args)
        kwargs = vars(args)
        self.py_function(**args)




class CommandParser(ArgumentParser):
    def __init__(self, default_command, **kwargs):
        self.default_command = default_command
        self.base_options = dict()
        self.commands = dict()
        self.aliases = dict()
        super().__init__(**kwargs)

    def _add_aliases(self, name, parser_kwargs):
        aliases = parser_kwargs.get('aliases')
        if aliases is None:
            return (name, )
        elif isinstance(aliases, str):
            aliases = [aliases]
        for alias in aliases:
            self.aliases[alias] = name
        return (name, *aliases)

    def normalize_args(self, args):
        normalized = []
        for arg in args:
            if arg in


    def add_base_options(self, opts):
        base_parser = self.add_mutually_exclusive_group(required=False)
        for opt_name, parser_kwargs in opts.items():
            # opt_names = self._add_aliases(opt_name, parser_kwargs)
            py_func = parser_kwargs.pop('py_function')
            base_parser.add_argument(opt_name, **parser_kwargs)
            self.base_options[opt_name] = py_func

    def add_commands(self, cmds):
        # create a "commands" section
        commands = self.add_subparsers(title='commands')
        # for each command
        for cmd in cmds:
            command = Command.from_dict(cmd)
            commands.choices[str(command)] = command.arg_parser

    def run(self, raw_args):

        cmd = raw_args[0]
        if cmd in self.commands:
            self.commands[cmd](raw_args[1:])
        else:
            parsed_opts = vars(self.parse_args(raw_args))
            for opt, passed in parsed_opts:
                if passed:
                    self.base_options[opt]()

















DEFAULT_COMMAND = 'status'


def main_old():
    parser = CommandParser(
        description='GitTracker: keep track of all your git repositories with '
                    'a single command',
        epilog="commands are run with `gittracker [cmd] [args].\nFor more "
               "information on a given 'cmd', enter `gittracker [cmd] --help`"
               "\nNOTE: simply running `gittracker [args]` will run "
               f"`gittracker {DEFAULT_COMMAND} [args]` unless 'args' contains "
               "any of the above base options",
        default_command=DEFAULT_COMMAND
    )
    parser.add_base_options(BASE_OPTIONS)
    parser.add_commands(COMMANDS)

    raw_args = sys.argv[1:]
    # call default command with passed args if args aren't for main package
    if len(raw_args) == 0 or raw_args[0] not in parser.base_options:
        raw_args.insert(0, parser.default_command)

    parser.run(raw_args)






def main():
    cli_parser = CommandParser()





if __name__ == '__main__':
    main()
