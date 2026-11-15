# Python 3.11+ | wininput.py | Windows 10 x64 | foreground checks and SendInput
import ctypes as c
from ctypes import wintypes as w
import os
import time
from pathlib import PureWindowsPath


class WindowsInput:
    def __init__(self):
        if os.name != "nt":
            raise OSError("Automação disponível somente no Windows.")
        self.u = c.WinDLL("user32", use_last_error=True)
        self.k = c.WinDLL("kernel32", use_last_error=True)
        self.u.GetForegroundWindow.restype = w.HWND
        self.u.GetWindowThreadProcessId.argtypes = [w.HWND, c.POINTER(w.DWORD)]
        self.k.OpenProcess.argtypes = [w.DWORD, w.BOOL, w.DWORD]
        self.k.OpenProcess.restype = w.HANDLE
        self.k.QueryFullProcessImageNameW.argtypes = [w.HANDLE, w.DWORD, w.LPWSTR, c.POINTER(w.DWORD)]
        self.k.CloseHandle.argtypes = [w.HANDLE]
        self.u.GetAsyncKeyState.argtypes = [c.c_int]
        self.u.GetAsyncKeyState.restype = c.c_short
        self.u.GetCursorPos.argtypes = [c.POINTER(w.POINT)]
        self.u.SetCursorPos.argtypes = [c.c_int, c.c_int]
        ulong_ptr = w.WPARAM

        class Mouse(c.Structure):
            _fields_ = [("dx", w.LONG), ("dy", w.LONG), ("mouseData", w.DWORD),
                        ("dwFlags", w.DWORD), ("time", w.DWORD), ("dwExtraInfo", ulong_ptr)]
        class Keyboard(c.Structure):
            _fields_ = [("wVk", w.WORD), ("wScan", w.WORD), ("dwFlags", w.DWORD),
                        ("time", w.DWORD), ("dwExtraInfo", ulong_ptr)]
        class Hardware(c.Structure):
            _fields_ = [("uMsg", w.DWORD), ("wParamL", w.WORD), ("wParamH", w.WORD)]
        class Payload(c.Union):
            _fields_ = [("mi", Mouse), ("ki", Keyboard), ("hi", Hardware)]
        class Input(c.Structure):
            _anonymous_ = ("data",)
            _fields_ = [("type", w.DWORD), ("data", Payload)]
        self.Input, self.Mouse, self.Keyboard = Input, Mouse, Keyboard
        self.u.SendInput.argtypes = [w.UINT, c.POINTER(Input), c.c_int]
        self.u.SendInput.restype = w.UINT

    def held(self, vk):
        return bool(self.u.GetAsyncKeyState(vk) & 0x8000)

    def cursor(self):
        point = w.POINT()
        if not self.u.GetCursorPos(c.byref(point)):
            raise c.WinError(c.get_last_error())
        return point.x, point.y

    def game_foreground(self):
        pid = w.DWORD()
        hwnd = self.u.GetForegroundWindow()
        self.u.GetWindowThreadProcessId(hwnd, c.byref(pid))
        handle = self.k.OpenProcess(0x1000, False, pid.value)
        if not handle:
            return False
        try:
            buf, length = c.create_unicode_buffer(32768), w.DWORD(32768)
            ok = self.k.QueryFullProcessImageNameW(handle, 0, buf, c.byref(length))
            return bool(ok and PureWindowsPath(buf.value).name.lower() == "league of legends.exe")
        finally:
            self.k.CloseHandle(handle)

    def perform(self, x, y, permission, key=None):
        # Recheck at the action boundary, including emergency stop and hold key.
        if not permission() or not self.game_foreground() or self.held(0x79):
            return False
        old = self.cursor()
        if not self.u.SetCursorPos(int(x), int(y)):
            raise c.WinError(c.get_last_error())
        inputs = (self.Input * 2)()
        try:
            time.sleep(.015)
            if not permission() or not self.game_foreground() or self.held(0x79):
                return False
            if key is None:
                inputs[0].type, inputs[1].type = 0, 0
                inputs[0].mi = self.Mouse(0, 0, 0, 0x0008, 0, 0)
                inputs[1].mi = self.Mouse(0, 0, 0, 0x0010, 0, 0)
            else:
                inputs[0].type, inputs[1].type = 1, 1
                inputs[0].ki = self.Keyboard(ord(key), 0, 0, 0, 0)
                inputs[1].ki = self.Keyboard(ord(key), 0, 2, 0, 0)
            sent = self.u.SendInput(2, inputs, c.sizeof(self.Input))
            if sent != 2:
                # If the button-down alone succeeded, release it before failing.
                self.u.SendInput(1, c.byref(inputs[1]), c.sizeof(self.Input))
                raise OSError("SendInput bloqueado ou incompleto; automação interrompida.")
            time.sleep(.03)
        finally:
            if self.cursor() == (int(x), int(y)):
                self.u.SetCursorPos(*old)
        return True
