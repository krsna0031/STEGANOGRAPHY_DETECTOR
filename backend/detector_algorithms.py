"""
Core Steganography Detection Algorithms

This module implements multiple detection techniques:
1. LSB (Least Significant Bit) Analysis
2. Chi-Square Attack
3. RS Analysis (Regular-Singular Groups)
4. Statistical Analysis
5. Histogram Analysis
"""

import numpy as np
from scipy import stats
from scipy.fftpack import dct
import cv2
from PIL import Image
import pywt
from typing import Dict, Tuple, List
import json


class LSBDetector:
    """
    Detect LSB steganography using statistical analysis
    """
    
    def __init__(self):
        self.threshold = 0.01
    
    def analyze(self, image_path: str) -> Dict[str, float]:
        """
        Analyze image for LSB steganography
        
        Returns:
            Dictionary with detection metrics
        """
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError("Invalid image file")
        
        # Convert to grayscale for analysis
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        results = {
            'lsb_pattern_score': self._detect_lsb_pattern(gray),
            'bit_plane_complexity': self._analyze_bit_planes(gray),
            'histogram_anomaly': self._histogram_analysis(gray),
            'noise_variance': self._noise_variance(gray)
        }
        
        return results
    
    def _detect_lsb_pattern(self, image: np.ndarray) -> float:
        """
        Detect patterns in LSB that indicate steganography
        """
        # Extract LSB plane
        lsb = image & 1
        
        # Calculate LSB randomness (should be ~0.5 for natural images)
        lsb_mean = np.mean(lsb)
        
        # Deviation from expected randomness
        randomness_score = abs(lsb_mean - 0.5) * 2
        
        return float(randomness_score)
    
    def _analyze_bit_planes(self, image: np.ndarray) -> float:
        """
        Analyze complexity across bit planes
        """
        complexities = []
        
        for i in range(8):
            # Extract i-th bit plane
            bit_plane = (image >> i) & 1
            
            # Calculate complexity (standard deviation)
            complexity = np.std(bit_plane)
            complexities.append(complexity)
        
        # LSB should have lower complexity in stego images
        lsb_complexity = complexities[0]
        avg_complexity = np.mean(complexities[1:4])
        
        # Ratio indicates potential steganography
        if avg_complexity > 0:
            ratio = lsb_complexity / avg_complexity
            return float(1 - ratio)  # Higher = more suspicious
        
        return 0.0
    
    def _histogram_analysis(self, image: np.ndarray) -> float:
        """
        Analyze histogram for characteristic patterns
        """
        hist, _ = np.histogram(image.flatten(), bins=256, range=(0, 256))
        
        # Pairs of Values Analysis
        # In LSB embedding, pairs (2i, 2i+1) become similar
        pair_similarity = 0
        for i in range(0, 256, 2):
            if i + 1 < 256:
                diff = abs(hist[i] - hist[i + 1])
                pair_similarity += diff
        
        # Normalize
        total_pixels = image.size
        anomaly_score = 1 - (pair_similarity / total_pixels)
        
        return float(max(0, anomaly_score))
    
    def _noise_variance(self, image: np.ndarray) -> float:
        """
        Calculate noise variance in LSB
        """
        lsb = image & 1
        
        # Calculate local variance
        variance = np.var(lsb)
        
        # Expected variance for random bits is ~0.25
        deviation = abs(variance - 0.25) / 0.25
        
        return float(deviation)


class ChiSquareDetector:
    """
    Chi-Square attack for detecting LSB steganography
    """
    
    def analyze(self, image_path: str) -> Dict[str, float]:
        """
        Perform chi-square analysis
        """
        img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        
        chi_square_values = []
        
        # Analyze in blocks
        block_size = 64
        h, w = img.shape
        
        for i in range(0, h - block_size, block_size):
            for j in range(0, w - block_size, block_size):
                block = img[i:i+block_size, j:j+block_size]
                chi_val = self._calculate_chi_square(block)
                chi_square_values.append(chi_val)
        
        avg_chi = np.mean(chi_square_values)
        max_chi = np.max(chi_square_values)
        
        return {
            'avg_chi_square': float(avg_chi),
            'max_chi_square': float(max_chi),
            'probability': float(self._chi_to_probability(avg_chi))
        }
    
    def _calculate_chi_square(self, block: np.ndarray) -> float:
        """
        Calculate chi-square statistic for a block
        """
        hist, _ = np.histogram(block.flatten(), bins=256, range=(0, 256))
        
        chi_square = 0
        
        # Check pairs of values
        for i in range(0, 256, 2):
            if i + 1 < 256:
                n = hist[i] + hist[i + 1]
                if n > 0:
                    expected = n / 2
                    chi_square += ((hist[i] - expected) ** 2 + 
                                  (hist[i + 1] - expected) ** 2) / expected
        
        return chi_square
    
    def _chi_to_probability(self, chi_value: float) -> float:
        """
        Convert chi-square value to probability of steganography
        """
        # Degrees of freedom = 127 (for 256 values paired)
        df = 127
        
        # Calculate p-value
        p_value = 1 - stats.chi2.cdf(chi_value, df)
        
        # Convert to probability of steganography (lower p-value = more likely)
        stego_probability = 1 - p_value
        
        return min(1.0, max(0.0, stego_probability))


