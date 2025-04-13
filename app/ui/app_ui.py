#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module cung cấp giao diện chính của ứng dụng
"""

import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image
import threading
import concurrent.futures
from io import BytesIO
import time
import config

from app.drive.drive_service import DriveService
from app.drive.file_manager import FileManager
from app.image.analyzer import ImageAnalyzer
from app.ui.input_frame import InputFrame
from app.ui.results_frame import ResultsFrame

class ScrollableFrame(ttk.Frame):
    """Frame có thể cuộn"""
    
    def __init__(self, container, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        
        # Tạo canvas để chứa nội dung và thanh cuộn
        self.canvas = tk.Canvas(self)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        
        # Frame bên trong canvas để chứa nội dung thực sự
        self.scrollable_frame = ttk.Frame(self.canvas)
        
        # Cấu hình để frame bên trong thay đổi theo kích thước canvas
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )
        
        # Tạo cửa sổ trong canvas chứa frame
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        
        # Cấu hình canvas để thay đổi kích thước frame khi canvas thay đổi kích thước
        self.canvas.bind('<Configure>', self._on_canvas_configure)
        
        # Thiết lập thanh cuộn cho canvas
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack các thành phần
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Cấu hình wheel scroll
        self.bind_mousewheel(self.canvas)
    
    def _on_canvas_configure(self, event):
        """Xử lý khi canvas thay đổi kích thước"""
        # Cập nhật chiều rộng của frame bên trong
        canvas_width = event.width
        self.canvas.itemconfig(self.canvas_window, width=canvas_width)
    
    def bind_mousewheel(self, widget):
        """Cấu hình sự kiện cuộn chuột"""
        # Cấu hình cho Windows và MacOS
        widget.bind("<MouseWheel>", self._on_mousewheel)
        # Cấu hình cho Linux
        widget.bind("<Button-4>", self._on_linux_mousewheel_up)
        widget.bind("<Button-5>", self._on_linux_mousewheel_down)
        
        # Đảm bảo các widget con cũng nhận sự kiện cuộn
        for child in widget.winfo_children():
            self.bind_mousewheel(child)
    
    def _on_mousewheel(self, event):
        """Xử lý sự kiện cuộn chuột trên Windows/MacOS"""
        # Windows: event.delta là bội số của 120
        # MacOS: event.delta có thể là giá trị nhỏ hơn
        delta = event.delta
        
        # Chuẩn hóa delta để có trải nghiệm cuộn nhất quán
        if abs(delta) < 120:  # Có thể là MacOS
            direction = -1 if delta < 0 else 1
            self.canvas.yview_scroll(direction, "units")
        else:  # Windows
            direction = -1 if delta < 0 else 1
            self.canvas.yview_scroll(int(-1 * delta / 120), "units")
    
    def _on_linux_mousewheel_up(self, event):
        """Xử lý sự kiện cuộn chuột lên trên Linux"""
        self.canvas.yview_scroll(-1, "units")
    
    def _on_linux_mousewheel_down(self, event):
        """Xử lý sự kiện cuộn chuột xuống trên Linux"""
        self.canvas.yview_scroll(1, "units")
    
    def get_frame(self):
        """Lấy frame bên trong để thêm các widget"""
        return self.scrollable_frame

class ImageSearchApp:
    """Lớp chính quản lý giao diện và chức năng của ứng dụng"""
    
    def __init__(self, root):
        """
        Khởi tạo ứng dụng với root window
        
        Args:
            root: Root window của ứng dụng
        """
        self.root = root
        self.root.title("Tìm kiếm hình ảnh PNG trong Google Drive")
        self.root.geometry("1000x700")
        
        # Khởi tạo các biến
        self.current_search_thread = None
        self.thread_var = tk.StringVar(value=str(config.DEFAULT_SETTINGS['num_threads']))
        self.cache_var = tk.BooleanVar(value=config.DEFAULT_SETTINGS['use_cache'])
        self.search_results = []
        
        # Khởi tạo các dịch vụ
        self.init_services()
        
        # Tạo giao diện
        self.create_ui()
    
    def init_services(self):
        """Khởi tạo các dịch vụ cần thiết"""
        # Dịch vụ Google Drive
        self.drive_service = DriveService()
        self.drive_connected = self.drive_service.connect()
        
        if not self.drive_connected:
            messagebox.showerror(
                "Lỗi kết nối", 
                f"Không thể kết nối với Google Drive: {self.drive_service.error_message}"
            )
        
        # Quản lý file
        self.file_manager = FileManager(self.drive_service)
        
        # Phân tích hình ảnh
        self.image_analyzer = ImageAnalyzer()
    
    def create_ui(self):
        """Tạo giao diện người dùng chính"""
        # Frame chính
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Tạo frame có thể cuộn cho bên trái
        left_scrollable_frame = ScrollableFrame(main_frame)
        left_scrollable_frame.pack(fill=tk.BOTH, expand=True, side=tk.LEFT, padx=5, pady=5)
        
        # Tạo frame đầu vào bên trái (trong frame có thể cuộn)
        self.input_frame = InputFrame(left_scrollable_frame.get_frame(), self.start_search)
        self.input_frame.get_frame().pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Tạo frame có thể cuộn cho bên phải
        right_scrollable_frame = ScrollableFrame(main_frame)
        right_scrollable_frame.pack(fill=tk.BOTH, expand=True, side=tk.RIGHT, padx=5, pady=5)
        
        # Tạo frame hiển thị kết quả bên phải (trong frame có thể cuộn)
        self.results_frame = ResultsFrame(right_scrollable_frame.get_frame())
        self.results_frame.get_frame().pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Thanh trạng thái
        self.status_bar = ttk.Frame(self.root)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM, padx=5, pady=2)
        
        # Thanh tiến trình
        self.progress = ttk.Progressbar(self.status_bar, orient="horizontal", mode="determinate")
        self.progress.pack(fill=tk.X, side=tk.LEFT, expand=True)
        
        # Label hiển thị trạng thái
        self.status_label = ttk.Label(self.status_bar, text="Sẵn sàng")
        self.status_label.pack(side=tk.RIGHT, padx=5)
        
        # Menu
        self.create_menu()
    
    def create_menu(self):
        """Tạo menu chính của ứng dụng"""
        # Tạo thanh menu
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # Menu File
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Làm mới danh sách file", command=self.refresh_file_list)
        file_menu.add_separator()
        file_menu.add_command(label="Thoát", command=self.root.quit)
        
        # Menu Tùy chọn
        options_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tùy chọn", menu=options_menu)
        options_menu.add_checkbutton(label="Sử dụng cache", variable=self.cache_var)
        
        # Menu con cho số lượng thread
        thread_menu = tk.Menu(options_menu, tearoff=0)
        options_menu.add_cascade(label="Số luồng xử lý", menu=thread_menu)
        
        # Thêm các tùy chọn thread
        for num in [1, 2, 4, 8, 10, 16, 32]:
            thread_menu.add_radiobutton(
                label=str(num), 
                variable=self.thread_var, 
                value=str(num)
            )
        
        # Menu Trợ giúp
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Trợ giúp", menu=help_menu)
        help_menu.add_command(label="Hướng dẫn sử dụng", command=self.show_help)
        help_menu.add_command(label="Giới thiệu", command=self.show_about)
    
    def show_help(self):
        """Hiển thị hướng dẫn sử dụng"""
        help_text = """
        Hướng dẫn sử dụng:
        
        1. Dán hình ảnh từ clipboard
        2. Chọn màu nền cần loại bỏ (có thể chọn bằng cách kéo thanh trượt RGB hoặc click vào ảnh)
        3. Chọn phương pháp tách nền phù hợp
        4. Nhấn "Tách nền" để loại bỏ màu nền
        5. Nhấn "Tìm kiếm (Đã tách nền)" để tìm kiếm với hình ảnh đã tách nền
           hoặc "Tìm kiếm (Ảnh gốc)" để tìm kiếm với hình ảnh gốc
        
        * Có thể cuộn lên/xuống nếu không nhìn thấy toàn bộ các tùy chọn
        * Nhấp vào URL trong kết quả để mở hình ảnh trong trình duyệt
        """
        messagebox.showinfo("Hướng dẫn sử dụng", help_text)
    
    def show_about(self):
        """Hiển thị thông tin về ứng dụng"""
        about_text = """
        Ứng dụng Tìm kiếm hình ảnh PNG trong Google Drive
        
        Phiên bản: 2.1
        
        Tính năng:
        - Tìm kiếm hình ảnh PNG trong Google Drive
        - Tách nền hình ảnh trước khi tìm kiếm với nhiều thuật toán
        - Giao diện có thể cuộn cho màn hình nhỏ
        - So sánh hình ảnh dựa trên histogram và đặc trưng
        - Hỗ trợ cache để tăng tốc tìm kiếm
        """
        messagebox.showinfo("Giới thiệu", about_text)
    
    def refresh_file_list(self):
        """Làm mới danh sách file trong cache"""
        if not self.drive_connected:
            messagebox.showerror("Lỗi", "Chưa kết nối được với Google Drive")
            return
            
        # Tìm ID thư mục gốc
        root_folder_id = self.drive_service.get_folder_id_by_name(config.ROOT_FOLDER_NAME)
        if not root_folder_id:
            messagebox.showerror("Lỗi", f"Không tìm thấy thư mục '{config.ROOT_FOLDER_NAME}'")
            return
            
        # Cập nhật trạng thái
        self.status_label.config(text="Đang làm mới danh sách file...")
        self.progress.start()
        
        # Làm mới danh sách file trong thread riêng
        threading.Thread(
            target=self._refresh_file_list_thread,
            args=(root_folder_id,),
            daemon=True
        ).start()
    
    def _refresh_file_list_thread(self, root_folder_id):
        """
        Thread làm mới danh sách file
        
        Args:
            root_folder_id (str): ID của thư mục gốc
        """
        try:
            success = self.file_manager.refresh_file_list_cache(
                root_folder_id, 
                lambda msg: self.root.after(0, lambda m=msg: self.status_label.config(text=m))
            )
            
            if success:
                self.root.after(0, lambda: messagebox.showinfo(
                    "Thông báo", 
                    "Đã làm mới danh sách file thành công"
                ))
            else:
                self.root.after(0, lambda: messagebox.showerror(
                    "Lỗi", 
                    "Có lỗi xảy ra khi làm mới danh sách file"
                ))
        except Exception as e:
            error_msg = str(e)
            self.root.after(0, lambda m=error_msg: messagebox.showerror(
                "Lỗi", 
                f"Lỗi khi làm mới danh sách file: {m}"
            ))
        finally:
            self.root.after(0, lambda: self.progress.stop())
            self.root.after(0, lambda: self.status_label.config(text="Sẵn sàng"))
    
    def start_search(self, image):
        """
        Bắt đầu tìm kiếm với hình ảnh đã cho
        
        Args:
            image (PIL.Image): Hình ảnh dùng để tìm kiếm
        """
        if not self.drive_connected:
            messagebox.showerror("Lỗi", "Chưa kết nối được với Google Drive")
            return
        
        # Xóa kết quả cũ
        self.results_frame.clear_results()
        
        # Cập nhật trạng thái
        self.status_label.config(text="Đang chuẩn bị tìm kiếm...")
        
        # Hiển thị thanh tiến trình
        self.progress.start()
        
        # Bắt đầu tìm kiếm trong một thread riêng
        if self.current_search_thread and self.current_search_thread.is_alive():
            # Hủy tìm kiếm hiện tại nếu đang chạy
            pass  # Cần thêm logic để hủy thread an toàn
        
        self.current_search_thread = threading.Thread(
            target=self.search_images_thread,
            args=(image,),
            daemon=True
        )
        self.current_search_thread.start()
    
    def search_images_thread(self, image):
        """
        Thread thực hiện tìm kiếm hình ảnh
        
        Args:
            image (PIL.Image): Hình ảnh dùng để tìm kiếm
        """
        try:
            # Tìm ID của thư mục gốc
            root_folder_id = self.drive_service.get_folder_id_by_name(config.ROOT_FOLDER_NAME)
            
            if not root_folder_id:
                self.root.after(0, lambda: messagebox.showerror(
                    "Lỗi", 
                    f"Không tìm thấy thư mục '{config.ROOT_FOLDER_NAME}'"
                ))
                self.root.after(0, lambda: self.progress.stop())
                self.root.after(0, lambda: self.status_label.config(
                    text=f"Lỗi: Không tìm thấy thư mục"
                ))
                return
            
            # Chuẩn bị hình ảnh đầu vào và tính toán đặc trưng
            input_img = self.image_analyzer.pil_to_cv2(image)
            
            # Thông báo đang tìm kiếm
            self.root.after(0, lambda: self.update_progress("Đang tìm kiếm các file PNG..."))
            
            # Lấy danh sách file PNG trong thư mục
            use_cache = self.cache_var.get()
            image_files = self.file_manager.list_all_image_files(
                root_folder_id, 
                lambda msg: self.root.after(0, lambda m=msg: self.update_progress(m)),
                use_cache=use_cache
            )
            
            if not image_files:
                self.root.after(0, lambda: messagebox.showinfo(
                    "Thông báo", 
                    "Không tìm thấy file PNG nào trong thư mục"
                ))
                self.root.after(0, lambda: self.progress.stop())
                self.root.after(0, lambda: self.status_label.config(
                    text="Không tìm thấy file PNG"
                ))
                return
            
            # Thiết lập thanh tiến trình
            self.progress['maximum'] = len(image_files)
            self.progress['value'] = 0
            
            # Xác định số lượng luồng từ giao diện
            try:
                num_threads = int(self.thread_var.get())
                if num_threads < 1:
                    num_threads = config.DEFAULT_SETTINGS['num_threads']
            except:
                num_threads = config.DEFAULT_SETTINGS['num_threads']
            
            # Tính toán và tìm kiếm với threads
            results = []
            
            # Tạo pool thread để tăng tốc quá trình
            with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
                futures = []
                for file_info in image_files:
                    futures.append(
                        executor.submit(
                            self.process_file, 
                            file_info, 
                            input_img
                        )
                    )
                
                # Hiển thị tiến trình
                completed = 0
                for future in concurrent.futures.as_completed(futures):
                    completed += 1
                    progress_msg = f"Đang xử lý {completed}/{len(image_files)}"
                    self.root.after(0, lambda msg=progress_msg: self.update_progress(msg))
                    self.root.after(0, lambda val=completed: self.progress.configure(value=val))
                    
                    # Lấy kết quả
                    result = future.result()
                    if result:
                        results.append(result)
            
            # Sắp xếp kết quả theo độ tương đồng giảm dần
            results.sort(key=lambda x: x['similarity'], reverse=True)
            
            # Lấy tối đa max_results kết quả
            max_results = config.DEFAULT_SETTINGS['max_results']
            top_results = results[:max_results]
            
            # Hiển thị kết quả
            self.root.after(0, lambda: self.display_results(top_results))
            
            # Đặt trạng thái hoàn thành
            self.root.after(0, lambda: self.progress.configure(value=len(image_files)))
            self.root.after(0, lambda: self.status_label.config(
                text=f"Hoàn thành! Tìm thấy {len(top_results)} kết quả"
            ))
        except Exception as e:
            error_msg = str(e)
            self.root.after(0, lambda m=error_msg: messagebox.showerror("Lỗi", f"Lỗi trong quá trình tìm kiếm: {m}"))
            self.root.after(0, lambda m=error_msg: self.status_label.config(text=f"Lỗi: {m}"))
        finally:
            self.root.after(0, lambda: self.progress.stop())
    
    def process_file(self, file_info, input_img):
        """
        Xử lý một file và tính toán độ tương đồng
        
        Args:
            file_info (dict): Thông tin về file
            input_img (numpy.ndarray): Hình ảnh đầu vào dạng OpenCV
            
        Returns:
            dict: Kết quả phân tích hoặc None nếu có lỗi
        """
        try:
            # Tải file về
            file_id = file_info['id']
            file_content = self.file_manager.download_file(
                file_id, 
                use_cache=self.cache_var.get()
            )
            
            if file_content:
                # Tạo URL truy cập Google Drive
                file_url = f"https://drive.google.com/file/d/{file_id}/view"
                
                # Xử lý hình ảnh
                try:
                    # Chuyển đổi dữ liệu nhị phân thành hình ảnh
                    content_stream = BytesIO(file_content)
                    img = Image.open(content_stream)
                    img = img.convert('RGB')
                    img_array = self.image_analyzer.pil_to_cv2(img)
                    
                    # So sánh hai hình ảnh
                    similarity = self.image_analyzer.compare_images(input_img, img_array)
                    
                    # Đặt stream về đầu để sử dụng lại
                    content_stream.seek(0)
                    
                    # Lưu kết quả
                    return {
                        'id': file_id,
                        'name': file_info['name'],
                        'similarity': similarity,
                        'content_stream': content_stream,
                        'url': file_url
                    }
                except Exception as e:
                    print(f"Lỗi khi xử lý file {file_info['name']}: {str(e)}")
        except Exception as e:
            print(f"Lỗi khi xử lý file {file_info['id']}: {str(e)}")
            
        return None
    
    def update_progress(self, message):
        """
        Cập nhật thanh trạng thái với thông điệp
        
        Args:
            message (str): Thông điệp cần hiển thị
        """
        print(message)  # In thông báo ra console
        self.status_label.config(text=message)
    
    def display_results(self, results):
        """
        Hiển thị kết quả tìm kiếm
        
        Args:
            results (list): Danh sách kết quả tìm kiếm
        """
        self.results_frame.display_results(results)