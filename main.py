import cmd
import csv

import yaml
import tarfile
import calendar
from structs import FileSystem, _HelpAction
from tabulate import tabulate
from datetime import datetime
import argparse
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
        self.update_prompt()

    def update_prompt(self):
        self.prompt = f"{self.username}@{self.hostname}:{self.current_directory}$ "

    def do_pwd(self, args: str):
        """Print the name of the current working directory."""

        parser = argparse.ArgumentParser(
            prog="pwd",
            description="Print the name of the current working directory.",
            add_help=False
        )
        parser.add_argument("--help", action=_HelpAction, help="show this help message and exit")
        args = parser.parse_args(shlex.split(args))

        if not args.help:
            self.log_writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), self.username, "pwd", "NoArgs"])
            print(self.current_directory)
        else:
            self.log_writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), self.username, "pwd", "--help"])

    def do_cat(self, args: str):
        """Concatenate FILE(s) to standard output."""

        parser = argparse.ArgumentParser(
            prog="cat",
            description="Concatenate FILE(s) to standard output.",
            add_help=False
        )
        parser.add_argument("-l", action="store_true", help="use a long listing format")
        parser.add_argument("--help", action=_HelpAction, help="show this help message and exit")
        parser.add_argument("files", type=str, nargs="*", metavar="FILE", default=[self.current_directory])
        args = parser.parse_args(shlex.split(args))

        self.log_writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), self.username, "cat", args])
        for path in args.split():
            found = self.current_directory_object.search_by_coord(path)
            if found is None:
                print(f"cat: {path}: No such file or directory")
            elif found.isfile():
                if found.extension == ".txt":
                    print(found.content.decode())
                else:
                    print(found.content)
            else:
                print(f"cat: {path}: Is a directory")

    def do_ls(self, args: str):
        """List information about the FILEs (the current directory by default)."""

        parser = argparse.ArgumentParser(
            prog="ls",
            description="List information about the FILEs (the current directory by default).",
            add_help=False
        )
        parser.add_argument("-l", action="store_true", help="use a long listing format")
        parser.add_argument("--help", action=_HelpAction, help="show this help message and exit")
        parser.add_argument("files", type=str, nargs="*", metavar="FILE", default=[self.current_directory])
        args = parser.parse_args(shlex.split(args))

        if not args.help:
            self.log_writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), self.username, "ls", args])
            for path in args.files:
                found = self.current_directory_object.search_by_coord(path)
                if found is None:
                    print(f"ls: cannot access '{path}': No such file or directory.")
                elif found.isfile():
                    print(path)
                else:
                    if len(args.files) > 1:
                        print(f"{path}:")
                    if args.l:
                        data = [[child.size, child.mtime.strftime("%b %d %H:%M:%S"), child.name]
                                for child in found.children]
                        print(tabulate(data, tablefmt="plain"))
                    else:
                        data = [child.name for child in found.children]
                        print(*data)
        else:
            self.log_writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), self.username, "ls", "--help"])

    def do_cd(self, args: str):
        """Change the shell working directory."""

        parser = argparse.ArgumentParser(
            prog="cd",
            description="Change the shell working directory.",
            add_help=False
        )
        parser.add_argument("--help", action=_HelpAction, help="show this help message and exit")
        parser.add_argument("dir", type=str, nargs="*", default=[self.current_directory])
        args = parser.parse_args(shlex.split(args))

        if not args.help:
            self.log_writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), self.username, "cd", args.dir])
            if len(args.dir) == 1:
                result = self.current_directory_object.search_by_coord(args.dir[0])
                if result is None:
                    print(f"cd: {args.dir}: No such file or directory")
                elif result.isfile():
                    print(f"cd: {args.dir}: Not a directory")
                else:
                    self.current_directory_object = result
                    self.current_directory = self.current_directory_object.abspath
                self.update_prompt()
            elif len(args.dir) > 1:
                print("cd: too many arguments")
        else:
            self.log_writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), self.username, "cd", "--help"])

    def do_exit(self, args: str):
        """Exit the shell."""

        parser = argparse.ArgumentParser(
            prog="exit",
            description="Exit the shell with a status of N.",
            add_help=False
        )
        parser.add_argument("--help", action=_HelpAction, help="show this help message and exit")
        parser.add_argument("status", type=int, nargs="*", metavar="N", default=0)
        args = parser.parse_args(shlex.split(args))

        if not args.help:
            if len(args.status) > 1:
                print("exit: too many arguments")
            else:
                self.log_writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), self.username, "exit",
                                          args.status])
                self.log_file.close()
                exit(args.status)
        else:
            self.log_writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), self.username, "exit", "--help"])

    def do_echo(self, args: str):
        """Write arguments to the standard output."""

        parser = argparse.ArgumentParser(
            prog="echo",
            description="Echo the STRING(s) to standard output.",
            add_help=False
        )
        parser.add_argument("--help", action=_HelpAction, help="show this help message and exit")
        parser.add_argument("strings", type=str, nargs="*", metavar="arg", default=[""])
        args = parser.parse_args(shlex.split(args))

        self.log_writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), self.username, "echo", args.strings])
        print(" ".join(args.strings))

    def do_cal(self, args: str):
        """Displays a calendar."""
        date = datetime.now()

        parser = argparse.ArgumentParser(
            prog="cal",
            description="Displays a calendar.",
            add_help=False
        )
        parser.add_argument("--help", action=_HelpAction, help="show this help message and exit")
        parser.add_argument("-d", type=str, nargs="?", metavar="yyyy-mm")
        parser.add_argument("-y", type=int, nargs="?", metavar="yyyy")

        args = parser.parse_args(shlex.split(args))

        if not args.help:
            if args.d and re.match(r"\d{4}-{1,2}", args.d):
                self.log_writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), self.username, "cal", args.d])
                year, month = list(map(int, args.d.split("-")))
                calendar.TextCalendar(6).prmonth(year, month)
            elif args.y:
                self.log_writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), self.username, "cal",
                                          f"{args.y}"])
                calendar.TextCalendar(6).pryear(args.y)
            else:
                self.log_writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), self.username, "cal", "NoArgs"])
                calendar.TextCalendar(6).prmonth(date.year, date.month)
        else:
            self.log_writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), self.username, "cal", "--help"])


if __name__ == "__main__":
    Shell().cmdloop()
