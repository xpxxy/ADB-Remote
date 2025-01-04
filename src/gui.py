import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess
import json
import os
import re
import sys
import locale

# Language strings
STRINGS = {
    'zh_CN': {
        'title': 'ADB连接工具',
        'settings': '设置',
        'set_adb_path': '设置ADB路径',
        'start_debug': '开启ADB连接',
        'stop_debug': '关闭ADB连接',
        'status_ready': '就绪',
        'error': '错误',
        'success': '成功',
        'invalid_adb': '选择的文件不是有效的ADB程序！',
        'adb_path_saved': 'ADB路径已保存！',
        'set_adb_first': '请先设置ADB路径',
        'enter_ip_port': '请输入IP地址和端口',
        'invalid_ip_port': 'IP地址或端口格式无效',
        'connected_to': '已连接到 {}',
        'connect_failed': '无法连接到设备 {}，请检查设备是否开启调试模式并确保网络连接正常',
        'disconnected': '已断开连接',
        'disconnect_failed': '断开连接失败',
        'language': '语言',
        'chinese': '中文',
        'english': '英文'
    },
    'en': {
        'title': 'ADB Connection Tool',
        'settings': 'Settings',
        'set_adb_path': 'Set ADB Path',
        'start_debug': 'Connect ADB',
        'stop_debug': 'Disconnect ADB',
        'status_ready': 'Ready',
        'error': 'Error',
        'success': 'Success',
        'invalid_adb': 'Selected file is not a valid ADB executable!',
        'adb_path_saved': 'ADB path saved!',
        'set_adb_first': 'Please set ADB path first',
        'enter_ip_port': 'Please enter IP address and port',
        'invalid_ip_port': 'Invalid IP address or port format',
        'connected_to': 'Connected to {}',
        'connect_failed': 'Failed to connect to device {}. Please check if debug mode is enabled and network connection is stable',
        'disconnected': 'Disconnected',
        'disconnect_failed': 'Failed to disconnect',
        'language': 'Language',
        'chinese': 'Chinese',
        'english': 'English'
    }
}

