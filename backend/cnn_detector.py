"""
Deep Learning Steganography Detector using CNN

This module implements a Convolutional Neural Network for detecting
steganography in images. The model learns patterns that distinguish
clean images from stego images.
"""

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, models
from tensorflow.keras.preprocessing.image import ImageDataGenerator
import numpy as np
import cv2
from pathlib import Path
from typing import Tuple, Dict
import json


class StegoNetCNN:
    """
    Custom CNN architecture for steganography detection
    
    Architecture inspired by:
    - Xu et al. "Structural Design of Convolutional Neural Networks for Steganalysis"
    - Ye et al. "Deep Learning Hierarchical Representations for Image Steganalysis"
    """
    
    def __init__(self, img_size: int = 256):
        self.img_size = img_size
        self.model = None
        self.history = None
    
    def build_model(self) -> keras.Model:
        """
        Build the CNN architecture
        
        Returns:
            Compiled Keras model
        """
        inputs = layers.Input(shape=(self.img_size, self.img_size, 3))
        
        # Preprocessing layer - High-pass filter for noise extraction
        x = self._preprocessing_layer(inputs)
        
        # Block 1: Feature extraction
        x = layers.Conv2D(32, (5, 5), activation='relu', padding='same')(x)
        x = layers.BatchNormalization()(x)
        x = layers.MaxPooling2D((2, 2))(x)
        x = layers.Dropout(0.25)(x)
        
        # Block 2: Deeper feature extraction
        x = layers.Conv2D(64, (3, 3), activation='relu', padding='same')(x)
        x = layers.BatchNormalization()(x)
        x = layers.Conv2D(64, (3, 3), activation='relu', padding='same')(x)
        x = layers.BatchNormalization()(x)
        x = layers.MaxPooling2D((2, 2))(x)
        x = layers.Dropout(0.25)(x)
        
        # Block 3: Pattern recognition
        x = layers.Conv2D(128, (3, 3), activation='relu', padding='same')(x)
        x = layers.BatchNormalization()(x)
        x = layers.Conv2D(128, (3, 3), activation='relu', padding='same')(x)
        x = layers.BatchNormalization()(x)
        x = layers.MaxPooling2D((2, 2))(x)
        x = layers.Dropout(0.3)(x)
        
        # Block 4: High-level features
        x = layers.Conv2D(256, (3, 3), activation='relu', padding='same')(x)
        x = layers.BatchNormalization()(x)
        x = layers.Conv2D(256, (3, 3), activation='relu', padding='same')(x)
        x = layers.BatchNormalization()(x)
        x = layers.GlobalAveragePooling2D()(x)
        
        # Dense layers
        x = layers.Dense(512, activation='relu')(x)
        x = layers.Dropout(0.5)(x)
        x = layers.Dense(256, activation='relu')(x)
        x = layers.Dropout(0.5)(x)
        
        # Output layer
        outputs = layers.Dense(1, activation='sigmoid')(x)
        
        model = models.Model(inputs=inputs, outputs=outputs, name='StegoNet')
        
        # Compile
        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=0.0001),
            loss='binary_crossentropy',
            metrics=['accuracy', keras.metrics.Precision(), keras.metrics.Recall()]
        )
        
        self.model = model
        return model
    
    def _preprocessing_layer(self, inputs):
        """
        Apply high-pass filter to extract noise residuals
        This helps detect steganographic modifications
        """
        # SRM (Spatial Rich Model) inspired preprocessing
        # High-pass kernel
        kernel = np.array([
            [-1, -2, -1],
            [-2, 12, -2],
            [-1, -2, -1]
        ], dtype=np.float32) / 12.0
        
        kernel = kernel.reshape(3, 3, 1, 1)
        kernel = np.repeat(kernel, 3, axis=2)  # For RGB channels
        
        # Convert to TensorFlow constant
        kernel_tf = tf.constant(kernel, dtype=tf.float32)
        
        # Apply convolution
        filtered = tf.nn.conv2d(
            inputs,
            kernel_tf,
            strides=[1, 1, 1, 1],
            padding='SAME'
        )
        
        return filtered
    
    def train(self, 
              train_dir: str,
              val_dir: str,
              epochs: int = 50,
              batch_size: int = 32) -> Dict:
        """
        Train the model
        
        Args:
            train_dir: Directory with train/clean and train/stego subdirectories
            val_dir: Directory with val/clean and val/stego subdirectories
            epochs: Number of training epochs
            batch_size: Batch size
            
        Returns:
            Training history
        """
        if self.model is None:
            self.build_model()
        
        # Data augmentation
        train_datagen = ImageDataGenerator(
            rescale=1./255,
            rotation_range=20,
            width_shift_range=0.1,
            height_shift_range=0.1,
            horizontal_flip=True,
            zoom_range=0.1
        )
        
        val_datagen = ImageDataGenerator(rescale=1./255)
        
        # Load data
        train_generator = train_datagen.flow_from_directory(
            train_dir,
            target_size=(self.img_size, self.img_size),
            batch_size=batch_size,
            class_mode='binary',
            classes=['clean', 'stego']
        )
        
        val_generator = val_datagen.flow_from_directory(
            val_dir,
            target_size=(self.img_size, self.img_size),
            batch_size=batch_size,
            class_mode='binary',
            classes=['clean', 'stego']
        )
        
        # Callbacks
        callbacks = [
            keras.callbacks.EarlyStopping(
                monitor='val_loss',
                patience=10,
                restore_best_weights=True
            ),
            keras.callbacks.ReduceLROnPlateau(
                monitor='val_loss',
                factor=0.5,
                patience=5,
                min_lr=1e-7
            ),
            keras.callbacks.ModelCheckpoint(
                'models/best_stego_detector.h5',
                monitor='val_accuracy',
                save_best_only=True
            )
        ]
        
        # Train
        self.history = self.model.fit(
            train_generator,
            epochs=epochs,
            validation_data=val_generator,
            callbacks=callbacks
        )
        
        return self.history.history
    
    def predict(self, image_path: str) -> Tuple[float, str]:
        """
        Predict if an image contains steganography
        
        Args:
            image_path: Path to image
            
        Returns:
            Tuple of (confidence_score, prediction)
        """
        if self.model is None:
            raise ValueError("Model not trained or loaded")
        
        # Load and preprocess image
        img = cv2.imread(image_path)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = cv2.resize(img, (self.img_size, self.img_size))
        img = img / 255.0
        img = np.expand_dims(img, axis=0)
        
        # Predict
        prediction = self.model.predict(img, verbose=0)[0][0]
        
        # Interpret
        label = "STEGO" if prediction > 0.5 else "CLEAN"
        confidence = prediction if prediction > 0.5 else (1 - prediction)
        
        return float(confidence), label
    
    def save_model(self, path: str):
        """Save trained model"""
        if self.model:
            self.model.save(path)
            print(f"Model saved to {path}")
    
    def load_model(self, path: str):
        """Load pre-trained model"""
        self.model = keras.models.load_model(path)
        print(f"Model loaded from {path}")
    
    def evaluate(self, test_dir: str, batch_size: int = 32) -> Dict:
        """
        Evaluate model on test set
        
        Args:
            test_dir: Directory with test/clean and test/stego subdirectories
            batch_size: Batch size
            
        Returns:
            Dictionary with evaluation metrics
        """
        if self.model is None:
            raise ValueError("Model not trained or loaded")
        
        test_datagen = ImageDataGenerator(rescale=1./255)
        
        test_generator = test_datagen.flow_from_directory(
            test_dir,
            target_size=(self.img_size, self.img_size),
            batch_size=batch_size,
            class_mode='binary',
            classes=['clean', 'stego'],
            shuffle=False
        )
        
        # Evaluate
        results = self.model.evaluate(test_generator)
        
        metrics = {
            'loss': results[0],
            'accuracy': results[1],
            'precision': results[2],
            'recall': results[3]
        }
        
        # Calculate F1 score
        if metrics['precision'] + metrics['recall'] > 0:
            metrics['f1_score'] = (2 * metrics['precision'] * metrics['recall']) / \
                                 (metrics['precision'] + metrics['recall'])
        else:
            metrics['f1_score'] = 0.0
        
        return metrics


