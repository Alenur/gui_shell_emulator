import cmd
import csv

import yaml
import tarfile
import calendar
from structs import FileSystem
from tabulate import tabulate
from datetime import datetime


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
        self.log_writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), self.username, "pwd", "NoArgs"])
        print(self.current_directory)

    def do_cat(self, args: str):
        """Concatenate FILE(s) to standard output."""
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
        if not args:
            self.log_writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), self.username, "ls", "NoArgs"])
            data = [[child.size, child.mtime.strftime("%b %d %H:%M:%S"), child.name]
                    for child in self.current_directory_object.children]
            print(tabulate(data, tablefmt="plain"))
        else:
            self.log_writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), self.username, "ls", args])
            for path in args.split():
                found = self.current_directory_object.search_by_coord(path)
                if found is None:
                    print(f"ls: cannot access '{path}': No such file or directory.")
                elif found.isfile():
                    print(path)
                else:
                    if len(args.split()) > 1:
                        print(f"{path}:")
                    data = [[child.size, child.mtime.strftime("%b %d %H:%M:%S"), child.name]
                            for child in found.children]
                    print(tabulate(data, tablefmt="plain"))

    def do_cd(self, args: str):
        """Change the shell working directory."""
        self.log_writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), self.username, "cd", args])
        result = self.current_directory_object.search_by_coord(args)
        if result is None:
            print(f"cd: {args}: No such file or directory")
        elif result.isfile():
            print(f"cd: {args}: Not a directory")
        else:
            self.current_directory_object = self.current_directory_object.search_by_coord(args)
            self.current_directory = self.current_directory_object.abspath
        self.update_prompt()

    def do_exit(self, args: str):
        """Exit the shell."""
        self.log_writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), self.username, "exit", "NoArgs"])
        self.log_file.close()
        exit()

    def do_echo(self, args: str):
        """Echo the STRING(s) to standard output."""
        self.log_writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), self.username, "echo", args])
        print(args)

    def do_cal(self, args: str):
        """Displays a calendar."""
        self.log_writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), self.username, "cal", "NoArgs"])
        date = datetime.now()
        calendar.TextCalendar(6).prmonth(date.year, date.month)


if __name__ == "__main__":
    Shell().cmdloop()