class ADBDebugGUI:
    def __init__(self):
        # Get the application path first
        if getattr(sys, 'frozen', False):
            # If running as exe (PyInstaller)
            self.app_path = os.path.dirname(sys.executable)
        else:
            # If running as script
            self.app_path = os.path.dirname(os.path.abspath(__file__))
            
        # Then load settings and determine language
        self.settings = self.load_settings()
        self.lang = self.settings.get('language', locale.getdefaultlocale()[0])
        if self.lang not in STRINGS:
            self.lang = 'en'
            
        self.root = tk.Tk()
        self.root.title(STRINGS[self.lang]['title'])
        self.root.geometry("400x300")
        
        # Create menu bar
        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)
        
        # Settings menu
        self.settings_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label=STRINGS[self.lang]['settings'], menu=self.settings_menu)
        self.settings_menu.add_command(label=STRINGS[self.lang]['set_adb_path'], command=self.set_adb_path)
        
        # Language submenu
        self.language_menu = tk.Menu(self.settings_menu, tearoff=0)
        self.settings_menu.add_cascade(label=STRINGS[self.lang]['language'], menu=self.language_menu)
        
        # Add language options with radio buttons
        self.lang_var = tk.StringVar(value=self.lang)
        self.language_menu.add_radiobutton(label=STRINGS[self.lang]['chinese'], 
                                         command=lambda: self.change_language('zh_CN'),
                                         variable=self.lang_var,
                                         value='zh_CN')
        self.language_menu.add_radiobutton(label=STRINGS[self.lang]['english'],
                                         command=lambda: self.change_language('en'),
                                         variable=self.lang_var,
                                         value='en')
        
        # Main frame
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # IP and Port entry
        ttk.Label(self.main_frame, text="IP:").grid(row=0, column=0, sticky=tk.W)
        last_ip_port = self.settings.get('last_ip_port', '')
        last_ip = last_ip_port.split(':')[0] if ':' in last_ip_port else ''
        last_port = last_ip_port.split(':')[1] if ':' in last_ip_port else ''
        
        self.ip_var = tk.StringVar(value=last_ip)
        self.port_var = tk.StringVar(value=last_port)
        
        self.ip_entry = ttk.Entry(self.main_frame, textvariable=self.ip_var, width=20)
        self.ip_entry.grid(row=0, column=1, pady=5, padx=(0,5))
        self.ip_entry.bind('<KeyRelease>', self.validate_input)
        
        ttk.Label(self.main_frame, text="Port:").grid(row=0, column=2, sticky=tk.W)
        self.port_entry = ttk.Entry(self.main_frame, textvariable=self.port_var, width=8)
        self.port_entry.grid(row=0, column=3, pady=5)
        self.port_entry.bind('<KeyRelease>', self.validate_input)
        
        # Style for invalid input
        self.style = ttk.Style()
        self.style.configure("Invalid.TEntry", fieldbackground="pink")
        self.style.configure("Valid.TEntry", fieldbackground="white")
        
        # Validation status icons
        self.valid_icon = ttk.Label(self.main_frame, text="✓", foreground="green")
        self.valid_icon.grid(row=0, column=4, padx=5)
        self.valid_icon.grid_remove()  # Hide initially
        
        self.invalid_icon = ttk.Label(self.main_frame, text="✗", foreground="red")
        self.invalid_icon.grid(row=0, column=4, padx=5)
        self.invalid_icon.grid_remove()  # Hide initially
        
        # Buttons
        self.start_button = ttk.Button(self.main_frame, text=STRINGS[self.lang]['start_debug'], command=self.start_debug)
        self.start_button.grid(row=1, column=0, columnspan=2, pady=10)
        
        self.stop_button = ttk.Button(self.main_frame, text=STRINGS[self.lang]['stop_debug'], command=self.stop_debug)
        self.stop_button.grid(row=1, column=2, columnspan=2, pady=10)
        
        # Status label
        self.status_var = tk.StringVar(value=STRINGS[self.lang]['status_ready'])
        self.status_label = ttk.Label(self.main_frame, textvariable=self.status_var)
        self.status_label.grid(row=2, column=0, columnspan=4, pady=5)

    def change_language(self, lang):
        self.lang = lang
        self.settings['language'] = lang
        self.save_settings()
        self.root.title(STRINGS[self.lang]['title'])
        # Update all text elements
        self.menu_bar.entryconfig(1, label=STRINGS[self.lang]['settings'])
        self.settings_menu.entryconfig(0, label=STRINGS[self.lang]['set_adb_path'])
        self.settings_menu.entryconfig(1, label=STRINGS[self.lang]['language'])
        self.start_button.configure(text=STRINGS[self.lang]['start_debug'])
        self.stop_button.configure(text=STRINGS[self.lang]['stop_debug'])
        self.status_var.set(STRINGS[self.lang]['status_ready'])
        # Update language menu labels
        self.language_menu.entryconfig(0, label=STRINGS[self.lang]['chinese'])
        self.language_menu.entryconfig(1, label=STRINGS[self.lang]['english'])

    def load_settings(self):
        settings_path = os.path.join(self.app_path, 'settings.json')
        try:
            if os.path.exists(settings_path):
                with open(settings_path, 'r') as f:
                    return json.load(f)
        except Exception:
            pass
        return {}

    def save_settings(self):
        settings_path = os.path.join(self.app_path, 'settings.json')
        with open(settings_path, 'w') as f:
            json.dump(self.settings, f)

    def validate_adb(self, adb_path):
        try:
            if os.name == 'nt':
                creationflags = subprocess.CREATE_NO_WINDOW
            else:
                creationflags = 0
            result = subprocess.run([adb_path, 'version'], 
                                  check=True, 
                                  capture_output=True, 
                                  text=True,
                                  creationflags=creationflags,
                                  timeout=2.5)
            return 'Android Debug Bridge' in result.stdout
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def set_adb_path(self):
        adb_path = filedialog.askopenfilename(
            title="Select adb.exe",
            filetypes=[("EXE files", "*.exe"), ("All files", "*.*")]
        )
        if adb_path:
            if not self.validate_adb(adb_path):
                messagebox.showerror(STRINGS[self.lang]['error'], STRINGS[self.lang]['invalid_adb'])
                return
            self.settings['adb_path'] = adb_path
            self.save_settings()
            messagebox.showinfo(STRINGS[self.lang]['success'], STRINGS[self.lang]['adb_path_saved'])

    def validate_input(self, event=None):
        # Validate IP
        ip = self.ip_var.get().strip()
        ip_valid = self.validate_ip(ip)
        self.ip_entry.configure(style="Valid.TEntry" if ip_valid else "Invalid.TEntry")
        
        # Validate Port
        port = self.port_var.get().strip()
        port_valid = self.validate_port(port)
        self.port_entry.configure(style="Valid.TEntry" if port_valid else "Invalid.TEntry")
        
        # Show/hide validation icons
        if ip_valid and port_valid:
            self.valid_icon.grid()
            self.invalid_icon.grid_remove()
        else:
            self.valid_icon.grid_remove()
            self.invalid_icon.grid()
        
        return ip_valid and port_valid

    def validate_ip(self, ip):
        if not ip:
            return False
        parts = ip.split('.')
        if len(parts) != 4:
            return False
        try:
            return all(0 <= int(part) <= 255 for part in parts)
        except ValueError:
            return False

    def validate_port(self, port):
        if not port:
            return False
        try:
            port_num = int(port)
            return 0 <= port_num <= 65535
        except ValueError:
            return False

    def start_debug(self):
        ip = self.ip_var.get().strip()
        port = self.port_var.get().strip()
        ip_port = f"{ip}:{port}"
        adb_path = self.settings.get('adb_path')

        # 检查ADB路径是否设置
        if not adb_path:
            messagebox.showerror(STRINGS[self.lang]['error'], STRINGS[self.lang]['set_adb_first'])
            return
        
        if not ip or not port:
            messagebox.showerror(STRINGS[self.lang]['error'], STRINGS[self.lang]['enter_ip_port'])
            return
            
        if not self.validate_input():
            messagebox.showerror(STRINGS[self.lang]['error'], STRINGS[self.lang]['invalid_ip_port'])
            return
            
        ip_port = f"{ip}:{port}"
        adb_path = self.settings.get('adb_path')

        try:
            if os.name == 'nt':
                creationflags = subprocess.CREATE_NO_WINDOW
            else:
                creationflags = 0
            result = subprocess.run([adb_path, 'connect', ip_port], 
                                  check=True, 
                                  capture_output=True, 
                                  text=True,
                                  creationflags=creationflags)
            if "connected" not in result.stdout.lower():
                raise subprocess.CalledProcessError(1, "adb connect")
                
            self.status_var.set(STRINGS[self.lang]['connected_to'].format(ip_port))
            self.settings['last_ip_port'] = ip_port
            self.save_settings()
        except subprocess.CalledProcessError:
            messagebox.showerror(STRINGS[self.lang]['error'], STRINGS[self.lang]['connect_failed'].format(ip_port))

    def stop_debug(self):
        adb_path = self.settings.get('adb_path')
        if not adb_path:
            messagebox.showerror(STRINGS[self.lang]['error'], STRINGS[self.lang]['set_adb_first'])
            return

        try:
            if os.name == 'nt':
                creationflags = subprocess.CREATE_NO_WINDOW
            else:
                creationflags = 0
            subprocess.run([adb_path, 'disconnect'], check=True, creationflags=creationflags)
            self.status_var.set(STRINGS[self.lang]['disconnected'])
        except subprocess.CalledProcessError:
            messagebox.showerror(STRINGS[self.lang]['error'], STRINGS[self.lang]['disconnect_failed'])

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = ADBDebugGUI()
    app.run()
