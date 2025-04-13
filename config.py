#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module chứa các thiết lập cấu hình cho ứng dụng
"""

import os

# Đường dẫn đến file credentials
CREDENTIALS_FILE = 'service-account-key.json'

# Tên thư mục chính trong Google Drive
ROOT_FOLDER_NAME = 'search_ggdrive'

# Thư mục cache
CACHE_DIR = os.path.join(os.path.expanduser("~"), ".image_search_cache")

# File cache cho danh sách file
FILE_LIST_CACHE_NAME = "file_list_cache.pkl"

# Cài đặt mặc định
DEFAULT_SETTINGS = {
    'use_cache': True,
    'num_threads': 10,
    'max_results': 7,  # Số lượng kết quả tối đa hiển thị
    'thumbnail_size': (100, 100),  # Kích thước ảnh thu nhỏ
    'input_canvas_size': (400, 400),  # Kích thước canvas hiển thị ảnh đầu vào
}

# Phạm vi cho Google Drive API
DRIVE_SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

# Thiết lập cho phân tích hình ảnh
IMAGE_ANALYSIS = {
    'histogram_size': [8, 8, 8],  # Kích thước histogram
    'feature_match_ratio': 0.7,  # Tỷ lệ so sánh đặc trưng
    'resize_max_size': 800,  # Kích thước tối đa cho ảnh khi trích xuất đặc trưng
    'similarity_weights': {
        'histogram': 0.5,  # Trọng số cho độ tương đồng histogram
        'feature': 0.5,  # Trọng số cho độ tương đồng đặc trưng
    },
    'background_removal': {
        'tolerance': 40,      # Dung sai màu khi loại bỏ nền (tăng lên từ 30)
        'erosion_kernel_size': 3,  # Kích thước kernel cho phép xói mòn
        'dilate_kernel_size': 5,   # Kích thước kernel cho phép giãn nở (tăng lên từ 3)
        'iterations': {       # Số lần lặp cho các phép toán hình thái học
            'erode': 1,
            'dilate': 2,
            'close': 3,
            'open': 2
        },
        'post_processing': True,  # Bật/tắt xử lý hậu kỳ
        'fill_holes': True,       # Bật/tắt điền các lỗ trong mask
        'smoothing': True,        # Bật/tắt làm mịn mask
    }
}