class EnsembleDetector:
    """
    Ensemble of multiple CNN models for robust detection
    """
    
    def __init__(self, models: list):
        self.models = models
    
    def predict(self, image_path: str) -> Tuple[float, str]:
        """
        Ensemble prediction using voting
        
        Args:
            image_path: Path to image
            
        Returns:
            Tuple of (confidence_score, prediction)
        """
        predictions = []
        
        for model in self.models:
            conf, label = model.predict(image_path)
            predictions.append(conf if label == "STEGO" else (1 - conf))
        
        # Average predictions
        avg_prediction = np.mean(predictions)
        
        label = "STEGO" if avg_prediction > 0.5 else "CLEAN"
        confidence = avg_prediction if avg_prediction > 0.5 else (1 - avg_prediction)
        
        return float(confidence), label


class TransferLearningDetector:
    """
    Use transfer learning with pre-trained models (ResNet, EfficientNet)
    for steganography detection
    """
    
    def __init__(self, base_model: str = 'EfficientNetB0', img_size: int = 224):
        self.base_model_name = base_model
        self.img_size = img_size
        self.model = None
    
    def build_model(self) -> keras.Model:
        """
        Build model using transfer learning
        """
        # Load base model
        if self.base_model_name == 'EfficientNetB0':
            base_model = keras.applications.EfficientNetB0(
                include_top=False,
                weights='imagenet',
                input_shape=(self.img_size, self.img_size, 3)
            )
        elif self.base_model_name == 'ResNet50':
            base_model = keras.applications.ResNet50(
                include_top=False,
                weights='imagenet',
                input_shape=(self.img_size, self.img_size, 3)
            )
        else:
            raise ValueError(f"Unknown base model: {self.base_model_name}")
        
        # Freeze base model
        base_model.trainable = False
        
        # Add custom head
        inputs = layers.Input(shape=(self.img_size, self.img_size, 3))
        x = base_model(inputs, training=False)
        x = layers.GlobalAveragePooling2D()(x)
        x = layers.Dense(256, activation='relu')(x)
        x = layers.Dropout(0.5)(x)
        x = layers.Dense(128, activation='relu')(x)
        x = layers.Dropout(0.3)(x)
        outputs = layers.Dense(1, activation='sigmoid')(x)
        
        model = models.Model(inputs=inputs, outputs=outputs)
        
        # Compile
        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=0.001),
            loss='binary_crossentropy',
            metrics=['accuracy', keras.metrics.Precision(), keras.metrics.Recall()]
        )
        
        self.model = model
        return model
    
    def fine_tune(self, num_layers: int = 20):
        """
        Unfreeze and fine-tune top layers
        
        Args:
            num_layers: Number of layers to unfreeze from the top
        """
        if self.model is None:
            raise ValueError("Model not built")
        
        # Unfreeze top layers
        base_model = self.model.layers[1]
        base_model.trainable = True
        
        for layer in base_model.layers[:-num_layers]:
            layer.trainable = False
        
        # Recompile with lower learning rate
        self.model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=0.0001),
            loss='binary_crossentropy',
            metrics=['accuracy', keras.metrics.Precision(), keras.metrics.Recall()]
        )
        
        print(f"Fine-tuning enabled for top {num_layers} layers")


# Example usage and training script
def create_and_train_detector():
    """
    Example training pipeline
    """
    # Initialize detector
    detector = StegoNetCNN(img_size=256)
    
    # Build model
    model = detector.build_model()
    print(model.summary())
    
    # Train (assuming data directories exist)
    # history = detector.train(
    #     train_dir='data/train',
    #     val_dir='data/val',
    #     epochs=50,
    #     batch_size=32
    # )
    
    # Save model
    # detector.save_model('models/stego_detector_v1.h5')
    
    # Evaluate
    # metrics = detector.evaluate('data/test')
    # print(f"Test Accuracy: {metrics['accuracy']:.4f}")
    # print(f"F1 Score: {metrics['f1_score']:.4f}")


if __name__ == "__main__":
    create_and_train_detector()
