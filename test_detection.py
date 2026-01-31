"""
Test Script for Steganography Detection System

This script demonstrates the detection capabilities on sample images.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.detector_algorithms import SteganographyDetector
import cv2
import numpy as np
from PIL import Image
import json


def create_test_images():
    """
    Create sample clean and stego images for testing
    """
    print("Creating test images...")
    
    # Create clean test image
    clean_img = np.random.randint(0, 256, (256, 256, 3), dtype=np.uint8)
    cv2.imwrite('data/test/clean_test.png', clean_img)
    
    # Create stego image (LSB embedding simulation)
    stego_img = clean_img.copy()
    # Modify LSBs (simplified steganography)
    mask = np.random.randint(0, 2, (256, 256, 3), dtype=np.uint8)
    stego_img = (stego_img & 0xFE) | mask  # Set LSB to random values
    cv2.imwrite('data/test/stego_test.png', stego_img)
    
    print("✅ Test images created")
    return 'data/test/clean_test.png', 'data/test/stego_test.png'


def test_lsb_detector():
    """
    Test LSB detection algorithm
    """
    print("\n" + "="*60)
    print("🔍 TESTING LSB DETECTOR")
    print("="*60)
    
    detector = SteganographyDetector()
    
    # Test on clean image
    print("\nAnalyzing CLEAN image...")
    clean_result = detector.lsb_detector.analyze('data/test/clean_test.png')
    print("Clean Image LSB Analysis:")
    for key, value in clean_result.items():
        print(f"  {key}: {value:.4f}")
    
    # Test on stego image
    print("\nAnalyzing STEGO image...")
    stego_result = detector.lsb_detector.analyze('data/test/stego_test.png')
    print("Stego Image LSB Analysis:")
    for key, value in stego_result.items():
        print(f"  {key}: {value:.4f}")
    
    # Compare
    print("\nComparison:")
    print(f"  LSB Pattern Score Difference: {stego_result['lsb_pattern_score'] - clean_result['lsb_pattern_score']:.4f}")
    print(f"  Histogram Anomaly Difference: {stego_result['histogram_anomaly'] - clean_result['histogram_anomaly']:.4f}")


def test_chi_square_detector():
    """
    Test Chi-Square detection algorithm
    """
    print("\n" + "="*60)
    print("🔍 TESTING CHI-SQUARE DETECTOR")
    print("="*60)
    
    detector = SteganographyDetector()
    
    # Test on clean image
    print("\nAnalyzing CLEAN image...")
    clean_result = detector.chi_square_detector.analyze('data/test/clean_test.png')
    print("Clean Image Chi-Square Analysis:")
    for key, value in clean_result.items():
        print(f"  {key}: {value:.4f}")
    
    # Test on stego image
    print("\nAnalyzing STEGO image...")
    stego_result = detector.chi_square_detector.analyze('data/test/stego_test.png')
    print("Stego Image Chi-Square Analysis:")
    for key, value in stego_result.items():
        print(f"  {key}: {value:.4f}")


def test_rs_detector():
    """
    Test RS Analysis
    """
    print("\n" + "="*60)
    print("🔍 TESTING RS DETECTOR")
    print("="*60)
    
    detector = SteganographyDetector()
    
    # Test on clean image
    print("\nAnalyzing CLEAN image...")
    clean_result = detector.rs_detector.analyze('data/test/clean_test.png')
    print("Clean Image RS Analysis:")
    for key, value in clean_result.items():
        if isinstance(value, bool):
            print(f"  {key}: {value}")
        else:
            print(f"  {key}: {value:.4f}")
    
    # Test on stego image
    print("\nAnalyzing STEGO image...")
    stego_result = detector.rs_detector.analyze('data/test/stego_test.png')
    print("Stego Image RS Analysis:")
    for key, value in stego_result.items():
        if isinstance(value, bool):
            print(f"  {key}: {value}")
        else:
            print(f"  {key}: {value:.4f}")


def test_comprehensive_detection():
    """
    Test full detection pipeline
    """
    print("\n" + "="*60)
    print("🎯 COMPREHENSIVE DETECTION TEST")
    print("="*60)
    
    detector = SteganographyDetector()
    
    # Test on clean image
    print("\n📷 Analyzing CLEAN image...")
    clean_result = detector.analyze('data/test/clean_test.png')
    print(f"\n{'='*50}")
    print("CLEAN IMAGE - FULL ANALYSIS RESULTS")
    print(f"{'='*50}")
    print(f"Confidence Score: {clean_result['confidence_score']:.2%}")
    print(f"Suspicious: {'YES ⚠️' if clean_result['is_suspicious'] else 'NO ✅'}")
    print(f"\nMethod Scores:")
    print(f"  LSB Analysis: {clean_result['lsb_analysis']['lsb_pattern_score']:.4f}")
    print(f"  Chi-Square: {clean_result['chi_square_analysis']['probability']:.4f}")
    print(f"  RS Analysis: {clean_result['rs_analysis']['estimated_message_length']:.4f}")
    print(f"  Frequency Domain: {clean_result['frequency_analysis']['frequency_domain_score']:.4f}")
    
    # Test on stego image
    print("\n📷 Analyzing STEGO image...")
    stego_result = detector.analyze('data/test/stego_test.png')
    print(f"\n{'='*50}")
    print("STEGO IMAGE - FULL ANALYSIS RESULTS")
    print(f"{'='*50}")
    print(f"Confidence Score: {stego_result['confidence_score']:.2%}")
    print(f"Suspicious: {'YES ⚠️' if stego_result['is_suspicious'] else 'NO ✅'}")
    print(f"\nMethod Scores:")
    print(f"  LSB Analysis: {stego_result['lsb_analysis']['lsb_pattern_score']:.4f}")
    print(f"  Chi-Square: {stego_result['chi_square_analysis']['probability']:.4f}")
    print(f"  RS Analysis: {stego_result['rs_analysis']['estimated_message_length']:.4f}")
    print(f"  Frequency Domain: {stego_result['frequency_analysis']['frequency_domain_score']:.4f}")
    
    # Save results
    print("\n💾 Saving results to JSON...")
    results = {
        'clean_image': clean_result,
        'stego_image': stego_result
    }
    
    with open('data/test/test_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print("✅ Results saved to data/test/test_results.json")


def print_detection_summary(clean_result, stego_result):
    """
    Print summary comparison
    """
    print("\n" + "="*60)
    print("📊 DETECTION SUMMARY")
    print("="*60)
    
    print("\n┌─────────────────────────┬───────────┬───────────┬──────────┐")
    print("│ Detection Method        │   Clean   │   Stego   │   Delta  │")
    print("├─────────────────────────┼───────────┼───────────┼──────────┤")
    
    methods = [
        ('Overall Confidence', 'confidence_score', 'confidence_score'),
        ('LSB Pattern', 'lsb_analysis.lsb_pattern_score', 'lsb_analysis.lsb_pattern_score'),
        ('Chi-Square Prob', 'chi_square_analysis.probability', 'chi_square_analysis.probability'),
        ('RS Message Length', 'rs_analysis.estimated_message_length', 'rs_analysis.estimated_message_length'),
    ]
    
    for name, clean_key, stego_key in methods:
        clean_val = _get_nested_value(clean_result, clean_key.split('.'))
        stego_val = _get_nested_value(stego_result, stego_key.split('.'))
        delta = stego_val - clean_val
        
        print(f"│ {name:23} │ {clean_val:9.4f} │ {stego_val:9.4f} │ {delta:+8.4f} │")
    
    print("└─────────────────────────┴───────────┴───────────┴──────────┘")


def _get_nested_value(data, keys):
    """Helper to get nested dictionary value"""
    for key in keys:
        data = data[key]
    return data


def main():
    """
    Main test runner
    """
    print("\n🚀 STEGANOGRAPHY DETECTION SYSTEM - TEST SUITE")
    print("="*60)
    
    # Create test directory if not exists
    os.makedirs('data/test', exist_ok=True)
    
    # Create test images
    clean_path, stego_path = create_test_images()
    
    # Run individual tests
    test_lsb_detector()
    test_chi_square_detector()
    test_rs_detector()
    
    # Run comprehensive test
    test_comprehensive_detection()
    
    print("\n" + "="*60)
    print("✅ ALL TESTS COMPLETED")
    print("="*60)
    print("\nNext steps:")
    print("  1. Review test_results.json for detailed analysis")
    print("  2. Train CNN model with your dataset")
    print("  3. Start Django server and test API endpoints")
    print("  4. Build frontend interface")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
