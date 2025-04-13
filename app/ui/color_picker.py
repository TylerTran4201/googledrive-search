#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module cung cấp component chọn màu
"""

import tkinter as tk
from tkinter import ttk
import cv2
import numpy as np
from PIL import Image, ImageTk

class ColorPicker:
    """Lớp cung cấp giao diện và chức năng chọn màu"""
    
    def __init__(self, parent):
        """
        Khởi tạo component chọn màu
        
        Args:
            parent: Frame cha chứa component này
        """
        self.parent = parent
        self.selected_color = (255, 255, 255)  # Mặc định là màu trắng (R, G, B)
        self.on_color_change = None  # Callback khi màu thay đổi
        
        # Khởi tạo các component UI
        self.create_widgets()
    
    def create_widgets(self):
        """Tạo các widget UI cho component chọn màu"""
        # Frame chính
        self.frame = ttk.LabelFrame(self.parent, text="Chọn màu nền", padding="5")
        
        # Frame chứa các thanh trượt
        slider_frame = ttk.Frame(self.frame)
        slider_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Biến theo dõi giá trị RGB
        self.red_var = tk.IntVar(value=255)
        self.green_var = tk.IntVar(value=255)
        self.blue_var = tk.IntVar(value=255)
        
        # Tạo thanh trượt cho màu đỏ
        ttk.Label(slider_frame, text="R:").grid(row=0, column=0, padx=5, pady=2)
        red_slider = ttk.Scale(slider_frame, from_=0, to=255, orient=tk.HORIZONTAL,
                              variable=self.red_var, command=self.update_color)
        red_slider.grid(row=0, column=1, padx=5, pady=2, sticky=tk.EW)
        ttk.Label(slider_frame, textvariable=self.red_var, width=3).grid(row=0, column=2, padx=5, pady=2)
        
        # Tạo thanh trượt cho màu xanh lá
        ttk.Label(slider_frame, text="G:").grid(row=1, column=0, padx=5, pady=2)
        green_slider = ttk.Scale(slider_frame, from_=0, to=255, orient=tk.HORIZONTAL,
                               variable=self.green_var, command=self.update_color)
        green_slider.grid(row=1, column=1, padx=5, pady=2, sticky=tk.EW)
        ttk.Label(slider_frame, textvariable=self.green_var, width=3).grid(row=1, column=2, padx=5, pady=2)
        
        # Tạo thanh trượt cho màu xanh dương
        ttk.Label(slider_frame, text="B:").grid(row=2, column=0, padx=5, pady=2)
        blue_slider = ttk.Scale(slider_frame, from_=0, to=255, orient=tk.HORIZONTAL,
                              variable=self.blue_var, command=self.update_color)
        blue_slider.grid(row=2, column=1, padx=5, pady=2, sticky=tk.EW)
        ttk.Label(slider_frame, textvariable=self.blue_var, width=3).grid(row=2, column=2, padx=5, pady=2)
        
        # Cấu hình grid
        slider_frame.columnconfigure(1, weight=1)
        
        # Frame hiển thị màu đã chọn
        color_preview_frame = ttk.Frame(self.frame)
        color_preview_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Canvas hiển thị màu
        self.color_canvas = tk.Canvas(color_preview_frame, width=50, height=30, bg="#FFFFFF", highlightthickness=1, highlightbackground="black")
        self.color_canvas.pack(side=tk.LEFT, padx=5)
        
        # Label hiển thị mã màu
        self.color_label = ttk.Label(color_preview_frame, text="#FFFFFF")
        self.color_label.pack(side=tk.LEFT, padx=5)
        
        # Các nút chọn nhanh màu phổ biến
        preset_frame = ttk.Frame(self.frame)
        preset_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Tạo các nút màu phổ biến
        preset_colors = [
            ("#FFFFFF", "Trắng"), 
            ("#000000", "Đen"),
            ("#FF0000", "Đỏ"), 
            ("#00FF00", "Xanh lá"), 
            ("#0000FF", "Xanh dương"),
            ("#FFFF00", "Vàng"), 
            ("#00FFFF", "Xanh ngọc")
        ]
        
        for i, (hex_color, name) in enumerate(preset_colors):
            btn = ttk.Button(preset_frame, text=name, 
                           command=lambda hex=hex_color: self.set_color_from_hex(hex))
            btn.grid(row=i // 4, column=i % 4, padx=2, pady=2, sticky=tk.EW)
        
        # Cấu hình grid cho preset frame
        for i in range(4):
            preset_frame.columnconfigure(i, weight=1)
        
        # Nút chọn màu từ hình ảnh
        pick_btn = ttk.Button(self.frame, text="Chọn màu từ hình ảnh", command=self.pick_color_from_image)
        pick_btn.pack(fill=tk.X, padx=5, pady=5)
    
    def update_color(self, event=None):
        """
        Cập nhật màu khi giá trị RGB thay đổi
        
        Args:
            event: Sự kiện từ thanh trượt (không sử dụng)
        """
        # Lấy giá trị RGB hiện tại
        r = self.red_var.get()
        g = self.green_var.get()
        b = self.blue_var.get()
        
        # Cập nhật màu đã chọn
        self.selected_color = (r, g, b)
        
        # Cập nhật hiển thị
        hex_color = f"#{r:02X}{g:02X}{b:02X}"
        self.color_canvas.config(bg=hex_color)
        self.color_label.config(text=hex_color)
        
        # Gọi callback nếu có
        if self.on_color_change:
            self.on_color_change(self.selected_color)
    
    def set_color_from_hex(self, hex_color):
        """
        Đặt màu từ giá trị hex
        
        Args:
            hex_color (str): Mã màu dạng hex, ví dụ "#FFFFFF"
        """
        # Chuyển từ hex sang RGB
        hex_color = hex_color.lstrip("#")
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        
        # Cập nhật các biến
        self.red_var.set(r)
        self.green_var.set(g)
        self.blue_var.set(b)
        
        # Cập nhật hiển thị
        self.update_color()
    
    def pick_color_from_image(self):
        """Hiển thị hướng dẫn chọn màu từ hình ảnh"""
        # Chỉ hiển thị thông báo hướng dẫn
        # Việc chọn màu thực sự sẽ được xử lý ở lớp InputFrame
        self.parent.event_generate("<<PickColorFromImage>>")
    
    def get_selected_color(self):
        """
        Lấy màu hiện tại đã chọn
        
        Returns:
            tuple: Màu RGB (R, G, B)
        """
        return self.selected_color
    
    def set_callback(self, callback):
        """
        Đặt callback khi màu thay đổi
        
        Args:
            callback (function): Hàm callback nhận tham số là màu RGB
        """
        self.on_color_change = callback
    
    def get_frame(self):
        """
        Lấy frame chính của component
        
        Returns:
            tkinter.Frame: Frame chứa toàn bộ component
        """
        return self.frame