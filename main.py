import customtkinter as ctk
from trading_logic import TradingBot
from loading_screen import LoadingScreen
import threading
import time
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import sys
import os

# Настройка футуристической темы
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("🚀 IMX/USDT Trading Bot")
        self.geometry("1200x750")
        self.resizable(False, False)

        # Иконка
        if getattr(sys, 'frozen', False):
            app_path = sys._MEIPASS
        else:
            app_path = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(app_path, "IMX.ico")
        if os.path.exists(icon_path):
            self.iconbitmap(icon_path)

        self.bot = TradingBot(self)

        self.create_widgets()
        self.running = False
        self.pulse = True
        self.animate_status()

    def create_widgets(self):
        # Заголовок
        self.label_title = ctk.CTkLabel(self, text="IMX/USDT Trading Bot", font=("Poppins", 28, "bold"))
        self.label_title.pack(pady=20)

        # Рамка для баланса и статуса
        frame_info = ctk.CTkFrame(self, fg_color="#1a1a1a")
        frame_info.pack(pady=10, padx=10, fill="x")

        self.label_balance = ctk.CTkLabel(frame_info, text="Баланс: 0.00 USDT", font=("Poppins", 18))
        self.label_balance.pack(side="left", padx=20, pady=10)

        self.label_status = ctk.CTkLabel(frame_info, text="Статус: Остановлено", font=("Poppins", 18))
        self.label_status.pack(side="right", padx=20, pady=10)

        # Кнопки управления
        frame_buttons = ctk.CTkFrame(self, fg_color="#1a1a1a")
        frame_buttons.pack(pady=10)

        self.start_btn = ctk.CTkButton(frame_buttons, text="🚀 Старт", command=self.start_trading, width=200, height=50)
        self.start_btn.grid(row=0, column=0, padx=20)

        self.stop_btn = ctk.CTkButton(frame_buttons, text="🛑 Стоп", command=self.stop_trading, width=200, height=50)
        self.stop_btn.grid(row=0, column=1, padx=20)

        # График цен
        self.figure, self.ax = plt.subplots(figsize=(8, 4), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.figure, master=self)
        self.canvas.get_tk_widget().pack(pady=20)

        # Логи действий
        self.log_box = ctk.CTkTextbox(self, width=1100, height=200, font=("Poppins", 14))
        self.log_box.pack(pady=10)

    def start_trading(self):
        if not self.running:
            self.running = True
            self.label_status.configure(text="Статус: Активно 🟢")
            threading.Thread(target=self.bot.run, daemon=True).start()

    def stop_trading(self):
        self.running = False
        self.label_status.configure(text="Статус: Остановлено 🔴")
        self.bot.running = False

    def update_balance(self, balance):
        self.label_balance.configure(text=f"Баланс: {balance:.2f} USDT")

    def log(self, message):
        self.log_box.insert("end", f"{time.strftime('%H:%M:%S')} — {message}\n")
        self.log_box.see("end")

    def update_chart(self, prices):
        self.ax.clear()
        self.ax.plot(prices, marker='o', linewidth=2)
        self.ax.set_title("История цен IMX/USDT", color='white')
        self.ax.set_facecolor("#121212")
        self.figure.patch.set_facecolor('#121212')
        self.ax.tick_params(axis='x', colors='white')
        self.ax.tick_params(axis='y', colors='white')
        self.canvas.draw()

    def animate_status(self):
        if self.running:
            color = "#00FF00" if self.pulse else "#007700"
            self.label_status.configure(text_color=color)
            self.pulse = not self.pulse
        self.after(500, self.animate_status)

if __name__ == "__main__":
    # Запускаем загрузку
    loading = LoadingScreen()
    loading.start()

    # После загрузки запускаем основное окно
    app = App()
    app.mainloop()
