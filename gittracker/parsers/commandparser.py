from argparse import ArgumentParser


# noinspection PyProtectedMember
class CommandParser(ArgumentParser):
    def __init__(
            self,
            name=None,
            aliases=None,
            py_function=None,
            subcommands=None,
            short_description=None,
            **kwargs
    ):
        self.name = name
        if isinstance(aliases, str):
            aliases = [aliases]
        self.aliases = [] if aliases is None else aliases
        self.py_function = py_function
        if subcommands is None:
            subcommands = []
        elif not hasattr(subcommands, '__iter__'):
                subcommands = [subcommands]
        self.subcommands = subcommands
        # if a short description isn't provided,
        # use the default description (if that was provided)
        if short_description is None:
            short_description = kwargs.get('description')
        self.short_description = short_description
        self.subcommand_parsers = None
        self._default_subcommand = None
        super().__init__(**kwargs)

        # set correct usage info for subcommands
        for cmd in self.subcommands:
            cmd.prog = f"{self.prog} {cmd.name}"

    # TODO: add custom string help formatting class

    @property
    def all_names(self):
        return (self.name, *self.aliases)

    @property
    def default_subcommand(self):
        return self._default_subcommand

    @default_subcommand.setter
    def default_subcommand(self, cmd):
        if cmd not in self.subcommands:
            raise ValueError("default subcommand must be an available subcommand")
        self._default_subcommand = cmd

    @default_subcommand.getter
    def get_default_subcommand(self):
        if self._default_subcommand is not None:
            return self._default_subcommand
        else:
            raise ValueError("default subcommand not set")

    def __eq__(self, other):
        return other in self.all_names

    @staticmethod
    def _format_subcmd_help(cmd, formatter):
        # determine the required width and the entry label
        help_position = min(formatter._action_max_length + 2,
                            formatter._max_help_position)
        help_width = max(formatter._width - help_position, 11)
        cmd_width = help_position - formatter._current_indent - 2
        cmd_header = cmd_str = ', '.join(cmd.all_names)

        tup = formatter._current_indent, '', cmd_width, cmd_header
        cmd_header = '%*s%-*s  ' % tup
        indent_first = 0

        # add lines of help text (from cmd.short_description)
        help_text = cmd.short_description
        help_lines = formatter._split_lines(help_text, help_width)
        parts = [cmd_header]
        parts.append('%*s%s\n' % (indent_first, '', help_lines[0]))
        for line in help_lines[1:]:
            parts.append('%*s%s\n' % (help_position, '', line))

        return formatter._join_parts(parts)

    def format_help(self):
        # overrides argparse.ArgumentParser's `format_help` function to
        # include subcommand info with custom help formatting
        formatter = self._get_formatter()
        # format usage
        formatter.add_usage(
            self.usage,
            self._actions,
            self._mutually_exclusive_groups
        )
        # format description
        formatter.add_text(self.description)
        # add existing groups first (in this case, "optional arguments")
        for action_group in self._action_groups:
            formatter.start_section(action_group.title)
            formatter.add_text(action_group.description)
            formatter.add_arguments(action_group._group_actions)
            formatter.end_section()

        # SUBCOMMAND CUSTOM HELP FORMATTING
        if any(self.subcommands):
            formatter.start_section("commands")
            for cmd in self.subcommands:
                cmd_str = ', '.join(cmd.all_names)
                cmd_len = len(cmd_str) + formatter._current_indent
                formatter._action_max_length = max(formatter._action_max_length,
                                                   cmd_len)
                formatter._add_item(self._format_subcmd_help, (cmd, formatter))

            formatter.end_section()

        # format epilogue section
        formatter.add_text(self.epilog)
        # format full help output
        return formatter.format_help()

    def run(self, raw_args):
        try:
            cmd = raw_args[0]
        except IndexError:
            # no positional or optional args were passed
            try:
                # use the default subcommand
                cmd = self.get_default_subcommand()
            except ValueError:
                # no default subcommand set
                cmd = None

        try:
            # Pass remaining args to the subcommand's CommandParser
            # (prevents argparse from consuming args meant for
            # subcommands like `--help/-h`)
            subcmd = self.subcommands[self.subcommands.index(cmd)]
            subcmd.run(raw_args[1:])
        except ValueError:
            # the args either belong to the present command or invalid
            parsed_args = self.parse_args(raw_args)
            self.py_function(**vars(parsed_args))