class RSDetector:
    """
    RS (Regular-Singular) Analysis for steganography detection
    """
    
    def analyze(self, image_path: str) -> Dict[str, float]:
        """
        Perform RS analysis
        """
        img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        
        # Divide image into groups
        groups = self._create_groups(img)
        
        # Analyze regular and singular groups
        r_m, s_m = self._analyze_groups(groups, mask=1)
        r_m_neg, s_m_neg = self._analyze_groups(groups, mask=-1)
        
        # Calculate message length estimate
        message_length = self._estimate_message_length(r_m, s_m, r_m_neg, s_m_neg)
        
        return {
            'regular_positive': float(r_m),
            'singular_positive': float(s_m),
            'regular_negative': float(r_m_neg),
            'singular_negative': float(s_m_neg),
            'estimated_message_length': float(message_length),
            'is_stego': message_length > 0.05  # >5% embedding rate
        }
    
    def _create_groups(self, image: np.ndarray, group_size: int = 4) -> List[np.ndarray]:
        """
        Divide image into pixel groups
        """
        h, w = image.shape
        groups = []
        
        for i in range(0, h, group_size):
            for j in range(0, w, group_size):
                if i + group_size <= h and j + group_size <= w:
                    group = image[i:i+group_size, j:j+group_size].flatten()
                    groups.append(group)
        
        return groups
    
    def _flip_lsb(self, group: np.ndarray, mask: int) -> np.ndarray:
        """
        Flip LSBs according to mask
        """
        flipped = group.copy()
        for i in range(len(group)):
            flipped[i] = (group[i] & 0xFE) | ((group[i] & 1) ^ (mask & 1))
        return flipped
    
    def _is_regular(self, group: np.ndarray, flipped: np.ndarray) -> bool:
        """
        Check if group is regular (discrimination function increases)
        """
        f_original = self._discrimination_function(group)
        f_flipped = self._discrimination_function(flipped)
        return f_flipped > f_original
    
    def _discrimination_function(self, group: np.ndarray) -> float:
        """
        Calculate discrimination function for a group
        """
        if len(group) < 2:
            return 0
        
        # Sum of absolute differences
        diff_sum = 0
        for i in range(len(group) - 1):
            diff_sum += abs(int(group[i]) - int(group[i + 1]))
        
        return diff_sum
    
    def _analyze_groups(self, groups: List[np.ndarray], mask: int) -> Tuple[float, float]:
        """
        Analyze groups to count regular and singular
        """
        regular_count = 0
        singular_count = 0
        
        for group in groups:
            flipped = self._flip_lsb(group, mask)
            
            if self._is_regular(group, flipped):
                regular_count += 1
            else:
                singular_count += 1
        
        total = len(groups)
        return regular_count / total, singular_count / total
    
    def _estimate_message_length(self, r_m: float, s_m: float, 
                                 r_m_neg: float, s_m_neg: float) -> float:
        """
        Estimate the length of hidden message
        """
        # Theoretical relationship for RS analysis
        try:
            d_0 = r_m - s_m
            d_1 = r_m_neg - s_m_neg
            
            if abs(d_0 - d_1) < 0.001:
                return 0.0
            
            p = (d_0 - d_1) / (d_0 + d_1)
            
            # Clamp to [0, 1]
            return max(0.0, min(1.0, abs(p)))
        except:
            return 0.0


