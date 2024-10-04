from PySide6.QtWidgets import QApplication, QPlainTextEdit
from PySide6.QtGui import QTextCursor, QPalette, QTextCharFormat, QFont, QKeyEvent, QMouseEvent, QContextMenuEvent
from PySide6.QtCore import Qt
from console import Shell


class Console(QPlainTextEdit):
    def __init__(self, parent=None):
        super(Console, self).__init__(parent)

        self.windowWidth = 0
        self.windowHeight = 0

        self.console = Shell()
        self.prompt = self.console.prompt
        self.insertPrompt()

        self.history = []
        self.historyPos = 0

        self.buffer = QApplication.clipboard()

        self.isLocked = False

        self.initUI()

    def initUI(self):
        DISPLAY_W = QApplication.screens()[0].size().width()
        DISPLAY_H = QApplication.screens()[0].size().height()
        self.windowWidth = DISPLAY_W // 2
        self.windowHeight = DISPLAY_H // 3
        self.setGeometry((DISPLAY_W - self.windowWidth) // 2, (DISPLAY_H - self.windowHeight) // 2, self.windowWidth, self.windowHeight)
        p = self.palette()
        p.setColor(QPalette.ColorRole.Base, Qt.GlobalColor.black)
        p.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
        self.setPalette(p)
        self.setFont(QFont("Consolas", 12))

    def keyPressEvent(self, event: QKeyEvent):
        if self.isLocked:
            return
        if 32 <= event.key() <= 126 and (event.modifiers() == Qt.KeyboardModifier.NoModifier or event.modifiers() == Qt.KeyboardModifier.ShiftModifier):
            super().keyPressEvent(event)
        if event.key() == Qt.Key.Key_Backspace and event.modifiers() == Qt.KeyboardModifier.NoModifier and self.textCursor().positionInBlock() > len(self.prompt):
            super().keyPressEvent(event)
        if event.key() == Qt.Key.Key_Return and event.modifiers() == Qt.KeyboardModifier.NoModifier:
            cmd = self.textCursor().block().text()[len(self.prompt):]
            self.onEnter(cmd)
        if event.key() == Qt.Key.Key_Up and event.modifiers() == Qt.KeyboardModifier.NoModifier:
            self.historyBack()
        if event.key() == Qt.Key.Key_Down and event.modifiers() == Qt.KeyboardModifier.NoModifier:
            self.historyForward()
        if event.key() == Qt.Key.Key_C and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            if self.buffer:
                self.buffer.setText(self.textCursor().block().text()[len(self.prompt):])
        if event.key() == Qt.Key.Key_Left and event.modifiers() == Qt.KeyboardModifier.NoModifier:
            self.textCursor().movePosition(QTextCursor.MoveOperation.StartOfBlock)

    def mousePressEvent(self, event: QMouseEvent):
        super().mousePressEvent(event)
        if event.button() == Qt.MouseButton.RightButton:
            if self.buffer:
                self.textCursor().insertText(self.buffer.text())

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        pass

    def contextMenuEvent(self, event: QContextMenuEvent):
        pass

    def onEnter(self, cmd: str):
        consoleOutput = self.console.onecmd(cmd)
        if consoleOutput:
            self.textCursor().insertBlock()
        self.historyAdd(cmd)
        self.textCursor().insertText(consoleOutput)
        self.insertPrompt(True)

    def insertPrompt(self, insertNewBlock: bool = False):
        self.prompt = self.console.update_prompt()
        if insertNewBlock:
            self.textCursor().insertBlock()
        format = QTextCharFormat()
        format.setForeground(Qt.GlobalColor.green)
        self.textCursor().setCharFormat(format)
        self.textCursor().insertText(self.prompt)
        self.setWindowTitle(f"{self.prompt[:self.prompt.find(self.console.current_directory)]} {self.console.current_directory}")
        self.scrollDown()

    def scrollDown(self):
        vbar = self.verticalScrollBar()
        vbar.setValue(vbar.maximum())

    def historyAdd(self, cmd: str):
        self.history.append(cmd)
        self.historyPos = len(self.history)

    def historyBack(self):
        if not self.historyPos:
            return
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock)
        cursor.movePosition(QTextCursor.MoveOperation.EndOfBlock, QTextCursor.MoveMode.KeepAnchor)
        cursor.removeSelectedText()
        cursor.insertText(self.prompt + self.history[self.historyPos - 1])
        self.setTextCursor(cursor)
        self.historyPos -= 1

    def historyForward(self):
        if self.historyPos == len(self.history):
            return
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock)
        cursor.movePosition(QTextCursor.MoveOperation.EndOfBlock, QTextCursor.MoveMode.KeepAnchor)
        cursor.removeSelectedText()
        if self.historyPos == len(self.history) - 1:
            cursor.insertText(self.prompt)
        else:
            cursor.insertText(self.prompt + self.history[self.historyPos + 1])
        self.setTextCursor(cursor)
        self.historyPos += 1


