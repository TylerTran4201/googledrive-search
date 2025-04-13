#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module phân tích hình ảnh: tính toán histogram, trích xuất và so sánh đặc trưng
"""

import cv2
import numpy as np
import config

class ImageAnalyzer:
    """Lớp phân tích hình ảnh"""
    
    def __init__(self):
        """Khởi tạo các tham số phân tích từ cấu hình"""
        self.histogram_size = config.IMAGE_ANALYSIS['histogram_size']
        self.feature_match_ratio = config.IMAGE_ANALYSIS['feature_match_ratio']
        self.resize_max_size = config.IMAGE_ANALYSIS['resize_max_size']
        self.hist_weight = config.IMAGE_ANALYSIS['similarity_weights']['histogram']
        self.feature_weight = config.IMAGE_ANALYSIS['similarity_weights']['feature']
    
    def pil_to_cv2(self, pil_img):
        """
        Chuyển đổi ảnh PIL sang định dạng OpenCV
        
        Args:
            pil_img (PIL.Image): Hình ảnh PIL
            
        Returns:
            numpy.ndarray: Hình ảnh OpenCV (BGR)
        """
        pil_img = pil_img.convert('RGB')
        img = np.array(pil_img)
        # Chuyển từ RGB sang BGR
        return cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    
    def cv2_to_pil(self, cv_img, with_alpha=False):
        """
        Chuyển đổi ảnh OpenCV sang định dạng PIL
        
        Args:
            cv_img (numpy.ndarray): Hình ảnh OpenCV (BGR hoặc BGRA)
            with_alpha (bool): Có kênh alpha hay không
            
        Returns:
            PIL.Image: Hình ảnh PIL
        """
        from PIL import Image
        
        if with_alpha:
            # Nếu có kênh alpha, chuyển BGRA sang RGBA
            img = cv2.cvtColor(cv_img, cv2.COLOR_BGRA2RGBA)
        else:
            # Nếu không có kênh alpha, chuyển BGR sang RGB
            img = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        
        return Image.fromarray(img)
    
    def calculate_histogram(self, img):
        """
        Tính toán histogram của hình ảnh
        
        Args:
            img (numpy.ndarray): Hình ảnh dạng mảng numpy (BGR)
            
        Returns:
            numpy.ndarray: Histogram đã chuẩn hóa
        """
        try:
            # Chuyển đổi kích thước của hình ảnh
            target_size = (100, 100)  # Kích thước chuẩn hóa
            img_resized = cv2.resize(img, target_size)
            
            # Tính toán histogram
            hist = cv2.calcHist(
                [img_resized], 
                [0, 1, 2], 
                None, 
                self.histogram_size, 
                [0, 256, 0, 256, 0, 256]
            )
            
            # Chuẩn hóa histogram
            cv2.normalize(hist, hist, 0, 1, cv2.NORM_MINMAX)
            
            return hist
        except Exception as e:
            print(f"Lỗi khi tính toán histogram: {str(e)}")
            # Trả về một histogram rỗng nếu có lỗi
            return np.zeros(tuple(self.histogram_size))
    
    def extract_features(self, img):
        """
        Trích xuất đặc trưng từ hình ảnh sử dụng SIFT
        
        Args:
            img (numpy.ndarray): Hình ảnh dạng mảng numpy (BGR)
            
        Returns:
            tuple: (keypoints, descriptors) đặc trưng của hình ảnh
        """
        try:
            # Chuyển đổi kích thước ảnh
            h, w = img.shape[:2]
            if max(h, w) > self.resize_max_size:
                scale = self.resize_max_size / max(h, w)
                img = cv2.resize(img, None, fx=scale, fy=scale)
            
            # Chuyển sang ảnh grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Tạo bộ trích xuất đặc trưng SIFT
            sift = cv2.SIFT_create()
            
            # Trích xuất đặc trưng
            keypoints, descriptors = sift.detectAndCompute(gray, None)
            
            return keypoints, descriptors
        except Exception as e:
            print(f"Lỗi khi trích xuất đặc trưng: {str(e)}")
            return None, None
    
    def compare_features(self, desc1, desc2):
        """
        So sánh hai bộ đặc trưng và tính độ tương đồng
        
        Args:
            desc1 (numpy.ndarray): Bộ đặc trưng thứ nhất
            desc2 (numpy.ndarray): Bộ đặc trưng thứ hai
            
        Returns:
            float: Độ tương đồng, giá trị từ 0 đến 1
        """
        # Kiểm tra các mô tả đặc trưng có giá trị không
        if desc1 is None or desc2 is None:
            return 0
            
        if len(desc1) < 2 or len(desc2) < 2:
            return 0
            
        try:
            # Sử dụng FLANN để tìm kiếm đặc trưng gần nhất
            FLANN_INDEX_KDTREE = 1
            index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=5)
            search_params = dict(checks=50)
            
            try:
                flann = cv2.FlannBasedMatcher(index_params, search_params)
                matches = flann.knnMatch(desc1, desc2, k=2)
            except:
                # Nếu FLANN không hoạt động, sử dụng BFMatcher
                bf = cv2.BFMatcher(cv2.NORM_L2)
                matches = bf.knnMatch(desc1, desc2, k=2)
            
            # Áp dụng bộ lọc Lowe's ratio test
            good_matches = []
            for m, n in matches:
                if m.distance < self.feature_match_ratio * n.distance:
                    good_matches.append(m)
            
            # Tính toán độ tương đồng
            return len(good_matches) / max(1, min(len(desc1), len(desc2)))
        except Exception as e:
            print(f"Lỗi khi so sánh đặc trưng: {str(e)}")
            return 0
    
    def compare_images(self, img1, img2):
        """
        So sánh hai hình ảnh và tính toán độ tương đồng tổng hợp
        
        Args:
            img1 (numpy.ndarray): Hình ảnh thứ nhất (BGR)
            img2 (numpy.ndarray): Hình ảnh thứ hai (BGR)
            
        Returns:
            float: Độ tương đồng tổng hợp, giá trị từ 0 đến 1
        """
        # Tính toán histogram và đặc trưng cho cả hai hình ảnh
        hist1 = self.calculate_histogram(img1)
        hist2 = self.calculate_histogram(img2)
        
        # So sánh histogram
        hist_similarity = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
        
        # Trích xuất và so sánh đặc trưng
        _, desc1 = self.extract_features(img1)
        _, desc2 = self.extract_features(img2)
        
        feature_similarity = 0
        if desc1 is not None and desc2 is not None and len(desc1) > 0 and len(desc2) > 0:
            feature_similarity = self.compare_features(desc1, desc2)
        
        # Kết hợp hai độ tương đồng
        combined_similarity = (self.hist_weight * hist_similarity + 
                               self.feature_weight * feature_similarity)
        
        return max(0, min(1, combined_similarity))  # Giới hạn giá trị từ 0 đến 1