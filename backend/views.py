"""
Django REST API Views for Steganography Detection
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser
from django.utils import timezone
from django.core.files.storage import default_storage
import os
import time
from PIL import Image

from .models import (
    UploadedImage, AnalysisResult, DetectionHistory,
    SteganographyTechnique, ModelVersion
)
from .serializers import (
    UploadedImageSerializer, AnalysisResultSerializer,
    DetectionHistorySerializer, SteganographyTechniqueSerializer
)
from .detector_algorithms import SteganographyDetector
from .cnn_detector import StegoNetCNN


class ImageAnalysisViewSet(viewsets.ModelViewSet):
    """
    API endpoint for image analysis
    """
    queryset = UploadedImage.objects.all()
    serializer_class = UploadedImageSerializer
    permission_classes = [AllowAny]  # Change to IsAuthenticated in production
    parser_classes = (MultiPartParser, FormParser)
    
    def create(self, request, *args, **kwargs):
        """
        Upload and analyze an image
        """
        if 'image' not in request.FILES:
            return Response(
                {'error': 'No image file provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        image_file = request.FILES['image']
        
        # Validate file size (max 20MB)
        max_size = 20 * 1024 * 1024  # 20MB
        if image_file.size > max_size:
            return Response(
                {'error': f'File size exceeds maximum allowed size of {max_size / (1024*1024)}MB'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate file type
        try:
            img = Image.open(image_file)
            img.verify()
            image_file.seek(0)  # Reset file pointer after verify
        except Exception as e:
            return Response(
                {'error': f'Invalid image file: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create UploadedImage object
        uploaded_image = UploadedImage.objects.create(
            user=request.user if request.user.is_authenticated else None,
            image=image_file,
            filename=image_file.name,
            file_size=image_file.size,
            width=img.width,
            height=img.height,
            format=img.format,
            status='pending'
        )
        
        # Trigger analysis
        self._analyze_image(uploaded_image)
        
        serializer = self.get_serializer(uploaded_image)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def _analyze_image(self, uploaded_image):
        """
        Perform comprehensive steganography analysis
        """
        try:
            uploaded_image.status = 'analyzing'
            uploaded_image.save()
            
            start_time = time.time()
            
            # Get image path
            image_path = uploaded_image.image.path
            
            # Statistical Analysis
            statistical_detector = SteganographyDetector()
            statistical_results = statistical_detector.analyze(image_path)
            
            # CNN Analysis (if model is available)
            cnn_confidence = None
            cnn_prediction = None
            try:
                cnn_detector = StegoNetCNN()
                # Load pre-trained model if exists
                if os.path.exists('models/best_stego_detector.h5'):
                    cnn_detector.load_model('models/best_stego_detector.h5')
                    cnn_confidence, cnn_prediction = cnn_detector.predict(image_path)
            except Exception as e:
                print(f"CNN analysis failed: {e}")
            
            # Combine results
            final_confidence = statistical_results['confidence_score']
            if cnn_confidence is not None:
                # Weighted average: 60% CNN, 40% statistical
                final_confidence = (cnn_confidence * 0.6) + (statistical_results['confidence_score'] * 0.4)
            
            is_suspicious = final_confidence > 0.7
            
            # Calculate estimated payload
            rs_result = statistical_results.get('rs_analysis', {})
            estimated_payload_pct = rs_result.get('estimated_message_length', 0)
            image_size_bytes = uploaded_image.width * uploaded_image.height * 3  # RGB
            estimated_payload_bytes = image_size_bytes * estimated_payload_pct
            
            # Create Analysis Result
            analysis_result = AnalysisResult.objects.create(
                image=uploaded_image,
                is_suspicious=is_suspicious,
                confidence_score=final_confidence,
                lsb_score=self._calculate_lsb_score(statistical_results['lsb_analysis']),
                chi_square_score=statistical_results['chi_square_analysis']['probability'],
                rs_score=rs_result.get('estimated_message_length', 0),
                frequency_score=statistical_results['frequency_analysis']['frequency_domain_score'],
                metadata_score=self._calculate_metadata_score(statistical_results['metadata_analysis']),
                cnn_confidence=cnn_confidence,
                cnn_prediction=cnn_prediction,
                lsb_details=statistical_results['lsb_analysis'],
                chi_square_details=statistical_results['chi_square_analysis'],
                rs_details=rs_result,
                frequency_details=statistical_results['frequency_analysis'],
                metadata_details=statistical_results['metadata_analysis'],
                estimated_payload_size=estimated_payload_bytes,
                estimated_payload_percentage=estimated_payload_pct * 100
            )
            
            # Create detection history entries
            for method, score in {
                'LSB': analysis_result.lsb_score,
                'Chi-Square': analysis_result.chi_square_score,
                'RS Analysis': analysis_result.rs_score,
                'Frequency': analysis_result.frequency_score,
                'CNN': cnn_confidence if cnn_confidence else 0
            }.items():
                DetectionHistory.objects.create(
                    image=uploaded_image,
                    method_used=method,
                    detected=score > 0.5,
                    confidence=score
                )
            
            # Update status
            uploaded_image.status = 'completed'
            uploaded_image.analyzed_at = timezone.now()
            uploaded_image.save()
            
            analysis_time = time.time() - start_time
            print(f"Analysis completed in {analysis_time:.2f}s")
            
        except Exception as e:
            uploaded_image.status = 'failed'
            uploaded_image.save()
            print(f"Analysis failed: {e}")
            raise
    
    def _calculate_lsb_score(self, lsb_analysis):
        """Calculate overall LSB score"""
        scores = [
            lsb_analysis.get('lsb_pattern_score', 0),
            lsb_analysis.get('bit_plane_complexity', 0),
            lsb_analysis.get('histogram_anomaly', 0),
            lsb_analysis.get('noise_variance', 0)
        ]
        return sum(scores) / len(scores)
    
    def _calculate_metadata_score(self, metadata_analysis):
        """Calculate metadata suspicion score"""
        score = 0.0
        if metadata_analysis.get('suspicious_comments', False):
            score += 0.5
        if metadata_analysis.get('exif_anomalies', 0) > 0:
            score += 0.3
        if metadata_analysis.get('file_size_ratio', 0) > 1.5:
            score += 0.2
        return min(1.0, score)
    
    @action(detail=True, methods=['get'])
    def result(self, request, pk=None):
        """
        Get analysis result for an image
        """
        uploaded_image = self.get_object()
        
        if uploaded_image.status != 'completed':
            return Response({
                'status': uploaded_image.status,
                'message': 'Analysis not yet completed'
            })
        
        try:
            result = uploaded_image.result
            serializer = AnalysisResultSerializer(result)
            return Response(serializer.data)
        except AnalysisResult.DoesNotExist:
            return Response(
                {'error': 'Analysis result not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def feedback(self, request, pk=None):
        """
        Submit user feedback on analysis result
        """
        uploaded_image = self.get_object()
        
        user_confirmed = request.data.get('confirmed')
        user_feedback = request.data.get('feedback', '')
        
        if user_confirmed is None:
            return Response(
                {'error': 'confirmed field is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update detection history with feedback
        DetectionHistory.objects.filter(image=uploaded_image).update(
            user_confirmed=user_confirmed,
            user_feedback=user_feedback
        )
        
        return Response({'status': 'feedback recorded'})
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Get overall detection statistics
        """
        total_images = UploadedImage.objects.filter(status='completed').count()
        suspicious_count = AnalysisResult.objects.filter(is_suspicious=True).count()
        
        if total_images > 0:
            suspicious_percentage = (suspicious_count / total_images) * 100
        else:
            suspicious_percentage = 0
        
        # Average confidence scores
        avg_scores = AnalysisResult.objects.aggregate(
            avg_confidence=models.Avg('confidence_score'),
            avg_lsb=models.Avg('lsb_score'),
            avg_chi=models.Avg('chi_square_score'),
            avg_rs=models.Avg('rs_score')
        )
        
        # Detection method performance
        method_stats = {}
        for method in ['LSB', 'Chi-Square', 'RS Analysis', 'Frequency', 'CNN']:
            history = DetectionHistory.objects.filter(method_used=method)
            if history.exists():
                method_stats[method] = {
                    'total': history.count(),
                    'detected': history.filter(detected=True).count(),
                    'avg_confidence': history.aggregate(
                        avg=models.Avg('confidence')
                    )['avg'] or 0
                }
        
        return Response({
            'total_analyzed': total_images,
            'suspicious_count': suspicious_count,
            'suspicious_percentage': suspicious_percentage,
            'average_scores': avg_scores,
            'method_statistics': method_stats
        })


class TechniqueViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for known steganography techniques
    """
    queryset = SteganographyTechnique.objects.all()
    serializer_class = SteganographyTechniqueSerializer
    permission_classes = [AllowAny]


class HistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for detection history
    """
    queryset = DetectionHistory.objects.all()
    serializer_class = DetectionHistorySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter by authenticated user's images"""
        if self.request.user.is_authenticated:
            return DetectionHistory.objects.filter(
                image__user=self.request.user
            )
        return DetectionHistory.objects.none()


# Import models for statistics
from django.db import models
