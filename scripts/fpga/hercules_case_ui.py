"""Select a fresh Hercules log or flush logging; never access the board or serial port."""
import argparse
import ctypes as c
from ctypes import wintypes as w
from datetime import datetime
import json
from pathlib import Path
import time
import hercules_controls as h

u = h.u
u.PostMessageW.argtypes = [w.HWND, w.UINT, w.WPARAM, w.LPARAM]
u.GetMenuState.argtypes = [w.HMENU, w.UINT, w.UINT]
u.GetMenuState.restype = w.UINT


class GUIInfo(c.Structure):
    _fields_ = [('size', w.DWORD), ('flags', w.DWORD), ('active', w.HWND),
                ('focus', w.HWND), ('capture', w.HWND), ('owner', w.HWND),
                ('movesize', w.HWND), ('caret', w.HWND), ('rect', w.RECT)]


u.GetGUIThreadInfo.argtypes = [w.DWORD, c.POINTER(GUIInfo)]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--pid', type=int, required=True)
    ap.add_argument('--receive-hwnd', type=int, required=True)
    modes = ap.add_mutually_exclusive_group(required=True)
    modes.add_argument('--log', type=Path)
    modes.add_argument('--stop', action='store_true')
    modes.add_argument('--wait-done', action='store_true', help='Read receive text only; never change logging or the board')
    ap.add_argument('--timeout-seconds', type=int, default=30, choices=range(1, 56))
    args = ap.parse_args()
    main_window = next(x['hwnd'] for x in h.windows(args.pid) if x['cls'] == 'TForm1')
    receive = args.receive_hwnd
    owner_pid = w.DWORD()
    u.GetWindowThreadProcessId(receive, c.byref(owner_pid))
    if owner_pid.value != args.pid or h.row(receive)['cls'] != 'TRichEdit':
        raise RuntimeError('Receive control does not belong to the selected Hercules process')

    if args.wait_done:
        u.SendMessageTimeoutW.argtypes = [w.HWND, w.UINT, w.WPARAM, w.LPARAM, w.UINT, w.UINT, c.POINTER(c.c_size_t)]
        u.SendMessageTimeoutW.restype = w.LPARAM
        started = time.monotonic()
        buffer, copied = c.create_unicode_buffer(65536), c.c_size_t()
        count, status = 0, 'WAIT_TIMEOUT'
        while time.monotonic()-started < args.timeout_seconds:
            remaining = args.timeout_seconds-(time.monotonic()-started)
            if not u.SendMessageTimeoutW(receive, 0xD, len(buffer), c.addressof(buffer), 2,
                                        max(1, min(500, int(remaining*1000))), c.byref(copied)):
                status = 'RECEIVE_TEXT_UNAVAILABLE'
                break
            if copied.value >= len(buffer)-1:
                status = 'RECEIVE_TEXT_TRUNCATED'
                break
            count = sum(line.strip() == 'DONE' for line in buffer.value.splitlines())
            if count:
                status = 'DONE' if count == 1 else 'MULTIPLE_DONE_FRAMES_ERROR'
                break
            time.sleep(max(0, min(.25, args.timeout_seconds-(time.monotonic()-started))))
        print(json.dumps({'status':status, 'done_count':count,
            'elapsed_seconds':round(time.monotonic()-started, 3), 'pid':args.pid,
            'receive_hwnd':receive, 'hardware_action_performed':False,
            'logging_or_UI_commands_performed':False}))
        raise SystemExit(0 if status == 'DONE' else 1)

    def menu():
        u.PostMessageW(receive, 0x7B, receive, -1)
        for _ in range(30):
            time.sleep(.1)
            popup = next((x for x in h.windows(args.pid)
                          if x['cls'] == '#32768' and x['visible']), None)
            if popup:
                break
        else:
            raise RuntimeError('Hercules popup unavailable')
        handle = u.SendMessageW(popup['hwnd'], 0x1E1, 0, 0)
        state = {key: int(u.GetMenuState(handle, key, 0)) for key in (12, 28, 38)}
        info = GUIInfo()
        info.size = c.sizeof(info)
        if (any(v == 0xffffffff for v in state.values()) or
                not u.GetGUIThreadInfo(u.GetWindowThreadProcessId(main_window, None), c.byref(info)) or
                not info.owner):
            raise RuntimeError('Hercules menu state/owner unavailable')
        u.PostMessageW(info.owner, 0x1F, 0, 0)
        return state, info.owner

    def command(command_id):
        _, owner = menu()
        u.PostMessageW(owner, 0x111, command_id, 0)
        time.sleep(.15)

    state, owner = menu()
    if state[28] & 8:
        u.PostMessageW(owner, 0x111, 28, 0)
        time.sleep(.15)
    if args.stop:
        state, _ = menu()
        if state[28] & 8:
            raise RuntimeError('Hercules logging did not stop')
        print(json.dumps({'logging_enabled': False, 'hardware_action_performed': False}))
        return
    path = args.log.resolve()
    if path.exists() or not path.parent.is_dir():
        raise RuntimeError('Require a new filename inside an existing capture directory')
    previous = path.with_suffix('.previous_receive.txt')
    if previous.exists():
        raise RuntimeError('Previous receive export already exists; preserve it')
    buffer = c.create_unicode_buffer(65536)
    u.SendMessageW(receive, 0xD, len(buffer), c.addressof(buffer))
    previous.write_bytes(buffer.value.encode('utf-8'))
    command(43)
    if h.row(receive)['text'].strip():
        raise RuntimeError('Receive pane was not cleared after preservation')
    command(30)
    for _ in range(30):
        dialogs = [x for x in h.windows(args.pid) if x['cls'] == '#32770' and x['visible']]
        if dialogs:
            dialog = dialogs[0]
            edit = next(x for x in dialog['children'] if x['cls'] == 'Edit' and x['control_id'] == 1148)
            button = next(x for x in dialog['children'] if x['cls'] == 'Button' and x['control_id'] == 1)
            text = c.create_unicode_buffer(str(path))
            u.SendMessageW(edit['hwnd'], 0xC, 0, c.addressof(text))
            u.PostMessageW(button['hwnd'], 0xF5, 0, 0)
            time.sleep(.4)
            break
        time.sleep(.1)
    else:
        raise RuntimeError('Hercules file dialog unavailable')
    state, owner = menu()
    if not state[28] & 8:
        u.PostMessageW(owner, 0x111, 28, 0)
        time.sleep(.15)
    state, owner = menu()
    if state[38] & 8:
        u.PostMessageW(owner, 0x111, 38, 0)
        time.sleep(.15)
    state, _ = menu()
    if not state[28] & 8 or state[12] & 8 or state[38] & 8 or not path.exists() or path.stat().st_size:
        raise RuntimeError('Logging/NVT/receive/new-file readiness check failed')
    ready = dict(configured_at=datetime.now().astimezone().isoformat(timespec='seconds'), pid=args.pid,
                 receive_hwnd=receive, log=str(path), logging_enabled=True, nvt=False, hide_received=False,
                 previous_receive=str(previous), hardware_action_performed=False, menu_states_by_command_id=state)
    path.with_suffix('.log.setup.json').write_text(json.dumps(ready, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(ready))


if __name__ == '__main__':
    main()
