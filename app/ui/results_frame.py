#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module cung cấp frame hiển thị kết quả tìm kiếm
"""

import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import webbrowser
import config

class ResultsFrame:
    """Lớp cung cấp giao diện hiển thị kết quả tìm kiếm"""
    
    def __init__(self, parent):
        """
        Khởi tạo frame hiển thị kết quả
        
        Args:
            parent: Frame cha chứa component này
        """
        self.parent = parent
        
        # Khởi tạo biến
        self.result_labels = []  # Danh sách các label hiển thị kết quả
        self.result_images = []  # Danh sách các hình ảnh hiển thị
        
        # Tạo frame chính
        self.frame = ttk.LabelFrame(parent, text="Kết quả tìm kiếm", padding="10")
        
        # Tạo các widget UI
        self.create_widgets()
    
    def create_widgets(self):
        """Tạo các widget UI cho frame kết quả"""
        # Frame để chứa kết quả hình ảnh
        self.results_display = ttk.Frame(self.frame)
        self.results_display.pack(fill=tk.BOTH, expand=True)
        
        # Label hướng dẫn
        help_label = ttk.Label(
            self.results_display, 
            text="* Click vào URL để mở trong trình duyệt", 
            foreground="gray"
        )
        help_label.pack(fill=tk.X, padx=5, pady=5)
        
        # Tạo scroll frame cho kết quả
        scroll_frame = ttk.Frame(self.results_display)
        scroll_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Tạo canvas và thanh cuộn
        self.canvas = tk.Canvas(scroll_frame)
        scrollbar = ttk.Scrollbar(scroll_frame, orient="vertical", command=self.canvas.yview)
        
        # Cấu hình canvas
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack thanh cuộn và canvas
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Tạo frame bên trong canvas để chứa kết quả
        self.results_inner_frame = ttk.Frame(self.canvas)
        
        # Tạo cửa sổ trong canvas
        self.canvas_window = self.canvas.create_window(
            (0, 0), 
            window=self.results_inner_frame, 
            anchor="nw",
            tags="results_window"
        )
        
        # Cấu hình canvas để tự điều chỉnh kích thước
        self.canvas.bind("<Configure>", self.on_canvas_configure)
        self.results_inner_frame.bind("<Configure>", self.on_frame_configure)
        
        # Tạo các label để hiển thị kết quả
        max_results = config.DEFAULT_SETTINGS['max_results']
        
        for i in range(max_results):  # Hiển thị tối đa max_results kết quả
            result_frame = ttk.Frame(self.results_inner_frame)
            result_frame.pack(fill=tk.X, padx=5, pady=5)
            
            # Label hiển thị hình ảnh
            img_label = ttk.Label(result_frame)
            img_label.pack(side=tk.LEFT, padx=5)
            
            # Label hiển thị thông tin
            info_label = ttk.Label(result_frame, text="", wraplength=300, cursor="hand2")
            info_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
            
            self.result_labels.append((img_label, info_label))
            self.result_images.append(None)  # Placeholder cho hình ảnh
    
    def on_canvas_configure(self, event):
        """
        Xử lý sự kiện cấu hình canvas thay đổi
        
        Args:
            event: Sự kiện configure
        """
        # Cập nhật chiều rộng của cửa sổ kết quả
        self.canvas.itemconfig("results_window", width=event.width)
    
    def on_frame_configure(self, event):
        """
        Xử lý sự kiện kích thước frame thay đổi
        
        Args:
            event: Sự kiện configure
        """
        # Cập nhật vùng cuộn của canvas
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def display_results(self, results):
        """
        Hiển thị kết quả tìm kiếm
        
        Args:
            results (list): Danh sách kết quả tìm kiếm
        """
        # Xóa tất cả kết quả hiện tại
        self.clear_results()
        
        # Hiển thị kết quả mới
        for i in range(len(self.result_labels)):
            if i < len(results):
                result = results[i]
                
                # Lấy thông tin file
                file_id = result['id']
                file_name = result['name']
                similarity = result['similarity'] * 100  # Đổi sang phần trăm
                file_url = result['url']
                
                # Hiển thị thông tin
                img_label, info_label = self.result_labels[i]
                info_text = f"Tên: {file_name}\nĐộ tương đồng: {similarity:.2f}%\nURL: {file_url}"
                info_label.config(text=info_text)
                
                # Thiết lập sự kiện click
                info_label.bind("<Button-1>", lambda e, url=file_url: self.open_url(url))
                
                # Hiển thị hình ảnh thu nhỏ
                try:
                    img = Image.open(result['content_stream'])
                    img = img.convert('RGB')
                    
                    # Chỉnh kích thước ảnh
                    thumbnail_size = config.DEFAULT_SETTINGS['thumbnail_size']
                    img.thumbnail(thumbnail_size)
                    
                    # Hiển thị ảnh
                    photo = ImageTk.PhotoImage(img)
                    img_label.config(image=photo)
                    self.result_images[i] = photo  # Giữ tham chiếu
                except Exception as e:
                    print(f"Lỗi khi hiển thị ảnh: {str(e)}")
            else:
                # Xóa thông tin của các slot không sử dụng
                img_label, info_label = self.result_labels[i]
                img_label.config(image='')
                info_label.config(text='')
                info_label.unbind("<Button-1>")  # Xóa sự kiện click
                self.result_images[i] = None
    
    def clear_results(self):
        """Xóa tất cả kết quả hiển thị"""
        for i in range(len(self.result_labels)):
            img_label, info_label = self.result_labels[i]
            img_label.config(image='')
            info_label.config(text='')
            info_label.unbind("<Button-1>")  # Xóa sự kiện click
            self.result_images[i] = None
    
    def open_url(self, url):
        """
        Mở URL trong trình duyệt
        
        Args:
            url (str): URL cần mở
        """
        try:
            webbrowser.open_new(url)
        except Exception as e:
            print(f"Lỗi khi mở URL: {str(e)}")
            messagebox.showerror("Lỗi", f"Không thể mở URL: {str(e)}")
    
    def get_frame(self):
        """
        Lấy frame chính của component
        
        Returns:
            tkinter.Frame: Frame chứa toàn bộ component
        """
        return self.frame