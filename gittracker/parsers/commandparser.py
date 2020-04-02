from argparse import ArgumentParser


class CommandParser(ArgumentParser):
    def __init__(self, name=None, py_function=None, aliases=None, subcommands=None, **kwargs):
        self.name = name
        if aliases is None:
            self.aliases = []
        else:
            self.aliases = aliases
        self.py_function = py_function
        if subcommands is not None and not hasattr(subcommands, '__iter__'):
                subcommands = [subcommands]
        self.subcommands = subcommands

        self.default_subcommand = None
        self.options = None
        self.subcommand_parsers = None
        super().__init__(**kwargs)

        self.add_subcommand_parsers()

    # TODO: setter for self.default_subcommand attr

    @property
    def all_names(self):
        return (self.name, *self.aliases)

    def __eq__(self, other):
        return other in self.all_names

    def __call__(self, raw_args):
        try:
            cmd = raw_args[0]
        except IndexError:
            cmd = self.default_subcommand

        if cmd in self.subcommands:
            subcmd







    # def add_subcommand_parsers(self):
    #     if self.subcommands is None:
    #         return
    #
    #     subcommands = self.add_subparsers(title='subcommands')
    #     for sc in self.subcommands:
    #         sc.add_as_subparser(subcommands)


    def add_as_subparser(self, superparser_group):





    def add_argument(self, arg, aliases=None, **kwargs):
        if aliases is not






    def parse_args(self, **kwargs):




