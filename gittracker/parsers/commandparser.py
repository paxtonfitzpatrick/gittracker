from argparse import ArgumentParser


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
