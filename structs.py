from __future__ import annotations

from typing import List
from tarfile import TarFile
from datetime import datetime
from pathlib import Path
import argparse


class Object:
    def __init__(self, parent: Directory | FileSystem | None, name: str, mtime: datetime | None):
        self.parent = parent
        self.name = name
        self.mtime = mtime
        self.size = 0
        self.abspath = self.get_abspath()
        if self.parent is not None:
            self.parent.children.append(self)

    def get_name(self) -> str:
        return self.name

    def get_parent(self) -> Directory | None:
        return self.parent

    def get_abspath(self) -> str:
        path = self.name
        p = self.parent
        while p is not None:
            path = p.name + "/" + path
            p = p.parent
        return path

    def isdir(self):
        return isinstance(self, Directory)

    def isfile(self):
        return isinstance(self, File)


class Directory(Object):
    def __init__(self, parent: Directory | FileSystem | None, name: str, mtime: datetime | None):
        super().__init__(parent, name, mtime)
        self.children: List[Directory | File] = []

    def get_child(self, name: str) -> Directory | None:
        for child in self.children:
            if child.get_name() == name:
                return child
        return None

    def search_by_coord(self, path: str) -> File | Directory | None:
        # /
        if path == "/":
            obj = self
            while obj.parent is not None:
                obj = obj.parent
            return obj
        if path == ".":
            return self
        if path == "..":
            if self.parent is not None:
                return self.parent
            else:
                return self
        # /dir
        if path.startswith("/"):
            obj = self
            while obj.parent is not None:
                obj = obj.parent
            parts = list(filter(lambda x: bool(x), path.split("/")[1:]))
            for part in parts:
                if obj.get_child(part):
                    obj = obj.get_child(part)
                else:
                    return None
            return obj
        # ..dir or ../dir
        if path.startswith(".."):
            obj = self.parent
            parts = list(filter(lambda x: bool(x), path[2:].split("/")))
            for part in parts:
                if obj.get_child(part):
                    obj = obj.get_child(part)
                else:
                    return None
            return obj
        # .dir or ./dir/file.txt
        if path.startswith("."):
            obj = self
            parts = list(filter(lambda x: bool(x), path[1:].split("/")))
            for part in parts:
                if obj.get_child(part):
                    obj = obj.get_child(part)
                else:
                    return None
            return obj
        # dir or dir/file.txt
        parts = list(filter(lambda x: bool(x), path.split("/")))
        obj = self
        for part in parts:
            if obj.get_child(part):
                obj = obj.get_child(part)
            else:
                return None
        return obj


class File(Object):
    def __init__(self, parent: Directory | FileSystem | None, name: str, extension: str, content: bytes, size: int,
                 mtime: datetime | None):
        super().__init__(parent, name, mtime)
        self.extension = extension
        self.content = content
        self.size = size

        p = self.parent
        while p is not None:
            p.size += self.size
            p = p.parent


class FileSystem(Directory):
    def __init__(self):
        super().__init__(None, "", None)
        self.abspath = "/"

    def fill(self, tarfile: TarFile):
        for member in tarfile.getmembers()[1:]:
            current = self
            parts = member.path.split("/")[1:]
            for part in parts:
                if current.get_child(part):
                    current = current.get_child(part)
                else:
                    if member.isfile():
                        File(current, part, Path(part).suffix, tarfile.extractfile(member).read(), member.size,
                             datetime.fromtimestamp(member.mtime))
                    elif member.isdir():
                        Directory(current, part, datetime.fromtimestamp(member.mtime))


# rewritten argparse._HelpAction
class _HelpAction(argparse.Action):
    def __init__(self,
                 option_strings,
                 dest,
                 default=False,
                 help=None):
        super(_HelpAction, self).__init__(
            option_strings=option_strings,
            dest=dest,
            const=True,
            default=default,
            nargs=0,
            help=help)

    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, self.const)
        return parser.format_help()


class ArgumentError(Exception):
    def __init__(self, message):
        super().__init__(message)


class ArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        raise ArgumentError(f"{self.prog}: {message}")
