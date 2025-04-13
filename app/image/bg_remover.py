#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module tách nền hình ảnh với các thuật toán nâng cao
"""

import cv2
import numpy as np
from PIL import Image
import config

class BackgroundRemover:
    """Lớp xử lý và tách nền hình ảnh với nhiều phương pháp khác nhau"""
    
    def __init__(self):
        """Khởi tạo các tham số cho việc tách nền"""
        self.tolerance = config.IMAGE_ANALYSIS['background_removal']['tolerance']
        self.erosion_kernel_size = config.IMAGE_ANALYSIS['background_removal']['erosion_kernel_size']
        self.dilate_kernel_size = config.IMAGE_ANALYSIS['background_removal']['dilate_kernel_size']
    
    def remove_background(self, img, bg_color, method='color'):
        """
        Tách nền khỏi hình ảnh dựa trên màu nền được chọn hoặc phương pháp khác
        
        Args:
            img (numpy.ndarray): Hình ảnh dạng mảng numpy (BGR)
            bg_color (tuple): Màu nền (B, G, R)
            method (str): Phương pháp tách nền: 'color', 'hsv_improved', 'grabcut', 'adaptive_threshold'
            
        Returns:
            numpy.ndarray: Hình ảnh đã tách nền, có kênh alpha
        """
        try:
            if method == 'color':
                return self._remove_background_color(img, bg_color)
            elif method == 'hsv_improved':
                return self._remove_background_hsv_improved(img, bg_color)
            elif method == 'grabcut':
                return self._remove_background_grabcut(img, bg_color)
            elif method == 'adaptive_threshold':
                return self._remove_background_adaptive(img, bg_color)
            else:
                # Mặc định sử dụng phương pháp màu
                return self._remove_background_color(img, bg_color)
        except Exception as e:
            print(f"Lỗi khi tách nền: {str(e)}")
            # Trả về hình ảnh gốc với kênh alpha đầy đủ nếu có lỗi
            bgra = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)
            return bgra

    def _remove_background_color(self, img, bg_color):
        """
        Tách nền dựa trên khoảng cách màu trong không gian RGB
        
        Args:
            img (numpy.ndarray): Hình ảnh dạng mảng numpy (BGR)
            bg_color (tuple): Màu nền (B, G, R)
            
        Returns:
            numpy.ndarray: Hình ảnh đã tách nền (BGRA)
        """
        # Tạo một bản sao của hình ảnh
        img_copy = img.copy()
        
        # Tính toán khoảng cách Euclidean giữa mỗi pixel và màu nền
        b, g, r = cv2.split(img_copy)
        bg_b, bg_g, bg_r = bg_color
        
        # Tính khoảng cách Euclidean mỗi kênh màu
        diff_b = cv2.absdiff(b, np.ones_like(b) * bg_b)
        diff_g = cv2.absdiff(g, np.ones_like(g) * bg_g)
        diff_r = cv2.absdiff(r, np.ones_like(r) * bg_r)
        
        # Kết hợp khoảng cách
        color_distance = cv2.sqrt(
            cv2.add(
                cv2.add(
                    cv2.multiply(diff_b, diff_b),
                    cv2.multiply(diff_g, diff_g)
                ),
                cv2.multiply(diff_r, diff_r)
            )
        )
        
        # Tạo mask dựa trên khoảng cách màu và ngưỡng dung sai
        mask = cv2.compare(color_distance, np.ones_like(color_distance) * self.tolerance, cv2.CMP_GT)
        
        # Áp dụng các phép biến đổi hình thái học để cải thiện mask
        kernel = np.ones((3, 3), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=2)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=3)
        
        # Chuyển đổi hình ảnh sang BGRA
        bgra = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)
        
        # Áp dụng mask vào kênh alpha
        bgra[:, :, 3] = mask
        
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
    
    def _remove_background_grabcut(self, img, bg_color):
        """
        Tách nền sử dụng thuật toán GrabCut dựa trên màu nền
        
        Args:
            img (numpy.ndarray): Hình ảnh dạng mảng numpy (BGR)
            bg_color (tuple): Màu nền (B, G, R)
            
        Returns:
            numpy.ndarray: Hình ảnh đã tách nền (BGRA)
        """
        # Chuyển đổi sang không gian màu HSV
        img_hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        bg_hsv = cv2.cvtColor(np.uint8([[bg_color]]), cv2.COLOR_BGR2HSV)[0][0]
        
        # Xác định khoảng giá trị màu cho nền
        lower_bound = np.array([
            max(0, bg_hsv[0] - self.tolerance),
            max(0, bg_hsv[1] - self.tolerance),
            max(0, bg_hsv[2] - self.tolerance)
        ])
        
        upper_bound = np.array([
            min(179, bg_hsv[0] + self.tolerance),
            min(255, bg_hsv[1] + self.tolerance),
            min(255, bg_hsv[2] + self.tolerance)
        ])
        
        # Tạo mask ban đầu dựa trên màu
        mask = cv2.inRange(img_hsv, lower_bound, upper_bound)
        
        # Tạo mask cho GrabCut
        # 0 = sure background, 1 = sure foreground, 2 = probable background, 3 = probable foreground
        grabcut_mask = np.ones(img.shape[:2], np.uint8) * 2  # Mặc định là probable background
        grabcut_mask[mask == 0] = 0  # Nền chắc chắn là khu vực có màu khớp
        
        # Thêm viền chắc chắn là nền
        border_size = 5
        grabcut_mask[:border_size, :] = 0
        grabcut_mask[-border_size:, :] = 0
        grabcut_mask[:, :border_size] = 0
        grabcut_mask[:, -border_size:] = 0
        
        # Chuẩn bị các biến cho GrabCut
        bgdModel = np.zeros((1, 65), np.float64)
        fgdModel = np.zeros((1, 65), np.float64)
        
        # Thực hiện GrabCut
        try:
            # Thực hiện GrabCut với số lần lặp thấp
            cv2.grabCut(img, grabcut_mask, None, bgdModel, fgdModel, 3, cv2.GC_INIT_WITH_MASK)
            
            # Tạo mask từ kết quả GrabCut
            # 0 & 2 = nền, 1 & 3 = đối tượng
            mask2 = np.where((grabcut_mask == 2) | (grabcut_mask == 0), 0, 1).astype('uint8')
            
            # Áp dụng các phép biến đổi hình thái học để cải thiện mask
            kernel = np.ones((3, 3), np.uint8)
            mask2 = cv2.morphologyEx(mask2, cv2.MORPH_OPEN, kernel, iterations=1)
            mask2 = cv2.morphologyEx(mask2, cv2.MORPH_CLOSE, kernel, iterations=2)
            
            # Làm mịn mask
            mask2 = cv2.GaussianBlur(mask2 * 255, (5, 5), 0)
            
            # Chuyển đổi hình ảnh sang BGRA
            bgra = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)
            bgra[:, :, 3] = mask2
            
            return bgra
        except Exception as e:
            print(f"Lỗi khi sử dụng GrabCut: {str(e)}")
            # Trở về phương pháp HSV nếu GrabCut thất bại
            return self._remove_background_hsv_improved(img, bg_color)
    
    def _remove_background_adaptive(self, img, bg_color):
        """
        Tách nền sử dụng ngưỡng thích ứng dựa trên màu nền và gradient
        
        Args:
            img (numpy.ndarray): Hình ảnh dạng mảng numpy (BGR)
            bg_color (tuple): Màu nền (B, G, R)
            
        Returns:
            numpy.ndarray: Hình ảnh đã tách nền (BGRA)
        """
        # Chuyển đổi sang ảnh grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Tính toán gradient để phát hiện viền
        gradient_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        gradient_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        gradient = cv2.magnitude(gradient_x, gradient_y)
        gradient = cv2.normalize(gradient, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
        
        # Áp dụng ngưỡng thích ứng để phát hiện đối tượng
        binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                      cv2.THRESH_BINARY, 11, 2)
        
        # Kết hợp với phát hiện dựa trên màu nền
        # Chuyển đổi sang không gian màu HSV
        img_hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        bg_hsv = cv2.cvtColor(np.uint8([[bg_color]]), cv2.COLOR_BGR2HSV)[0][0]
        
        # Xác định khoảng giá trị màu cho nền
        lower_bound = np.array([
            max(0, bg_hsv[0] - self.tolerance * 1.5),
            max(0, bg_hsv[1] - self.tolerance),
            max(0, bg_hsv[2] - self.tolerance * 1.5)
        ])
        
        upper_bound = np.array([
            min(179, bg_hsv[0] + self.tolerance * 1.5),
            min(255, bg_hsv[1] + self.tolerance),
            min(255, bg_hsv[2] + self.tolerance * 1.5)
        ])
        
        # Tạo mask dựa trên màu
        color_mask = cv2.inRange(img_hsv, lower_bound, upper_bound)
        
        # Đảo ngược mask để lấy đối tượng, không lấy nền
        color_mask = cv2.bitwise_not(color_mask)
        
        # Kết hợp các mask
        combined_mask = cv2.bitwise_and(binary, color_mask)
        
        # Áp dụng các phép biến đổi hình thái học
        kernel = np.ones((3, 3), np.uint8)
        mask = cv2.morphologyEx(combined_mask, cv2.MORPH_OPEN, kernel, iterations=1)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=3)
        
        # Phát hiện và điền các vùng là đối tượng
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        mask_filled = np.zeros_like(mask)
        
        # Chỉ giữ lại các contour đủ lớn
        min_contour_area = 100  # Có thể điều chỉnh tùy theo ảnh
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > min_contour_area:
                cv2.drawContours(mask_filled, [contour], 0, 255, -1)
        
        # Làm mịn mask
        mask_final = cv2.GaussianBlur(mask_filled, (5, 5), 0)
        
        # Tạo ảnh kết quả
        bgra = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)
        bgra[:, :, 3] = mask_final
        
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
            method (str): Phương pháp tách nền
            
        Returns:
            PIL.Image: Hình ảnh PIL đã tách nền, có kênh alpha
        """
        # Chuyển đổi từ RGB sang BGR cho màu nền
        bg_color_bgr = (bg_color_rgb[2], bg_color_rgb[1], bg_color_rgb[0])
        
        # Chuyển hình ảnh PIL sang OpenCV
        cv_img = self.pil_to_cv2(pil_img)
        
        # Tách nền với phương pháp đã chọn
        result_cv = self.remove_background(cv_img, bg_color_bgr, method)
        
        # Chuyển lại kết quả sang PIL
        return self.cv2_to_pil(result_cv, with_alpha=True)