# 🚀 Quick Start Guide - Steganography Detection System

## 📋 Prerequisites Checklist

Before starting, ensure you have:
- [ ] Python 3.10 or higher installed
- [ ] pip package manager
- [ ] At least 4GB RAM
- [ ] 2GB free disk space
- [ ] (Optional) GPU with CUDA for faster CNN training

---

## ⚡ 5-Minute Quick Start

### Step 1: Setup Environment

```bash
# Clone/navigate to project
cd steganography-detector

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies (this may take 5-10 minutes)
pip install -r requirements.txt
```

### Step 2: Test Detection Algorithms

```bash
# Run the test suite
python test_detection.py
```

**Expected Output:**
```
🚀 STEGANOGRAPHY DETECTION SYSTEM - TEST SUITE
============================================================
Creating test images...
✅ Test images created

============================================================
🔍 TESTING LSB DETECTOR
============================================================
...
✅ ALL TESTS COMPLETED
```

### Step 3: Analyze Your Own Image

```python
# Create a simple script: analyze_image.py
from backend.detector_algorithms import SteganographyDetector

detector = SteganographyDetector()
results = detector.analyze('path/to/your/image.png')

print(f"Confidence Score: {results['confidence_score']:.2%}")
print(f"Suspicious: {results['is_suspicious']}")
```

```bash
# Run it
python analyze_image.py
```

---

## 📚 Detailed Setup

### Option 1: Statistical Detection Only (No Deep Learning)

If you just want to use statistical methods without CNN:

```bash
# Install minimal dependencies
pip install numpy scipy opencv-python Pillow scikit-image PyWavelets

# Run detection
python -c "
from backend.detector_algorithms import SteganographyDetector
detector = SteganographyDetector()
result = detector.analyze('data/test/clean_test.png')
print(f'Confidence: {result[\"confidence_score\"]:.2%}')
"
```

### Option 2: Full System with Deep Learning

```bash
# Install all dependencies
pip install -r requirements.txt

# Train CNN model (requires dataset)
python backend/cnn_detector.py
```

### Option 3: Django REST API

```bash
# Setup Django
python manage.py migrate
python manage.py createsuperuser

# Run server
python manage.py runserver

# Access at http://localhost:8000
```

---

## 🗂️ Project Structure

```
steganography-detector/
│
├── backend/
│   ├── detector_algorithms.py  # Statistical detection methods
│   ├── cnn_detector.py         # Deep learning models
│   ├── models.py               # Django models
│   ├── views.py                # Django API views
│   └── serializers.py          # DRF serializers
│
├── data/
│   ├── clean/                  # Clean images (for training)
│   ├── stego/                  # Steganography images
│   └── test/                   # Test images
│
├── models/                     # Trained ML models
│   └── best_stego_detector.h5
│
├── requirements.txt            # Python dependencies
├── test_detection.py          # Test suite
└── README.md                  # Full documentation
```

---

## 🎯 Usage Examples

### Example 1: Analyze Single Image

```python
from backend.detector_algorithms import SteganographyDetector

# Initialize detector
detector = SteganographyDetector()

# Analyze image
results = detector.analyze('suspicious_image.png')

# Print results
print(f"Overall Confidence: {results['confidence_score']:.2%}")
print(f"Verdict: {'SUSPICIOUS' if results['is_suspicious'] else 'CLEAN'}")

# Detailed analysis
print("\nMethod Breakdown:")
print(f"  LSB Analysis: {results['lsb_analysis']}")
print(f"  Chi-Square: {results['chi_square_analysis']}")
print(f"  RS Analysis: {results['rs_analysis']}")
```

### Example 2: Batch Analysis

```python
import os
from backend.detector_algorithms import SteganographyDetector

detector = SteganographyDetector()

# Analyze all images in a directory
image_dir = 'data/test/'
results_list = []

for filename in os.listdir(image_dir):
    if filename.endswith(('.png', '.jpg', '.jpeg')):
        filepath = os.path.join(image_dir, filename)
        result = detector.analyze(filepath)
        results_list.append({
            'filename': filename,
            'confidence': result['confidence_score'],
            'suspicious': result['is_suspicious']
        })

# Sort by confidence (most suspicious first)
results_list.sort(key=lambda x: x['confidence'], reverse=True)

# Print summary
for r in results_list:
    status = "⚠️  SUSPICIOUS" if r['suspicious'] else "✅ CLEAN"
    print(f"{r['filename']:30} {status} ({r['confidence']:.2%})")
```

