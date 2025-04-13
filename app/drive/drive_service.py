#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module quản lý kết nối và dịch vụ Google Drive
"""

from google.oauth2 import service_account
from googleapiclient.discovery import build
import config

class DriveService:
    """Lớp quản lý kết nối và dịch vụ Google Drive"""
    
    def __init__(self):
        """Khởi tạo kết nối Google Drive"""
        self.drive_service = None
        self.connected = False
        self.error_message = ""
        
    def connect(self):
        """Kết nối với Google Drive sử dụng credentials"""
        try:
            # Tạo credentials
            credentials = service_account.Credentials.from_service_account_file(
                config.CREDENTIALS_FILE, scopes=config.DRIVE_SCOPES)
            
            # Tạo dịch vụ Drive
            self.drive_service = build('drive', 'v3', credentials=credentials)
            self.connected = True
            return True
        except Exception as e:
            self.error_message = str(e)
            self.connected = False
            return False
    
    def get_folder_id_by_name(self, folder_name):
        """
        Tìm kiếm folder theo tên
        
        Args:
            folder_name (str): Tên thư mục cần tìm
            
        Returns:
            str: ID của thư mục hoặc None nếu không tìm thấy
        """
        if not self.connected or not self.drive_service:
            return None
            
        try:
            query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder'"
            results = self.drive_service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name)'
            ).execute()
            
            items = results.get('files', [])
            if items:
                return items[0]['id']
        except Exception as e:
            print(f"Lỗi khi tìm thư mục {folder_name}: {str(e)}")
            
        return None