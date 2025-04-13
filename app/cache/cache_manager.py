#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module quản lý cache cho ứng dụng
"""

import os
import pickle
import config

class CacheManager:
    """Lớp quản lý cache cho ứng dụng"""
    
    def __init__(self):
        """Khởi tạo thư mục cache nếu chưa tồn tại"""
        self.cache_dir = config.CACHE_DIR
        self.file_list_cache_path = os.path.join(self.cache_dir, config.FILE_LIST_CACHE_NAME)
        
        # Đảm bảo thư mục cache tồn tại
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
    
    def get_image_cache_path(self, file_id):
        """
        Lấy đường dẫn cache cho một hình ảnh
        
        Args:
            file_id (str): ID của file
            
        Returns:
            str: Đường dẫn đến file cache
        """
        return os.path.join(self.cache_dir, f"img_{file_id}.png")
    
    def get_file_list_from_cache(self):
        """
        Lấy danh sách file từ cache
        
        Returns:
            list: Danh sách các file hoặc None nếu không có cache
        """
        if os.path.exists(self.file_list_cache_path):
            try:
                with open(self.file_list_cache_path, 'rb') as f:
                    return pickle.load(f)
            except Exception as e:
                print(f"Lỗi khi đọc cache: {e}")
        return None
    
    def save_file_list_to_cache(self, file_list):
        """
        Lưu danh sách file vào cache
        
        Args:
            file_list (list): Danh sách file cần lưu
        """
        try:
            with open(self.file_list_cache_path, 'wb') as f:
                pickle.dump(file_list, f)
        except Exception as e:
            print(f"Lỗi khi lưu cache: {e}")
    
    def clear_file_list_cache(self):
        """Xóa cache danh sách file"""
        try:
            if os.path.exists(self.file_list_cache_path):
                os.remove(self.file_list_cache_path)
        except Exception as e:
            print(f"Lỗi khi xóa cache: {e}")
    
    def clear_all_image_cache(self):
        """Xóa tất cả cache hình ảnh"""
        try:
            for filename in os.listdir(self.cache_dir):
                if filename.startswith("img_") and filename.endswith(".png"):
                    os.remove(os.path.join(self.cache_dir, filename))
        except Exception as e:
            print(f"Lỗi khi xóa cache hình ảnh: {e}")