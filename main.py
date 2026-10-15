import tkinter as tk
from app_gui import App

def main():
    """程序入口函数"""
    root = tk.Tk()
    app = App(root)
    root.mainloop()

if __name__ == "__main__":
    main()