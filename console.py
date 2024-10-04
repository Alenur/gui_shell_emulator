import cmd
import csv

import yaml
import tarfile
import calendar
from structs import FileSystem, _HelpAction, ArgumentParser, ArgumentError
from tabulate import tabulate
from datetime import datetime
import shlex
import re


class Shell(cmd.Cmd):
    def __init__(self):
        super().__init__()

        with open("config.yaml") as file:
            config = yaml.safe_load(file)

        self.intro = 'Welcome to GPU Shell Emulator. Type "help" for available commands.'
        self.username = config["username"]
        self.hostname = config["hostname"]

        self.system = FileSystem()
        self.system.fill(tarfile.open(config["system_directory"]))

        self.log_file = open(config["log_file"], "w", newline="")
        self.log_writer = csv.writer(self.log_file, delimiter=";")

        self.current_directory_object = self.system
        self.current_directory = self.current_directory_object.abspath
        self.prompt = self.update_prompt()

        self.parsers = self.generate_parsers()

    def update_prompt(self):
        return f"{self.username}@{self.hostname}:{self.current_directory}$ "

    def generate_parsers(self):
        parsers = dict()

        parsers["pwd"] = ArgumentParser(
            prog="pwd",
            description="Print the name of the current working directory.",
            add_help=False,
            exit_on_error=False
        )
        parsers["pwd"].add_argument("--help", action=_HelpAction, help="show this help message and exit")

        parsers["cat"] = ArgumentParser(
            prog="cat",
            description="Concatenate FILE(s) to standard output.",
            add_help=False
        )
        parsers["cat"].add_argument("-l", action="store_true", help="use a long listing format")
        parsers["cat"].add_argument("--help", action=_HelpAction, help="show this help message and exit")
        parsers["cat"].add_argument("files", type=str, nargs="*", metavar="FILE", default=[self.current_directory])

        parsers["ls"] = ArgumentParser(
            prog="ls",
            description="List information about the FILEs (the current directory by default).",
            add_help=False
        )
        parsers["ls"].add_argument("-l", action="store_true", help="use a long listing format")
        parsers["ls"].add_argument("--help", action=_HelpAction, help="show this help message and exit")
        parsers["ls"].add_argument("files", type=str, nargs="*", metavar="FILE", default=[self.current_directory])

        parsers["cd"] = ArgumentParser(
            prog="cd",
            description="Change the shell working directory.",
            add_help=False
        )
        parsers["cd"].add_argument("--help", action=_HelpAction, help="show this help message and exit")
        parsers["cd"].add_argument("dir", type=str, nargs="*", default=[self.current_directory])

        parsers["exit"] = ArgumentParser(
            prog="exit",
            description="Exit the shell with a status of N.",
            add_help=False
        )
        parsers["exit"].add_argument("--help", action=_HelpAction, help="show this help message and exit")
        parsers["exit"].add_argument("status", type=str, nargs="*", metavar="N", default=0)

        parsers["echo"] = ArgumentParser(
            prog="echo",
            description="Echo the STRING(s) to standard output.",
            add_help=False
        )
        parsers["echo"].add_argument("--help", action=_HelpAction, help="show this help message and exit")
        parsers["echo"].add_argument("strings", type=str, nargs="*", metavar="arg", default=[""])

        parsers["cal"] = ArgumentParser(
            prog="cal",
            description="Displays a calendar.",
            add_help=False
        )
        parsers["cal"].add_argument("--help", action=_HelpAction, help="show this help message and exit")
        parsers["cal"].add_argument("-d", type=str, nargs="?", metavar="yyyy-mm")
        parsers["cal"].add_argument("-y", type=int, nargs="?", metavar="yyyy")

        return parsers

    def default(self, line: str):
        return f"{line}: command not found"

    def do_help(self, arg):
        """
        List available commands with "help" or detailed help with "help cmd".
        """
        if arg:
            # Try to find the method for the given command
            try:
                method = getattr(self, 'do_' + arg)
            except AttributeError:
                try:
                    method = getattr(self, 'help_' + arg)
                except AttributeError:
                    return f'No help on {arg}'

            # If the parser exists, print its usage
            if self.parsers[arg]:
                return self.parsers[arg].format_help()
            else:
                # Otherwise, print the docstring for the method
                return getattr(method, '__doc__', None)
        else:
            # If no command is given, print a list of available commands
            cmds = [cmd[3:] for cmd in self.get_names() if cmd.startswith("do_")]
            return "Available commands:\n" + " ".join(cmds)

    def do_pwd(self, args: str):
        """Print the name of the current working directory."""
        try:
            args = self.parsers["pwd"].parse_args(shlex.split(args))
        except ArgumentError as e:
            return e.args[0]

        if not args.help:
            self.log_writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), self.username, "pwd", "NoArgs"])
            return self.current_directory
        else:
            self.log_writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), self.username, "pwd", "--help"])
            return self.parsers["pwd"].format_help()

    def do_cat(self, args: str):
        """Concatenate FILE(s) to standard output."""
        try:
            args = self.parsers["cat"].parse_args(shlex.split(args))
        except ArgumentError as e:
            return e.args[0]

        if not args.help:
            self.log_writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), self.username, "cat", args])
            for path in args.files:
                found = self.current_directory_object.search_by_coord(path)
                if found is None:
                    return f"cat: {path}: No such file or directory"
                elif found.isfile():
                    if found.extension == ".txt":
                        return found.content.decode()
                    else:
                        return found.content
                else:
                    return f"cat: {path}: Is a directory"
        else:
            self.log_writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), self.username, "cat", "--help"])
            return self.parsers["cat"].format_help()

    def do_ls(self, args: str):
        """List information about the FILEs (the current directory by default)."""
        try:
            args = self.parsers["ls"].parse_args(shlex.split(args))
        except ArgumentError as e:
            return e.args[0]

        if not args.help:
            self.log_writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), self.username, "ls", args])
            for path in args.files:
                found = self.current_directory_object.search_by_coord(path)
                if found is None:
                    return f"ls: cannot access '{path}': No such file or directory."
                elif found.isfile():
                    return path
                else:
                    if len(args.files) > 1:
                        return f"{path}:"
                    if args.l:
                        data = [[child.size, child.mtime.strftime("%b %d %H:%M:%S"), child.name]
                                for child in found.children]
                        return tabulate(data, tablefmt="plain")
                    else:
                        data = [child.name for child in found.children]
                        return " ".join(data)
        else:
            self.log_writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), self.username, "ls", "--help"])
            return self.parsers["ls"].format_help()

    def do_cd(self, args: str):
        """Change the shell working directory."""
        try:
            args = self.parsers["cd"].parse_args(shlex.split(args))
        except ArgumentError as e:
            return e.args[0]

        if not args.help:
            self.log_writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), self.username, "cd", args.dir])
            if len(args.dir) == 1:
                result = self.current_directory_object.search_by_coord(args.dir[0])
                if result is None:
                    return f"cd: {args.dir}: No such file or directory"
                elif result.isfile():
                    return f"cd: {args.dir}: Not a directory"
                else:
                    self.current_directory_object = result
                    self.current_directory = self.current_directory_object.abspath
                self.prompt = self.update_prompt()
            elif len(args.dir) > 1:
                return "cd: too many arguments"
        else:
            self.log_writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), self.username, "cd", "--help"])
            return self.parsers["cd"].format_help()

    def do_exit(self, args: str):
        """Exit the shell."""
        try:
            args = self.parsers["exit"].parse_args(shlex.split(args))
        except ArgumentError as e:
            return e.args[0]

        if not args.help:
            if len(args.status) > 1:
                return "exit: too many arguments"
            else:
                if args.status[0].isdigit():
                    args.status[0] = int(args.status[0])
                self.log_writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), self.username, "exit",
                                          args.status[0]])
                self.log_file.close()
                exit(args.status[0])
        else:
            self.log_writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), self.username, "exit", "--help"])
            return self.parsers["exit"].format_help()

    def do_echo(self, args: str):
        """Write arguments to the standard output."""
        try:
            args = self.parsers["echo"].parse_args(shlex.split(args))
        except ArgumentError as e:
            return e.args[0]

        self.log_writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), self.username, "echo", args.strings])
        return " ".join(args.strings)

    def do_cal(self, args: str):
        """Displays a calendar."""
        try:
            args = self.parsers["cal"].parse_args(shlex.split(args))
        except ArgumentError as e:
            return e.args[0]

        date = datetime.now()

        if not args.help:
            if args.d and re.match(r"\d{4}-{1,2}", args.d):
                self.log_writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), self.username, "cal", args.d])
                year, month = list(map(int, args.d.split("-")))
                return calendar.TextCalendar(6).formatmonth(year, month)
            elif args.y:
                self.log_writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), self.username, "cal",
                                          f"{args.y}"])
                return calendar.TextCalendar(6).formatyear(args.y)
            else:
                self.log_writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), self.username, "cal", "NoArgs"])
                return calendar.TextCalendar(6).formatmonth(date.year, date.month)
        else:
            self.log_writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), self.username, "cal", "--help"])
            return self.parsers["cal"].format_help()


if __name__ == "__main__":
    Shell().cmdloop()
