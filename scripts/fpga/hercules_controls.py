"""Inspect controls belonging only to an explicitly selected Hercules process."""
import argparse
import ctypes as c
from ctypes import wintypes as w
import json

u = c.WinDLL('user32', use_last_error=True)
u.GetWindowTextW.argtypes = [w.HWND, w.LPWSTR, c.c_int]
u.GetClassNameW.argtypes = [w.HWND, w.LPWSTR, c.c_int]
u.GetWindowThreadProcessId.argtypes = [w.HWND, c.POINTER(w.DWORD)]
u.IsWindowVisible.argtypes = [w.HWND]
u.GetDlgCtrlID.argtypes = [w.HWND]
u.SendMessageW.argtypes = [w.HWND, w.UINT, w.WPARAM, w.LPARAM]
u.SendMessageW.restype = w.LPARAM
callback = c.WINFUNCTYPE(w.BOOL, w.HWND, w.LPARAM)
u.EnumWindows.argtypes = [callback, w.LPARAM]
u.EnumChildWindows.argtypes = [w.HWND, callback, w.LPARAM]

def row(hwnd):
    text, cls = c.create_unicode_buffer(2048), c.create_unicode_buffer(256)
    u.SendMessageW(hwnd, 0xD, len(text), c.addressof(text))
    u.GetClassNameW(hwnd, cls, len(cls))
    return dict(hwnd=int(hwnd), text=text.value, cls=cls.value,
                visible=bool(u.IsWindowVisible(hwnd)), control_id=u.GetDlgCtrlID(hwnd))

def windows(pid):
    found = []
    @callback
    def visit(hwnd, _):
        owner = w.DWORD(); u.GetWindowThreadProcessId(hwnd, c.byref(owner))
        if owner.value == pid:
            top = row(hwnd); children = []
            @callback
            def child(h, _):
                children.append(row(h)); return True
            u.EnumChildWindows(hwnd, child, 0)
            top['children'] = children; found.append(top)
        return True
    u.EnumWindows(visit, 0)
    return found

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--pid', type=int, required=True)
    args = ap.parse_args()
    print(json.dumps(windows(args.pid), ensure_ascii=False, indent=2))