class FrequencyDomainDetector:
    """
    Detect steganography in frequency domain (DCT, DWT)
    """
    
    def analyze(self, image_path: str) -> Dict[str, float]:
        """
        Analyze frequency domain characteristics
        """
        img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        
        dct_score = self._analyze_dct(img)
        dwt_score = self._analyze_dwt(img)
        
        return {
            'dct_anomaly': dct_score,
            'dwt_anomaly': dwt_score,
            'frequency_domain_score': (dct_score + dwt_score) / 2
        }
    
    def _analyze_dct(self, image: np.ndarray) -> float:
        """
        Analyze DCT coefficients for anomalies
        """
        # Apply DCT
        dct_coeffs = dct(dct(image.T, norm='ortho').T, norm='ortho')
        
        # Analyze high-frequency components
        h, w = dct_coeffs.shape
        high_freq = dct_coeffs[h//2:, w//2:]
        
        # Calculate variance in high-frequency region
        variance = np.var(high_freq)
        
        # Normalize (typical range: 0-1000)
        score = min(1.0, variance / 1000)
        
        return float(score)
    
    def _analyze_dwt(self, image: np.ndarray) -> float:
        """
        Analyze wavelet coefficients
        """
        # Apply 2D wavelet transform
        coeffs = pywt.dwt2(image, 'haar')
        cA, (cH, cV, cD) = coeffs
        
        # Analyze detail coefficients
        detail_variance = (np.var(cH) + np.var(cV) + np.var(cD)) / 3
        
        # Normalize
        score = min(1.0, detail_variance / 500)
        
        return float(score)


class MetadataAnalyzer:
    """
    Analyze image metadata for suspicious patterns
    """
    
    def analyze(self, image_path: str) -> Dict[str, any]:
        """
        Extract and analyze metadata
        """
        results = {
            'has_exif': False,
            'exif_anomalies': 0,
            'file_size_ratio': 0.0,
            'suspicious_comments': False
        }
        
        try:
            img = Image.open(image_path)
            
            # Check EXIF data
            exif = img.getexif()
            if exif:
                results['has_exif'] = True
                results['exif_anomalies'] = self._check_exif_anomalies(exif)
            
            # File size analysis
            import os
            file_size = os.path.getsize(image_path)
            expected_size = img.width * img.height * 3  # RGB
            results['file_size_ratio'] = file_size / expected_size
            
            # Check for suspicious metadata
            if hasattr(img, 'info'):
                for key, value in img.info.items():
                    if self._is_suspicious_metadata(key, value):
                        results['suspicious_comments'] = True
                        break
        
        except Exception as e:
            results['error'] = str(e)
        
        return results
    
    def _check_exif_anomalies(self, exif: dict) -> int:
        """
        Check for unusual EXIF patterns
        """
        anomalies = 0
        
        # Check for unusually large comments
        if 'UserComment' in exif:
            if len(str(exif['UserComment'])) > 1000:
                anomalies += 1
        
        # Check for non-standard tags
        standard_tags = {271, 272, 274, 282, 283, 296, 305, 306}
        for tag in exif.keys():
            if tag > 50000:  # Very high tag numbers are suspicious
                anomalies += 1
        
        return anomalies
    
    def _is_suspicious_metadata(self, key: str, value: any) -> bool:
        """
        Check if metadata field is suspicious
        """
        suspicious_keys = ['comment', 'software', 'description']
        
        if any(k in key.lower() for k in suspicious_keys):
            value_str = str(value)
            # Check for high entropy or unusual characters
            if len(value_str) > 500:
                return True
            # Check for base64-like patterns
            if value_str.isalnum() and len(value_str) % 4 == 0:
                return True
        
        return False


class SteganographyDetector:
    """
    Main detector class combining all analysis techniques
    """
    
    def __init__(self):
        self.lsb_detector = LSBDetector()
        self.chi_square_detector = ChiSquareDetector()
        self.rs_detector = RSDetector()
        self.freq_detector = FrequencyDomainDetector()
        self.metadata_analyzer = MetadataAnalyzer()
    
    def analyze(self, image_path: str) -> Dict[str, any]:
        """
        Perform comprehensive steganography analysis
        
        Returns:
            Complete analysis results with confidence score
        """
        results = {
            'lsb_analysis': self.lsb_detector.analyze(image_path),
            'chi_square_analysis': self.chi_square_detector.analyze(image_path),
            'rs_analysis': self.rs_detector.analyze(image_path),
            'frequency_analysis': self.freq_detector.analyze(image_path),
            'metadata_analysis': self.metadata_analyzer.analyze(image_path)
        }
        
        # Calculate overall confidence score
        confidence = self._calculate_confidence(results)
        results['confidence_score'] = confidence
        results['is_suspicious'] = confidence > 0.7
        
        return results
    
    def _calculate_confidence(self, results: Dict) -> float:
        """
        Calculate overall confidence that image contains steganography
        """
        scores = []
        
        # LSB Analysis
        lsb = results['lsb_analysis']
        lsb_score = (lsb['lsb_pattern_score'] + 
                    lsb['bit_plane_complexity'] + 
                    lsb['histogram_anomaly']) / 3
        scores.append(lsb_score * 0.25)  # 25% weight
        
        # Chi-Square Analysis
        chi = results['chi_square_analysis']
        scores.append(chi['probability'] * 0.25)  # 25% weight
        
        # RS Analysis
        rs = results['rs_analysis']
        scores.append(rs['estimated_message_length'] * 0.30)  # 30% weight
        
        # Frequency Analysis
        freq = results['frequency_analysis']
        scores.append(freq['frequency_domain_score'] * 0.15)  # 15% weight
        
        # Metadata Analysis
        meta = results['metadata_analysis']
        meta_score = 0.5 if meta.get('suspicious_comments', False) else 0
        meta_score += 0.3 if meta.get('file_size_ratio', 0) > 1.5 else 0
        scores.append(meta_score * 0.05)  # 5% weight
        
        # Combine scores
        total_confidence = sum(scores)
        
        return min(1.0, max(0.0, total_confidence))


def _main():
    import argparse

    parser = argparse.ArgumentParser(description='Run steganography detectors on an image')
    parser.add_argument('image', help='Path to image file to analyze')
    parser.add_argument('--pretty', action='store_true', help='Pretty-print JSON output')
    args = parser.parse_args()

    detector = SteganographyDetector()
    results = detector.analyze(args.image)

    if args.pretty:
        print(json.dumps(results, indent=2))
    else:
        print(json.dumps(results))


if __name__ == "__main__":
    _main()
