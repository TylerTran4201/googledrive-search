#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module cung cấp frame nhập liệu và xử lý ảnh đầu vào với phương pháp tách nền HSV
"""

import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk, ImageGrab
import os
import io
import cv2
import numpy as np
from app.image.bg_remover import BackgroundRemover
from app.ui.color_picker import ColorPicker
import config

class InputFrame:
    """Lớp cung cấp giao diện và chức năng xử lý đầu vào"""
    
    def __init__(self, parent, search_callback):
        """
        Khởi tạo frame xử lý đầu vào
        
        Args:
            parent: Frame cha chứa component này
            search_callback: Hàm callback khi nhấn nút tìm kiếm
        """
        self.parent = parent
        self.search_callback = search_callback
        
        # Khởi tạo các biến
        self.clipboard_image = None        # Ảnh gốc từ clipboard
        self.processed_image = None        # Ảnh đã xử lý (đã tách nền)
        self.is_bg_removed = False         # Cờ đánh dấu đã tách nền chưa
        self.is_picking_color = False      # Cờ đánh dấu đang chọn màu từ ảnh
        self.color_pick_mode = "one-click" # Chế độ chọn màu: "one-click" hoặc "picker"
        self.display_image = None          # Ảnh hiển thị trên canvas (để tính toán tọa độ)
        self.eyedropper_active = False     # Cờ đánh dấu công cụ eyedropper đang hoạt động
        
        # Khởi tạo đối tượng tách nền
        self.bg_remover = BackgroundRemover()
        
        # Tạo frame chính
        self.frame = ttk.LabelFrame(parent, text="Hình ảnh đầu vào", padding="10")
        
        # Tạo các widget UI
        self.create_widgets()
        
        # Khởi tạo events
        self.initialize_events()
    
    def create_widgets(self):
        """Tạo các widget UI cho frame đầu vào"""
        # Canvas hiển thị hình ảnh
        self.input_canvas = tk.Canvas(
            self.frame, 
            bg="white", 
            width=config.DEFAULT_SETTINGS['input_canvas_size'][0],
            height=config.DEFAULT_SETTINGS['input_canvas_size'][1]
        )
        self.input_canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Nút để dán hình ảnh từ clipboard
        paste_button = ttk.Button(
            self.frame, 
            text="Dán hình ảnh từ Clipboard", 
            command=self.paste_from_clipboard
        )
        paste_button.pack(fill=tk.X, padx=5, pady=5)
        
        # Frame cho chế độ chọn màu
        color_mode_frame = ttk.Frame(self.frame)
        color_mode_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Nút chọn màu nhanh
        self.eyedropper_button = ttk.Button(
            color_mode_frame,
            text="Chọn màu nền bằng cách click vào ảnh",
            command=self.activate_eyedropper
        )
        self.eyedropper_button.pack(fill=tk.X, padx=5, pady=5)
        
        # Thêm ColorPicker (sẽ ẩn đi mặc định)
        self.color_picker = ColorPicker(self.frame)
        self.color_picker.set_callback(self.on_color_changed)
        self.color_picker_frame = self.color_picker.get_frame()
        self.color_picker_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Biến để lưu trạng thái hiển thị ColorPicker
        self.color_picker_visible = tk.BooleanVar(value=False)
        
        # Checkbox hiển thị/ẩn ColorPicker nâng cao
        self.show_advanced_cb = ttk.Checkbutton(
            self.frame,
            text="Hiển thị tùy chọn màu nâng cao",
            variable=self.color_picker_visible,
            command=self.toggle_color_picker
        )
        self.show_advanced_cb.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        # Ẩn ColorPicker ban đầu
        self.color_picker_frame.pack_forget()
        
        # Frame cho tham số tách nền
        param_frame = ttk.LabelFrame(self.frame, text="Tham số tách nền HSV", padding="5")
        param_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Thanh trượt điều chỉnh dung sai màu nền
        ttk.Label(param_frame, text="Dung sai màu nền:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.tolerance_var = tk.IntVar(value=config.IMAGE_ANALYSIS['background_removal']['tolerance'])
        tolerance_slider = ttk.Scale(
            param_frame,
            from_=5,
            to=100,
            orient=tk.HORIZONTAL,
            variable=self.tolerance_var
        )
        tolerance_slider.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=2)
        ttk.Label(param_frame, textvariable=self.tolerance_var).grid(row=0, column=2, padx=5, pady=2)
        
        # Cấu hình grid
        param_frame.columnconfigure(1, weight=1)
        
        # Nút tách nền
        self.remove_bg_button = ttk.Button(
            self.frame, 
            text="Tách nền (HSV)", 
            command=self.remove_background,
            state=tk.DISABLED
        )
        self.remove_bg_button.pack(fill=tk.X, padx=5, pady=5)
        
        # Nút hoàn tác
        self.reset_button = ttk.Button(
            self.frame, 
            text="Khôi phục ảnh gốc", 
            command=self.reset_image,
            state=tk.DISABLED
        )
        self.reset_button.pack(fill=tk.X, padx=5, pady=5)
        
        # Khung trạng thái
        status_frame = ttk.Frame(self.frame)
        status_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.status_label = ttk.Label(status_frame, text="Trạng thái: Sẵn sàng")
        self.status_label.pack(side=tk.LEFT, padx=5)
        
        # Hiển thị màu đã chọn
        self.color_preview = tk.Canvas(status_frame, width=20, height=20, bg="#FFFFFF", highlightthickness=1)
        self.color_preview.pack(side=tk.RIGHT, padx=5)
        
        # Nút tìm kiếm (Đã tách nền)
        self.search_button = ttk.Button(
            self.frame, 
            text="Tìm kiếm (Đã tách nền)", 
            command=self.on_search_with_processed,
            state=tk.DISABLED
        )
        self.search_button.pack(fill=tk.X, padx=5, pady=5)
        
        # Nút tìm kiếm (Không tách nền)
        self.search_original_button = ttk.Button(
            self.frame, 
            text="Tìm kiếm (Ảnh gốc)", 
            command=self.on_search_with_original,
            state=tk.DISABLED
        )
        self.search_original_button.pack(fill=tk.X, padx=5, pady=5)
    
    def initialize_events(self):
        """Khởi tạo các event liên quan đến đầu vào"""
        # Sự kiện click chuột trên canvas khi đang chọn màu
        self.input_canvas.bind("<Button-1>", self.on_canvas_click)
        
        # Sự kiện di chuyển chuột trên canvas (cho eyedropper)
        self.input_canvas.bind("<Motion>", self.on_mouse_move)
        
        # Sự kiện yêu cầu chọn màu từ ảnh
        self.parent.bind("<<PickColorFromImage>>", self.start_color_picking)
    
    def toggle_color_picker(self):
        """Hiển thị hoặc ẩn ColorPicker nâng cao"""
        if self.color_picker_visible.get():
            self.color_picker_frame.pack(fill=tk.X, padx=5, pady=5, after=self.show_advanced_cb)
        else:
            self.color_picker_frame.pack_forget()
    
    def activate_eyedropper(self):
        """Kích hoạt công cụ eyedropper để chọn màu từ ảnh"""
        if not self.clipboard_image:
            messagebox.showinfo("Thông báo", "Vui lòng dán hình ảnh trước khi chọn màu nền")
            return
        
        # Đánh dấu eyedropper đang hoạt động
        self.eyedropper_active = True
        
        # Thay đổi con trỏ chuột
        self.input_canvas.config(cursor="crosshair")
        
        # Cập nhật trạng thái
        self.status_label.config(text="Trạng thái: Di chuột và click vào màu nền cần loại bỏ")
        
        # Thay đổi nút eyedropper
        self.eyedropper_button.config(
            text="Đang chọn màu nền... (click vào ảnh)",
            style="Accent.TButton"
        )
        
        # Tạo style cho nút accent
        style = ttk.Style()
        style.configure("Accent.TButton", background="blue", foreground="white")
    
    def deactivate_eyedropper(self):
        """Hủy kích hoạt công cụ eyedropper"""
        self.eyedropper_active = False
        self.input_canvas.config(cursor="")
        self.eyedropper_button.config(
            text="Chọn màu nền bằng cách click vào ảnh",
            style="TButton"
        )
    
    def on_mouse_move(self, event):
        """
        Xử lý sự kiện di chuyển chuột trên canvas
        
        Args:
            event: Sự kiện di chuột
        """
        if not self.eyedropper_active or not self.clipboard_image:
            return
        
        # Lấy tọa độ chuột hiện tại
        x, y = event.x, event.y
        
        # Chuyển đổi tọa độ canvas thành tọa độ hình ảnh
        img_coords = self.canvas_to_image_coords(x, y)
        if img_coords is None:
            return
        
        img_x, img_y = img_coords
        
        # Lấy màu tại vị trí đó
        try:
            color = self.clipboard_image.getpixel((img_x, img_y))
            
            # Nếu là ảnh RGBA, bỏ qua kênh alpha
            if len(color) == 4:
                color = color[:3]
                
            # Hiển thị màu ở trạng thái
            hex_color = f"#{color[0]:02X}{color[1]:02X}{color[2]:02X}"
            self.color_preview.config(bg=hex_color)
            
            # Cập nhật trạng thái
            self.status_label.config(text=f"Màu: RGB{color} - Hex: {hex_color} (Click để chọn)")
        except:
            pass
    
    def canvas_to_image_coords(self, canvas_x, canvas_y):
        """
        Chuyển đổi tọa độ trên canvas sang tọa độ trên ảnh gốc
        
        Args:
            canvas_x (int): Tọa độ X trên canvas
            canvas_y (int): Tọa độ Y trên canvas
            
        Returns:
            tuple: (img_x, img_y) hoặc None nếu nằm ngoài ảnh
        """
        if not self.clipboard_image or not self.display_image:
            return None
            
        # Lấy kích thước canvas
        canvas_width = self.input_canvas.winfo_width()
        canvas_height = self.input_canvas.winfo_height()
        
        # Lấy kích thước ảnh hiển thị
        display_width, display_height = self.display_image.size
        
        # Tính toán vị trí bắt đầu của ảnh trên canvas
        start_x = (canvas_width - display_width) // 2
        start_y = (canvas_height - display_height) // 2
        
        # Kiểm tra xem click có nằm trong phạm vi ảnh không
        if (start_x <= canvas_x < start_x + display_width and 
            start_y <= canvas_y < start_y + display_height):
            
            # Tính toán vị trí tương đối trên ảnh hiển thị
            rel_x = canvas_x - start_x
            rel_y = canvas_y - start_y
            
            # Tính tỷ lệ kích thước
            original_width, original_height = self.clipboard_image.size
            scale_x = original_width / display_width
            scale_y = original_height / display_height
            
            # Tính toán vị trí trên ảnh gốc
            img_x = int(rel_x * scale_x)
            img_y = int(rel_y * scale_y)
            
            # Đảm bảo tọa độ nằm trong phạm vi ảnh
            img_x = max(0, min(img_x, original_width - 1))
            img_y = max(0, min(img_y, original_height - 1))
            
            return (img_x, img_y)
        
        return None
    
    def paste_from_clipboard(self):
        """Lấy hình ảnh từ clipboard và hiển thị trên canvas"""
        # Xóa hình ảnh hiện tại
        self.clear_input_image()
        
        # Lấy hình ảnh từ clipboard
        try:
            # Phương pháp cho Windows
            try:
                img = ImageGrab.grabclipboard()
                if img:
                    self.process_clipboard_image(img)
                else:
                    messagebox.showwarning("Cảnh báo", "Không tìm thấy hình ảnh trong clipboard")
            except ImportError:
                # Phương pháp thay thế cho Linux/Mac
                try:
                    import subprocess
                    
                    # Sử dụng xclip hoặc pbpaste tùy thuộc vào hệ điều hành
                    if os.name == 'posix':  # Linux hoặc Mac
                        if hasattr(os, 'uname') and os.uname().sysname == 'Darwin':  # Mac
                            process = subprocess.Popen(['pbpaste', '-Prefer', 'public.tiff'], 
                                                      stdout=subprocess.PIPE)
                        else:  # Linux
                            process = subprocess.Popen(['xclip', '-selection', 'clipboard', '-t', 'image/png', '-o'], 
                                                      stdout=subprocess.PIPE)
                        
                        img_data = process.stdout.read()
                        if img_data:
                            img = Image.open(io.BytesIO(img_data))
                            self.process_clipboard_image(img)
                        else:
                            messagebox.showwarning("Cảnh báo", "Không tìm thấy hình ảnh trong clipboard")
                except Exception as e:
                    messagebox.showerror("Lỗi", f"Không thể lấy hình ảnh từ clipboard: {str(e)}")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể lấy hình ảnh từ clipboard: {str(e)}")
    
    def process_clipboard_image(self, img):
        """
        Xử lý hình ảnh từ clipboard
        
        Args:
            img (PIL.Image): Hình ảnh từ clipboard
        """
        if img:
            # Lưu ảnh gốc
            self.clipboard_image = img
            self.processed_image = None
            self.is_bg_removed = False
            
            # Cập nhật trạng thái các nút
            self.remove_bg_button.config(state=tk.NORMAL)
            self.reset_button.config(state=tk.DISABLED)
            self.search_button.config(state=tk.DISABLED)
            self.search_original_button.config(state=tk.NORMAL)
            self.eyedropper_button.config(state=tk.NORMAL)
            
            # Hiển thị ảnh trên canvas
            self.display_image_on_canvas(img)
            
            # Cập nhật trạng thái
            self.status_label.config(text="Trạng thái: Đã tải ảnh. Click vào ảnh để chọn màu nền cần tách")
        else:
            messagebox.showwarning("Cảnh báo", "Không tìm thấy hình ảnh trong clipboard")
    
    def display_image_on_canvas(self, img):
        """
        Hiển thị hình ảnh trên canvas
        
        Args:
            img (PIL.Image): Hình ảnh cần hiển thị
        """
        # Lấy kích thước canvas
        canvas_width = self.input_canvas.winfo_width()
        canvas_height = self.input_canvas.winfo_height()
        
        # Nếu canvas chưa được render, sử dụng kích thước mặc định
        if canvas_width <= 10:
            canvas_width = config.DEFAULT_SETTINGS['input_canvas_size'][0]
        if canvas_height <= 10:
            canvas_height = config.DEFAULT_SETTINGS['input_canvas_size'][1]
        
        # Lấy kích thước ảnh
        width, height = img.size
        
        # Tính toán tỷ lệ
        scale = min(canvas_width / width, canvas_height / height)
        new_width = int(width * scale)
        new_height = int(height * scale)
        
        # Chỉnh kích thước ảnh
        resized_img = img.resize((new_width, new_height), Image.LANCZOS)
        
        # Lưu ảnh hiển thị để tính toán tọa độ sau này
        self.display_image = resized_img
        
        # Hiển thị ảnh
        photo = ImageTk.PhotoImage(resized_img)
        self.input_canvas.create_image(
            canvas_width // 2, 
            canvas_height // 2, 
            image=photo, 
            anchor=tk.CENTER,
            tags="input_image"
        )
        self.input_canvas.image = photo  # Giữ tham chiếu
    
    def clear_input_image(self):
        """Xóa hình ảnh hiện tại trên canvas"""
        self.input_canvas.delete("all")
        self.clipboard_image = None
        self.processed_image = None
        self.display_image = None
        self.is_bg_removed = False
        self.deactivate_eyedropper()
        
        # Cập nhật trạng thái các nút
        self.remove_bg_button.config(state=tk.DISABLED)
        self.reset_button.config(state=tk.DISABLED)
        self.search_button.config(state=tk.DISABLED)
        self.search_original_button.config(state=tk.DISABLED)
        self.eyedropper_button.config(state=tk.DISABLED)
        
        # Cập nhật trạng thái
        self.status_label.config(text="Trạng thái: Sẵn sàng")
    
    def on_color_changed(self, color):
        """
        Xử lý sự kiện khi màu được chọn thay đổi
        
        Args:
            color (tuple): Màu được chọn (R, G, B)
        """
        # Cập nhật màu hiển thị
        hex_color = f"#{color[0]:02X}{color[1]:02X}{color[2]:02X}"
        self.color_preview.config(bg=hex_color)
        
        # Chỉ bật nút tách nền nếu có ảnh từ clipboard
        if self.clipboard_image:
            self.remove_bg_button.config(state=tk.NORMAL)
    
    def start_color_picking(self, event=None):
        """Bắt đầu chế độ chọn màu từ ảnh (cho ColorPicker nâng cao)"""
        if not self.clipboard_image:
            messagebox.showinfo("Thông báo", "Vui lòng dán hình ảnh trước khi chọn màu từ ảnh")
            return
            
        # Đánh dấu đang trong chế độ chọn màu
        self.is_picking_color = True
        
        # Thay đổi con trỏ chuột
        self.input_canvas.config(cursor="crosshair")
        
        # Cập nhật trạng thái
        self.status_label.config(text="Trạng thái: Đang chọn màu. Nhấp chuột vào ảnh để chọn màu nền")
        
        # Thông báo hướng dẫn
        messagebox.showinfo("Chọn màu", "Hãy nhấp chuột vào vị trí màu nền cần loại bỏ")
    
    def on_canvas_click(self, event):
        """
        Xử lý sự kiện click chuột trên canvas
        
        Args:
            event: Sự kiện click chuột
        """
        # Nếu đang dùng eyedropper hoặc đang trong chế độ chọn màu
        if (self.eyedropper_active or self.is_picking_color) and self.clipboard_image:
            # Lấy tọa độ chuột hiện tại
            x, y = event.x, event.y
            
            # Chuyển đổi tọa độ canvas thành tọa độ hình ảnh
            img_coords = self.canvas_to_image_coords(x, y)
            if img_coords is None:
                return
                
            img_x, img_y = img_coords
            
            # Lấy màu tại vị trí đó
            try:
                color = self.clipboard_image.getpixel((img_x, img_y))
                
                # Nếu là ảnh RGBA, bỏ qua kênh alpha
                if len(color) == 4:
                    color = color[:3]
                    
                # Cập nhật màu được chọn trong ColorPicker
                self.color_picker.set_color_from_hex(f"#{color[0]:02X}{color[1]:02X}{color[2]:02X}")
                
                # Cập nhật màu hiển thị
                hex_color = f"#{color[0]:02X}{color[1]:02X}{color[2]:02X}"
                self.color_preview.config(bg=hex_color)
                
                # Thông báo
                self.status_label.config(text=f"Trạng thái: Đã chọn màu nền RGB{color}. Nhấn 'Tách nền (HSV)' để tiếp tục")
                
                # Hủy kích hoạt eyedropper
                self.deactivate_eyedropper()
                self.is_picking_color = False
                self.input_canvas.config(cursor="")
                
                # Kích hoạt nút tách nền
                self.remove_bg_button.config(state=tk.NORMAL)
            except Exception as e:
                print(f"Lỗi khi lấy màu: {e}")
    
    def remove_background(self):
        """Xử lý sự kiện tách nền từ hình ảnh sử dụng phương pháp HSV"""
        if not self.clipboard_image:
            messagebox.showwarning("Cảnh báo", "Vui lòng dán hình ảnh trước khi tách nền")
            return
            
        try:
            # Lấy màu nền đã chọn
            bg_color = self.color_picker.get_selected_color()
            
            # Cập nhật dung sai màu nền nếu người dùng đã điều chỉnh
            config.IMAGE_ANALYSIS['background_removal']['tolerance'] = self.tolerance_var.get()
            
            # Tách nền
            self.status_label.config(text="Trạng thái: Đang tách nền bằng phương pháp HSV...")
            
            # Thực hiện tách nền với phương pháp HSV
            result_image = self.bg_remover.remove_background_pil(self.clipboard_image, bg_color, method='hsv_improved')
            
            # Lưu kết quả
            self.processed_image = result_image
            self.is_bg_removed = True
            
            # Hiển thị kết quả
            self.display_image_on_canvas(result_image)
            
            # Cập nhật trạng thái các nút
            self.remove_bg_button.config(state=tk.NORMAL)
            self.reset_button.config(state=tk.NORMAL)
            self.search_button.config(state=tk.NORMAL)
            self.search_original_button.config(state=tk.NORMAL)
            
            # Cập nhật trạng thái
            self.status_label.config(text="Trạng thái: Đã tách nền thành công bằng phương pháp HSV")
            
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi khi tách nền: {str(e)}")
            self.status_label.config(text=f"Trạng thái: Lỗi khi tách nền")
    
    def reset_image(self):
        """Khôi phục hình ảnh gốc"""
        if self.clipboard_image:
            # Hiển thị lại ảnh gốc
            self.display_image_on_canvas(self.clipboard_image)
            
            # Cập nhật trạng thái
            self.processed_image = None
            self.is_bg_removed = False
            
            # Cập nhật trạng thái các nút
            self.remove_bg_button.config(state=tk.NORMAL)
            self.reset_button.config(state=tk.DISABLED)
            self.search_button.config(state=tk.DISABLED)
            self.search_original_button.config(state=tk.NORMAL)
            
            # Cập nhật trạng thái
            self.status_label.config(text="Trạng thái: Đã khôi phục ảnh gốc")
    
    def on_search_with_processed(self):
        """Xử lý sự kiện tìm kiếm với ảnh đã tách nền"""
        if not self.is_bg_removed or not self.processed_image:
            messagebox.showwarning("Cảnh báo", "Vui lòng tách nền trước khi tìm kiếm")
            return
            
        # Gọi callback tìm kiếm với ảnh đã xử lý
        self.search_callback(self.processed_image)
    
    def on_search_with_original(self):
        """Xử lý sự kiện tìm kiếm với ảnh gốc"""
        if not self.clipboard_image:
            messagebox.showwarning("Cảnh báo", "Vui lòng dán hình ảnh trước khi tìm kiếm")
            return
            
        # Gọi callback tìm kiếm với ảnh gốc
        self.search_callback(self.clipboard_image)
    
    def get_frame(self):
        """
        Lấy frame chính của component
        
        Returns:
            tkinter.Frame: Frame chứa toàn bộ component
        """
        return self.frame