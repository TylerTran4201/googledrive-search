#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Main module - Khởi chạy ứng dụng tìm kiếm hình ảnh Google Drive
"""

import tkinter as tk
from app.ui.app_ui import ImageSearchApp

def main():
    """Hàm chính để khởi chạy ứng dụng"""
    root = tk.Tk()
    app = ImageSearchApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()