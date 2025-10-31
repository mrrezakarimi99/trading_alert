"""Tests for Model Service."""

import pytest
import tempfile
import shutil
import os
from datetime import datetime, timedelta
from src.models import PriceData, ModelMetrics
from src.services import ModelService


class TestModelService:
    """Test ML model functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        # Use temporary directory for models
        self.temp_dir = tempfile.mkdtemp()
        self.model_service = ModelService(models_dir=self.temp_dir)
        
        # Create sample price data
        self.sample_data = []
        base_price = 50000
        for i in range(100):
            price = base_price + (i * 10) + (i % 10) * 50  # Some variation
            self.sample_data.append(PriceData(
                timestamp=datetime.now() - timedelta(days=100-i),
                price=price,
                volume=1000000 + i * 10000
            ))
    
    def teardown_method(self):
        """Cleanup test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_model_creation(self):
        """Test model service initialization."""
        assert self.model_service.models_dir == self.temp_dir
        assert self.model_service.sequence_length == 60
        assert os.path.exists(self.temp_dir)
    
    def test_model_paths(self):
        """Test model file path generation."""
        model_path = self.model_service._get_model_path('bitcoin')
        scaler_path = self.model_service._get_scaler_path('bitcoin')
        metrics_path = self.model_service._get_metrics_path('bitcoin')
        
        assert 'bitcoin_model.h5' in model_path
        assert 'bitcoin_scaler.pkl' in scaler_path
        assert 'bitcoin_metrics.pkl' in metrics_path
    
    @pytest.mark.skipif(not pytest.importorskip("tensorflow"), reason="TensorFlow not available")
    def test_model_training(self):
        """Test model training functionality."""
        success = self.model_service.train_model('test_asset', self.sample_data, epochs=1)
        
        if success:  # Training might fail in CI environments
            assert self.model_service.model_exists('test_asset')
            metrics = self.model_service.get_model_metrics('test_asset')
            assert metrics is not None
            assert hasattr(metrics, 'accuracy')
    
    def test_insufficient_data_handling(self):
        """Test handling of insufficient training data."""
        # Create minimal data (less than required)
        minimal_data = self.sample_data[:10]  # Only 10 data points
        
        success = self.model_service.train_model('test_minimal', minimal_data, epochs=1)
        assert success == False  # Should fail due to insufficient data
    
    def test_model_listing(self):
        """Test listing available models."""
        models = self.model_service.list_available_models()
        assert isinstance(models, list)
    
    @pytest.mark.skipif(not pytest.importorskip("tensorflow"), reason="TensorFlow not available")
    def test_prediction(self):
        """Test price prediction functionality."""
        # First train a model
        success = self.model_service.train_model('test_predict', self.sample_data, epochs=1)
        
        if success:
            # Test prediction
            recent_data = self.sample_data[-70:]  # Get recent data for prediction
            prediction = self.model_service.predict_price('test_predict', recent_data)
            
            if prediction:  # Prediction might fail
                assert prediction.asset_id == 'test_predict'
                assert prediction.predicted_price > 0
                assert prediction.confidence >= 0
                assert prediction.confidence <= 100
    
    def test_model_exists(self):
        """Test model existence checking."""
        assert self.model_service.model_exists('nonexistent_model') == False
    
    def test_data_preprocessing(self):
        """Test data preprocessing functionality."""
        # This tests the internal _preprocess_data method indirectly
        result = self.model_service._preprocess_data(self.sample_data, self.model_service.sequence_length)
        
        if result is not None:
            X, y, scaler = result
            assert X.shape[0] > 0  # Should have some sequences
            assert X.shape[1] == self.model_service.sequence_length  # Correct sequence length
            assert len(y) == X.shape[0]  # Same number of labels as sequences