### Example 3: Using CNN Detector

```python
from backend.cnn_detector import StegoNetCNN

# Initialize CNN detector
cnn = StegoNetCNN(img_size=256)

# Load pre-trained model
cnn.load_model('models/best_stego_detector.h5')

# Predict
confidence, prediction = cnn.predict('test_image.png')
print(f"CNN Prediction: {prediction} (Confidence: {confidence:.2%})")
```

### Example 4: Using Django API

```bash
# Start server
python manage.py runserver

# In another terminal, upload image via curl:
curl -X POST http://localhost:8000/api/analyze/ \
  -F "image=@test_image.png"

# Response:
# {
#   "id": "uuid-here",
#   "filename": "test_image.png",
#   "status": "completed",
#   ...
# }

# Get results:
curl http://localhost:8000/api/analyze/{uuid}/result/
```

---

## 🧪 Testing Your Setup

### Test 1: Import Check

```python
# test_imports.py
try:
    import cv2
    import numpy as np
    from PIL import Image
    import pywt
    from scipy import stats
    print("✅ All core dependencies imported successfully!")
except ImportError as e:
    print(f"❌ Import error: {e}")
```

### Test 2: Algorithm Check

```bash
# Run the comprehensive test
python test_detection.py

# Should output:
# ✅ ALL TESTS COMPLETED
```

### Test 3: CNN Check (if using deep learning)

```python
# test_cnn.py
try:
    import tensorflow as tf
    from backend.cnn_detector import StegoNetCNN
    
    cnn = StegoNetCNN()
    model = cnn.build_model()
    print(f"✅ CNN model built successfully!")
    print(f"   Total parameters: {model.count_params():,}")
except Exception as e:
    print(f"❌ CNN test failed: {e}")
```

---

## 🐛 Troubleshooting

### Issue: "TensorFlow not found"

**Solution:**
```bash
# Install TensorFlow separately
pip install tensorflow==2.15.0

# Or use CPU-only version (smaller, faster install)
pip install tensorflow-cpu==2.15.0
```

### Issue: "OpenCV import error"

**Solution:**
```bash
# Reinstall OpenCV
pip uninstall opencv-python
pip install opencv-python-headless==4.9.0.80
```

### Issue: "Memory error during CNN training"

**Solution:**
```python
# Reduce batch size in cnn_detector.py
detector.train(
    train_dir='data/train',
    val_dir='data/val',
    batch_size=16,  # Reduced from 32
    epochs=50
)
```

### Issue: "Module not found: backend"

**Solution:**
```bash
# Run from project root directory
cd steganography-detector

# Or add to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

---

## 📊 Performance Benchmarks

**On a typical laptop (Intel i5, 8GB RAM):**

| Operation | Time |
|-----------|------|
| Single image analysis (statistical) | ~0.5s |
| Single image analysis (with CNN) | ~2.0s |
| Batch analysis (100 images) | ~50s |
| CNN training (1 epoch, 1000 images) | ~2min |

**GPU Acceleration (NVIDIA GTX 1060):**

| Operation | Time | Speedup |
|-----------|------|---------|
| CNN training (1 epoch) | ~30s | 4x |
| Batch CNN inference (100 images) | ~15s | 6x |

---

## 🎓 Next Steps

Once you have the system running:

1. **Collect Dataset**
   - Download BOSSbase or ALASKA2 datasets
   - Create your own stego images using tools like `steghide`, `outguess`

2. **Train Custom CNN**
   - Prepare train/val/test splits
   - Experiment with different architectures
   - Fine-tune hyperparameters

3. **Build API**
   - Setup Django REST Framework
   - Add authentication
   - Deploy to cloud

4. **Create Frontend**
   - Build React UI for image upload
   - Add visualization of results
   - Create dashboard for statistics

5. **Optimize**
   - Profile performance bottlenecks
   - Implement caching
   - Add batch processing

---

## 📧 Need Help?

- Check the full README.md for detailed documentation
- Review the code comments in detector_algorithms.py
- Run the test suite for debugging

---

## 🎉 You're Ready!

Your steganography detection system is now set up and ready to use. Start by analyzing some test images and exploring the different detection methods!

**Happy detecting! 🔍**
