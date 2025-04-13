#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module quản lý file trên Google Drive (liệt kê, tải xuống)
"""

from googleapiclient.http import MediaIoBaseDownload
from io import BytesIO
import os
import config
from app.cache.cache_manager import CacheManager

class FileManager:
    """Lớp quản lý file trên Google Drive"""
    
    def __init__(self, drive_service):
        """
        Khởi tạo với dịch vụ Drive
        
        Args:
            drive_service: Đối tượng DriveService đã kết nối
        """
        self.drive_service = drive_service
        self.cache_manager = CacheManager()
    
    def list_all_image_files(self, folder_id, status_callback=None, use_cache=True):
        """
        Liệt kê tất cả file PNG trong thư mục và thư mục con
        
        Args:
            folder_id (str): ID của thư mục gốc
            status_callback (function): Hàm callback để cập nhật trạng thái
            use_cache (bool): Có sử dụng cache không
            
        Returns:
            list: Danh sách thông tin các file PNG
        """
        # Kiểm tra cache nếu được yêu cầu
        if use_cache:
            cached_files = self.cache_manager.get_file_list_from_cache()
            if cached_files:
                if status_callback:
                    status_callback(f"Đã tìm thấy {len(cached_files)} file PNG từ cache")
                return cached_files
        
        if not self.drive_service.drive_service:
            return []
            
        files = []
        try:
            self._list_files_recursive(folder_id, files, status_callback)
            
            # Lưu vào cache nếu cần
            if use_cache:
                self.cache_manager.save_file_list_to_cache(files)
                
            return files
        except Exception as e:
            if status_callback:
                status_callback(f"Lỗi khi liệt kê file: {str(e)}")
            return []
    
    def _list_files_recursive(self, folder_id, files=None, status_callback=None, page_token=None):
        """
        Đệ quy liệt kê các file PNG trong thư mục và thư mục con
        
        Args:
            folder_id (str): ID của thư mục
            files (list): Danh sách file đã tìm thấy
            status_callback (function): Hàm callback để cập nhật trạng thái
            page_token (str): Token cho trang tiếp theo
            
        Returns:
            list: Danh sách thông tin các file PNG
        """
        if files is None:
            files = []
            
        # Chuẩn bị query để chỉ tìm file PNG trong thư mục
        query = f"'{folder_id}' in parents and (mimeType = 'image/png')"
        
        # Lấy danh sách file
        response = self.drive_service.drive_service.files().list(
            q=query,
            spaces='drive',
            fields='nextPageToken, files(id, name, mimeType)',
            pageToken=page_token
        ).execute()
        
        # Thêm các file PNG tìm được vào danh sách
        for file in response.get('files', []):
            if file.get('mimeType', '') == 'image/png':
                files.append(file)
        
        # Cập nhật trạng thái
        if status_callback:
            status_callback(f"Đang quét: Đã tìm thấy {len(files)} file PNG")
        
        # Tiếp tục với page token tiếp theo nếu có
        page_token = response.get('nextPageToken', None)
        if page_token:
            self._list_files_recursive(folder_id, files, status_callback, page_token)
        
        # Tìm kiếm trong các thư mục con
        query = f"'{folder_id}' in parents and mimeType='application/vnd.google-apps.folder'"
        sub_folders = self.drive_service.drive_service.files().list(
            q=query,
            spaces='drive',
            fields='files(id, name)'
        ).execute().get('files', [])
        
        for folder in sub_folders:
            self._list_files_recursive(folder['id'], files, status_callback)
            
        return files
    
    def download_file(self, file_id, use_cache=True):
        """
        Tải file từ Google Drive, sử dụng cache nếu có thể
        
        Args:
            file_id (str): ID của file cần tải
            use_cache (bool): Có sử dụng cache không
            
        Returns:
            bytes: Nội dung của file hoặc None nếu có lỗi
        """
        if not self.drive_service.drive_service:
            return None
            
        # Kiểm tra xem file có trong cache không
        cache_path = self.cache_manager.get_image_cache_path(file_id)
        if use_cache and os.path.exists(cache_path):
            try:
                with open(cache_path, 'rb') as f:
                    return f.read()
            except Exception as e:
                print(f"Lỗi khi đọc cache cho file {file_id}: {str(e)}")
        
        # Nếu không có trong cache, tải từ Google Drive
        try:
            request = self.drive_service.drive_service.files().get_media(fileId=file_id)
            file_content = BytesIO()
            downloader = MediaIoBaseDownload(file_content, request)
            
            done = False
            while not done:
                status, done = downloader.next_chunk()
            
            # Lưu vào cache
            file_data = file_content.getvalue()
            if use_cache:
                try:
                    with open(cache_path, 'wb') as f:
                        f.write(file_data)
                except Exception as e:
                    print(f"Lỗi khi lưu cache cho file {file_id}: {str(e)}")
            
            return file_data
        except Exception as e:
            print(f"Lỗi khi tải file {file_id}: {str(e)}")
            return None
            
    def refresh_file_list_cache(self, root_folder_id, status_callback=None):
        """
        Làm mới cache danh sách file
        
        Args:
            root_folder_id (str): ID của thư mục gốc
            status_callback (function): Hàm callback để cập nhật trạng thái
            
        Returns:
            bool: True nếu thành công, False nếu thất bại
        """
        try:
            # Xóa cache hiện tại
            self.cache_manager.clear_file_list_cache()
            
            if status_callback:
                status_callback("Đang làm mới danh sách file...")
            
            # Tải lại danh sách file
            image_files = self.list_all_image_files(root_folder_id, status_callback, use_cache=False)
            
            if status_callback:
                status_callback(f"Đã tìm thấy {len(image_files)} file PNG")
                
            return True
        except Exception as e:
            if status_callback:
                status_callback(f"Lỗi khi làm mới cache: {str(e)}")
            return False