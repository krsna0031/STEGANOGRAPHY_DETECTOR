"""
Django Models for Steganography Detection System
"""

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator
import uuid


class UploadedImage(models.Model):
    """
    Store uploaded images for analysis
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='uploads', null=True, blank=True)
    
    # Image file
    image = models.ImageField(
        upload_to='uploads/%Y/%m/%d/',
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'bmp', 'tiff'])]
    )
    filename = models.CharField(max_length=255)
    file_size = models.IntegerField()  # in bytes
    
    # Metadata
    width = models.IntegerField(null=True)
    height = models.IntegerField(null=True)
    format = models.CharField(max_length=10)
    
    # Timestamps
    uploaded_at = models.DateTimeField(auto_now_add=True)
    analyzed_at = models.DateTimeField(null=True, blank=True)
    
    # Analysis status
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('analyzing', 'Analyzing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    class Meta:
        db_table = 'uploaded_images'
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['user', '-uploaded_at']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.filename} ({self.id})"


class AnalysisResult(models.Model):
    """
    Store comprehensive analysis results
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    image = models.OneToOneField(UploadedImage, on_delete=models.CASCADE, related_name='result')
    
    # Overall verdict
    is_suspicious = models.BooleanField(default=False)
    confidence_score = models.FloatField()  # 0.0 to 1.0
    
    # Detection method scores
    lsb_score = models.FloatField(default=0.0)
    chi_square_score = models.FloatField(default=0.0)
    rs_score = models.FloatField(default=0.0)
    frequency_score = models.FloatField(default=0.0)
    metadata_score = models.FloatField(default=0.0)
    
    # CNN predictions
    cnn_confidence = models.FloatField(null=True, blank=True)
    cnn_prediction = models.CharField(max_length=10, null=True, blank=True)  # CLEAN or STEGO
    
    # Detailed results (JSON)
    lsb_details = models.JSONField(null=True, blank=True)
    chi_square_details = models.JSONField(null=True, blank=True)
    rs_details = models.JSONField(null=True, blank=True)
    frequency_details = models.JSONField(null=True, blank=True)
    metadata_details = models.JSONField(null=True, blank=True)
    
    # Estimated payload
    estimated_payload_size = models.FloatField(null=True, blank=True)  # in bytes
    estimated_payload_percentage = models.FloatField(null=True, blank=True)  # percentage of image
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'analysis_results'
        indexes = [
            models.Index(fields=['-confidence_score']),
            models.Index(fields=['is_suspicious']),
        ]
    
    def __str__(self):
        return f"Analysis for {self.image.filename} - {self.confidence_score:.2%}"


class DetectionHistory(models.Model):
    """
    Track detection history for statistics and improvements
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    image = models.ForeignKey(UploadedImage, on_delete=models.CASCADE, related_name='history')
    
    # Detection information
    method_used = models.CharField(max_length=50)  # LSB, CNN, Chi-Square, etc.
    detected = models.BooleanField()
    confidence = models.FloatField()
    
    # User feedback (for model improvement)
    user_confirmed = models.BooleanField(null=True, blank=True)
    user_feedback = models.TextField(blank=True)
    
    # Timestamp
    detected_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'detection_history'
        verbose_name_plural = 'detection histories'
        ordering = ['-detected_at']


class SteganographyTechnique(models.Model):
    """
    Catalog of known steganography techniques
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    category = models.CharField(max_length=50)  # LSB, DCT, DWT, etc.
    detection_methods = models.JSONField()  # List of applicable detection methods
    
    # Performance metrics
    detection_rate = models.FloatField(default=0.0)  # Success rate
    false_positive_rate = models.FloatField(default=0.0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'steganography_techniques'
    
    def __str__(self):
        return f"{self.name} ({self.category})"


class ModelVersion(models.Model):
    """
    Track different versions of ML models
    """
    version = models.CharField(max_length=20, unique=True)
    model_type = models.CharField(max_length=50)  # CNN, SVM, Random Forest, etc.
    model_path = models.CharField(max_length=255)
    
    # Performance metrics
    accuracy = models.FloatField()
    precision = models.FloatField()
    recall = models.FloatField()
    f1_score = models.FloatField()
    
    # Training info
    trained_on = models.DateTimeField()
    training_samples = models.IntegerField()
    
    # Status
    is_active = models.BooleanField(default=False)
    
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'model_versions'
        ordering = ['-trained_on']
    
    def __str__(self):
        return f"{self.model_type} v{self.version} (Acc: {self.accuracy:.2%})"


class AnalyticsLog(models.Model):
    """
    Analytics and logging for system monitoring
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # System metrics
    total_analyses = models.IntegerField(default=0)
    stego_detected = models.IntegerField(default=0)
    clean_detected = models.IntegerField(default=0)
    
    # Performance
    avg_analysis_time = models.FloatField(default=0.0)  # in seconds
    avg_confidence = models.FloatField(default=0.0)
    
    # Date
    date = models.DateField(unique=True)
    
    class Meta:
        db_table = 'analytics_logs'
        ordering = ['-date']
    
    def __str__(self):
        return f"Analytics for {self.date}"
