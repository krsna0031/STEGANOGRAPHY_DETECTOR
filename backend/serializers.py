"""
Django REST Framework Serializers
"""

from rest_framework import serializers
from .models import (
    UploadedImage, AnalysisResult, DetectionHistory,
    SteganographyTechnique, ModelVersion
)


class UploadedImageSerializer(serializers.ModelSerializer):
    """
    Serializer for uploaded images
    """
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = UploadedImage
        fields = [
            'id', 'filename', 'image_url', 'file_size',
            'width', 'height', 'format', 'status',
            'uploaded_at', 'analyzed_at'
        ]
        read_only_fields = ['id', 'uploaded_at', 'analyzed_at']
    
    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and hasattr(obj.image, 'url'):
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None


class AnalysisResultSerializer(serializers.ModelSerializer):
    """
    Serializer for analysis results
    """
    image_info = UploadedImageSerializer(source='image', read_only=True)
    verdict = serializers.SerializerMethodField()
    confidence_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = AnalysisResult
        fields = [
            'id', 'image_info', 'is_suspicious', 'confidence_score',
            'confidence_percentage', 'verdict',
            'lsb_score', 'chi_square_score', 'rs_score',
            'frequency_score', 'metadata_score',
            'cnn_confidence', 'cnn_prediction',
            'lsb_details', 'chi_square_details', 'rs_details',
            'frequency_details', 'metadata_details',
            'estimated_payload_size', 'estimated_payload_percentage',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_verdict(self, obj):
        if obj.is_suspicious:
            if obj.confidence_score > 0.9:
                return "HIGHLY SUSPICIOUS - Steganography detected with high confidence"
            elif obj.confidence_score > 0.7:
                return "SUSPICIOUS - Likely contains hidden data"
            else:
                return "POTENTIALLY SUSPICIOUS - Further investigation recommended"
        else:
            if obj.confidence_score < 0.3:
                return "CLEAN - No steganography detected"
            else:
                return "LIKELY CLEAN - Low probability of hidden data"
    
    def get_confidence_percentage(self, obj):
        return f"{obj.confidence_score * 100:.2f}%"


class DetectionHistorySerializer(serializers.ModelSerializer):
    """
    Serializer for detection history
    """
    image_filename = serializers.CharField(source='image.filename', read_only=True)
    confidence_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = DetectionHistory
        fields = [
            'id', 'image_filename', 'method_used',
            'detected', 'confidence', 'confidence_percentage',
            'user_confirmed', 'user_feedback', 'detected_at'
        ]
        read_only_fields = ['id', 'detected_at']
    
    def get_confidence_percentage(self, obj):
        return f"{obj.confidence * 100:.2f}%"


class SteganographyTechniqueSerializer(serializers.ModelSerializer):
    """
    Serializer for steganography techniques
    """
    detection_rate_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = SteganographyTechnique
        fields = [
            'id', 'name', 'description', 'category',
            'detection_methods', 'detection_rate',
            'detection_rate_percentage', 'false_positive_rate'
        ]
    
    def get_detection_rate_percentage(self, obj):
        return f"{obj.detection_rate * 100:.2f}%"


class ModelVersionSerializer(serializers.ModelSerializer):
    """
    Serializer for ML model versions
    """
    performance_metrics = serializers.SerializerMethodField()
    
    class Meta:
        model = ModelVersion
        fields = [
            'version', 'model_type', 'accuracy', 'precision',
            'recall', 'f1_score', 'performance_metrics',
            'trained_on', 'training_samples', 'is_active'
        ]
    
    def get_performance_metrics(self, obj):
        return {
            'accuracy': f"{obj.accuracy * 100:.2f}%",
            'precision': f"{obj.precision * 100:.2f}%",
            'recall': f"{obj.recall * 100:.2f}%",
            'f1_score': f"{obj.f1_score * 100:.2f}%"
        }
