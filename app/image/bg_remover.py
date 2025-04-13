#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module tách nền hình ảnh với thuật toán HSV
"""

import cv2
import numpy as np
from PIL import Image
import config

class BackgroundRemover:
    """Lớp xử lý và tách nền hình ảnh sử dụng phương pháp HSV"""
    
    def __init__(self):
        """Khởi tạo các tham số cho việc tách nền"""
        self.tolerance = config.IMAGE_ANALYSIS['background_removal']['tolerance']
        self.erosion_kernel_size = config.IMAGE_ANALYSIS['background_removal']['erosion_kernel_size']
        self.dilate_kernel_size = config.IMAGE_ANALYSIS['background_removal']['dilate_kernel_size']
    
    def remove_background(self, img, bg_color, method='hsv_improved'):
        """
        Tách nền khỏi hình ảnh dựa trên màu nền được chọn
        
        Args:
            img (numpy.ndarray): Hình ảnh dạng mảng numpy (BGR)
            bg_color (tuple): Màu nền (B, G, R)
            method (str): Tham số này giữ lại để tương thích, mọi phương pháp sẽ sử dụng HSV
            
        Returns:
            numpy.ndarray: Hình ảnh đã tách nền, có kênh alpha
        """
        try:
            return self._remove_background_hsv_improved(img, bg_color)
        except Exception as e:
            print(f"Lỗi khi tách nền: {str(e)}")
            # Trả về hình ảnh gốc với kênh alpha đầy đủ nếu có lỗi
            bgra = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)
            return bgra

    def _remove_background_hsv_improved(self, img, bg_color):
        """
        Tách nền nâng cao sử dụng không gian màu HSV với các cải tiến
        
        Args:
            img (numpy.ndarray): Hình ảnh dạng mảng numpy (BGR)
            bg_color (tuple): Màu nền (B, G, R)
            
        Returns:
            numpy.ndarray: Hình ảnh đã tách nền (BGRA)
        """
        # Chuyển đổi sang không gian màu HSV
        img_hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        bg_hsv = cv2.cvtColor(np.uint8([[bg_color]]), cv2.COLOR_BGR2HSV)[0][0]
        
        # Tính toán khoảng giá trị HSV cho nền với dung sai cao hơn
        # Đặc biệt tăng dung sai cho kênh Hue
        h_tolerance = min(90, self.tolerance * 2)  # Dung sai cao hơn cho Hue
        s_tolerance = self.tolerance
        v_tolerance = self.tolerance * 1.5  # Tăng dung sai cho Value
        
        # Xác định khoảng giá trị màu cho nền (HSV space)
        # Kênh Hue là kênh vòng tròn (0-179), cần xử lý đặc biệt
        if bg_hsv[0] - h_tolerance < 0:
            lower_hue1 = 0
            upper_hue1 = min(179, bg_hsv[0] + h_tolerance)
            lower_hue2 = max(0, 180 + (bg_hsv[0] - h_tolerance))
            upper_hue2 = 179
            
            # Tạo hai mask cho hai khoảng Hue
            lower_bound1 = np.array([lower_hue1, max(0, bg_hsv[1] - s_tolerance), max(0, bg_hsv[2] - v_tolerance)])
            upper_bound1 = np.array([upper_hue1, min(255, bg_hsv[1] + s_tolerance), min(255, bg_hsv[2] + v_tolerance)])
            
            lower_bound2 = np.array([lower_hue2, max(0, bg_hsv[1] - s_tolerance), max(0, bg_hsv[2] - v_tolerance)])
            upper_bound2 = np.array([upper_hue2, min(255, bg_hsv[1] + s_tolerance), min(255, bg_hsv[2] + v_tolerance)])
            
            mask1 = cv2.inRange(img_hsv, lower_bound1, upper_bound1)
            mask2 = cv2.inRange(img_hsv, lower_bound2, upper_bound2)
            mask = cv2.bitwise_or(mask1, mask2)
        
        elif bg_hsv[0] + h_tolerance > 179:
            lower_hue1 = max(0, bg_hsv[0] - h_tolerance)
            upper_hue1 = 179
            lower_hue2 = 0
            upper_hue2 = min(179, (bg_hsv[0] + h_tolerance) - 180)
            
            # Tạo hai mask cho hai khoảng Hue
            lower_bound1 = np.array([lower_hue1, max(0, bg_hsv[1] - s_tolerance), max(0, bg_hsv[2] - v_tolerance)])
            upper_bound1 = np.array([upper_hue1, min(255, bg_hsv[1] + s_tolerance), min(255, bg_hsv[2] + v_tolerance)])
            
            lower_bound2 = np.array([lower_hue2, max(0, bg_hsv[1] - s_tolerance), max(0, bg_hsv[2] - v_tolerance)])
            upper_bound2 = np.array([upper_hue2, min(255, bg_hsv[1] + s_tolerance), min(255, bg_hsv[2] + v_tolerance)])
            
            mask1 = cv2.inRange(img_hsv, lower_bound1, upper_bound1)
            mask2 = cv2.inRange(img_hsv, lower_bound2, upper_bound2)
            mask = cv2.bitwise_or(mask1, mask2)
        else:
            # Khoảng Hue bình thường
            lower_bound = np.array([
                max(0, bg_hsv[0] - h_tolerance),
                max(0, bg_hsv[1] - s_tolerance),
                max(0, bg_hsv[2] - v_tolerance)
            ])
            
            upper_bound = np.array([
                min(179, bg_hsv[0] + h_tolerance),
                min(255, bg_hsv[1] + s_tolerance),
                min(255, bg_hsv[2] + v_tolerance)
            ])
            
            # Tạo mask
            mask = cv2.inRange(img_hsv, lower_bound, upper_bound)
        
        # Đảo ngược mask để lấy đối tượng, không lấy nền
        mask = cv2.bitwise_not(mask)
        
        # Áp dụng phép xói mòn để loại bỏ nhiễu nhỏ
        kernel = np.ones((self.erosion_kernel_size, self.erosion_kernel_size), np.uint8)
        mask = cv2.erode(mask, kernel, iterations=1)
        
        # Áp dụng phép giãn nở để phục hồi đối tượng
        kernel = np.ones((self.dilate_kernel_size, self.dilate_kernel_size), np.uint8)
        mask = cv2.dilate(mask, kernel, iterations=2)
        
        # Áp dụng lọc trung vị để làm mịn mask
        mask = cv2.medianBlur(mask, 5)
        
        # Lấp đầy các lỗ trong mask
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        filled_mask = np.zeros_like(mask)
        cv2.drawContours(filled_mask, contours, -1, 255, cv2.FILLED)
        
        # Làm mịn mask bằng lọc Gaussian
        mask = cv2.GaussianBlur(filled_mask, (5, 5), 0)
        
        # Chuyển đổi hình ảnh sang BGRA
        bgra = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)
        bgra[:, :, 3] = mask
        
        return bgra
    
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
        if with_alpha:
            # Nếu có kênh alpha, chuyển BGRA sang RGBA
            img = cv2.cvtColor(cv_img, cv2.COLOR_BGRA2RGBA)
        else:
            # Nếu không có kênh alpha, chuyển BGR sang RGB
            img = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        
        return Image.fromarray(img)
    
    def remove_background_pil(self, pil_img, bg_color_rgb, method='hsv_improved'):
        """
        Tách nền khỏi hình ảnh PIL dựa trên màu nền RGB được chọn
        
        Args:
            pil_img (PIL.Image): Hình ảnh PIL
            bg_color_rgb (tuple): Màu nền (R, G, B)
            method (str): Phương pháp tách nền (tham số này giữ lại để tương thích)
            
        Returns:
            PIL.Image: Hình ảnh PIL đã tách nền, có kênh alpha
        """
        # Chuyển đổi từ RGB sang BGR cho màu nền
        bg_color_bgr = (bg_color_rgb[2], bg_color_rgb[1], bg_color_rgb[0])
        
        # Chuyển hình ảnh PIL sang OpenCV
        cv_img = self.pil_to_cv2(pil_img)
        
        # Tách nền với phương pháp HSV được cải tiến
        result_cv = self.remove_background(cv_img, bg_color_bgr)
        
        # Chuyển lại kết quả sang PIL
        return self.cv2_to_pil(result_cv, with_alpha=True)