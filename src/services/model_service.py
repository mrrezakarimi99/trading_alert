"""
Model Service
=============

Handles LSTM model creation, training, prediction and model persistence.
"""

import os
import logging
import numpy as np
import pandas as pd
from typing import Tuple, Optional, List, Dict
from datetime import datetime, timedelta
import joblib
from dataclasses import asdict

from ..models import PriceData, Prediction, ModelMetrics

logger = logging.getLogger(__name__)


class ModelService:
    """Service for managing LSTM models and predictions."""
    
    def __init__(self, models_dir: str = "models"):
        self.models_dir = models_dir
        self.models: Dict[str, any] = {}  # Store loaded models
        self.scalers: Dict[str, any] = {}  # Store scalers for each asset
        self.sequence_length = 60  # Days of historical data for prediction
        
        # Create models directory
        os.makedirs(self.models_dir, exist_ok=True)
        
        # Lazy import to avoid loading TensorFlow unless needed
        self._tf = None
        self._keras = None
    
    def _import_tf(self):
        """Lazy import TensorFlow and Keras."""
        if self._tf is None:
            try:
                import tensorflow as tf
                from tensorflow import keras
                from sklearn.preprocessing import MinMaxScaler
                from sklearn.metrics import mean_absolute_error, mean_squared_error
                
                self._tf = tf
                self._keras = keras
                self._scaler_class = MinMaxScaler
                self._mae = mean_absolute_error
                self._mse = mean_squared_error
                
                # Set TensorFlow to use CPU only to avoid GPU setup issues
                tf.config.set_visible_devices([], 'GPU')
                
                logger.info("TensorFlow imported successfully")
                
            except ImportError as e:
                logger.error(f"Failed to import TensorFlow: {e}")
                raise ImportError("TensorFlow is required for model operations")
    
    def _get_model_path(self, asset_id: str) -> str:
        """Get model file path for an asset."""
        return os.path.join(self.models_dir, f"{asset_id}_model.h5")
    
    def _get_scaler_path(self, asset_id: str) -> str:
        """Get scaler file path for an asset."""
        return os.path.join(self.models_dir, f"{asset_id}_scaler.pkl")
    
    def _get_metrics_path(self, asset_id: str) -> str:
        """Get metrics file path for an asset."""
        return os.path.join(self.models_dir, f"{asset_id}_metrics.pkl")
    
    def _prepare_data(self, price_data: List[PriceData]) -> Tuple[np.ndarray, np.ndarray, any]:
        """Prepare price data for model training."""
        self._import_tf()
        
        # Convert to DataFrame
        df = pd.DataFrame([asdict(data) for data in price_data])
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')
        
        # Use closing price for training
        prices = df['price'].values.reshape(-1, 1)
        
        # Scale the data
        scaler = self._scaler_class(feature_range=(0, 1))
        scaled_prices = scaler.fit_transform(prices)
        
        # Create sequences for LSTM
        X, y = [], []
        for i in range(self.sequence_length, len(scaled_prices)):
            X.append(scaled_prices[i-self.sequence_length:i, 0])
            y.append(scaled_prices[i, 0])
        
        return np.array(X), np.array(y), scaler
    
    def _create_lstm_model(self, input_shape: Tuple[int, int]) -> any:
        """Create LSTM model architecture."""
        self._import_tf()
        
        model = self._keras.Sequential([
            self._keras.layers.LSTM(50, return_sequences=True, input_shape=input_shape),
            self._keras.layers.Dropout(0.2),
            self._keras.layers.LSTM(50, return_sequences=True),
            self._keras.layers.Dropout(0.2),
            self._keras.layers.LSTM(50),
            self._keras.layers.Dropout(0.2),
            self._keras.layers.Dense(1)
        ])
        
        model.compile(optimizer='adam', loss='mean_squared_error')
        return model
    
    def train_model(self, asset_id: str, price_data: List[PriceData], 
                   epochs: int = 50, batch_size: int = 32) -> bool:
        """Train LSTM model for an asset."""
        try:
            self._import_tf()
            
            if len(price_data) < self.sequence_length + 10:
                logger.error(f"Insufficient data for {asset_id}: {len(price_data)} points")
                return False
            
            logger.info(f"Training model for {asset_id} with {len(price_data)} data points")
            
            # Prepare data
            X, y, scaler = self._prepare_data(price_data)
            
            if len(X) == 0:
                logger.error(f"No training sequences created for {asset_id}")
                return False
            
            # Reshape for LSTM
            X = X.reshape(X.shape[0], X.shape[1], 1)
            
            # Create model
            model = self._create_lstm_model((X.shape[1], 1))
            
            # Train model
            history = model.fit(
                X, y,
                epochs=epochs,
                batch_size=batch_size,
                validation_split=0.2,
                verbose=0,
                shuffle=False
            )
            
            # Calculate metrics
            predictions = model.predict(X, verbose=0)
            
            # Inverse transform for metrics calculation
            y_actual = scaler.inverse_transform(y.reshape(-1, 1))
            y_pred = scaler.inverse_transform(predictions)
            
            mae = self._mae(y_actual, y_pred)
            mse = self._mse(y_actual, y_pred)
            rmse = np.sqrt(mse)
            
            # Calculate accuracy (within 5% tolerance)
            tolerance = 0.05
            accurate_predictions = np.abs((y_pred - y_actual) / y_actual) <= tolerance
            accuracy = np.mean(accurate_predictions) * 100
            
            metrics = ModelMetrics(
                asset_id=asset_id,
                mae=float(mae),
                mse=float(mse),
                rmse=float(rmse),
                accuracy=float(accuracy),
                training_loss=float(history.history['loss'][-1]),
                validation_loss=float(history.history['val_loss'][-1]),
                trained_at=datetime.now()
            )
            
            # Save model, scaler, and metrics
            model.save(self._get_model_path(asset_id))
            joblib.dump(scaler, self._get_scaler_path(asset_id))
            joblib.dump(metrics, self._get_metrics_path(asset_id))
            
            # Store in memory
            self.models[asset_id] = model
            self.scalers[asset_id] = scaler
            
            logger.info(f"Model trained for {asset_id} - Accuracy: {accuracy:.2f}%, RMSE: {rmse:.2f}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to train model for {asset_id}: {e}")
            return False
    
    def load_model(self, asset_id: str) -> bool:
        """Load trained model and scaler for an asset."""
        try:
            self._import_tf()
            
            model_path = self._get_model_path(asset_id)
            scaler_path = self._get_scaler_path(asset_id)
            
            if not os.path.exists(model_path) or not os.path.exists(scaler_path):
                logger.warning(f"Model files not found for {asset_id}")
                return False
            
            model = self._keras.models.load_model(model_path)
            scaler = joblib.load(scaler_path)
            
            self.models[asset_id] = model
            self.scalers[asset_id] = scaler
            
            logger.info(f"Model loaded for {asset_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load model for {asset_id}: {e}")
            return False
    
    def predict_price(self, asset_id: str, recent_prices: List[float]) -> Optional[Prediction]:
        """Make price prediction for an asset."""
        try:
            # Try to use ML model first
            if asset_id not in self.models:
                if not self.load_model(asset_id):
                    logger.warning(f"No ML model available for {asset_id}, using technical analysis fallback")
                    return self._simple_technical_prediction(asset_id, recent_prices)
            
            if len(recent_prices) < self.sequence_length:
                logger.error(f"Insufficient recent prices for prediction: {len(recent_prices)}")
                return None
            
            model = self.models[asset_id]
            scaler = self.scalers[asset_id]
            
            # Prepare input data
            input_prices = np.array(recent_prices[-self.sequence_length:]).reshape(-1, 1)
            scaled_input = scaler.transform(input_prices)
            
            # Reshape for prediction
            X = scaled_input.reshape(1, self.sequence_length, 1)
            
            # Make prediction
            scaled_prediction = model.predict(X, verbose=0)
            predicted_price = scaler.inverse_transform(scaled_prediction)[0][0]
            
            # Calculate price change percentage
            current_price = recent_prices[-1]
            price_change = ((predicted_price - current_price) / current_price) * 100
            
            # Calculate confidence based on model performance
            metrics = self.get_model_metrics(asset_id)
            base_confidence = metrics.accuracy if metrics else 70.0
            
            # Adjust confidence based on price change magnitude
            if abs(price_change) > 10:
                confidence = base_confidence * 0.7  # Reduce confidence for extreme predictions
            elif abs(price_change) > 5:
                confidence = base_confidence * 0.85
            else:
                confidence = base_confidence
            
            confidence = max(50.0, min(95.0, confidence))  # Clamp between 50-95%
            
            return Prediction(
                asset_id=asset_id,
                predicted_price=float(predicted_price),
                current_price=current_price,
                price_change=float(price_change),
                confidence=float(confidence),
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Failed to predict price for {asset_id}: {e}")
            return None
    
    def get_model_metrics(self, asset_id: str) -> Optional[ModelMetrics]:
        """Get model performance metrics."""
        try:
            metrics_path = self._get_metrics_path(asset_id)
            if os.path.exists(metrics_path):
                return joblib.load(metrics_path)
            return None
        except Exception as e:
            logger.error(f"Failed to load metrics for {asset_id}: {e}")
            return None
    
    def model_exists(self, asset_id: str) -> bool:
        """Check if trained model exists for an asset."""
        model_path = self._get_model_path(asset_id)
        scaler_path = self._get_scaler_path(asset_id)
        return os.path.exists(model_path) and os.path.exists(scaler_path)
    
    def delete_model(self, asset_id: str) -> bool:
        """Delete model files for an asset."""
        try:
            model_path = self._get_model_path(asset_id)
            scaler_path = self._get_scaler_path(asset_id)
            metrics_path = self._get_metrics_path(asset_id)
            
            for path in [model_path, scaler_path, metrics_path]:
                if os.path.exists(path):
                    os.remove(path)
            
            # Remove from memory
            self.models.pop(asset_id, None)
            self.scalers.pop(asset_id, None)
            
            logger.info(f"Model deleted for {asset_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete model for {asset_id}: {e}")
            return False
    
    def list_available_models(self) -> List[str]:
        """List all available trained models."""
        models = []
        for file in os.listdir(self.models_dir):
            if file.endswith('_model.h5'):
                asset_id = file.replace('_model.h5', '')
                if self.model_exists(asset_id):
                    models.append(asset_id)
        return models
    
    def validate_model(self, asset_id: str, test_data: List[PriceData]) -> Optional[Dict]:
        """Validate model performance on test data."""
        try:
            if not self.load_model(asset_id):
                return None
            
            if len(test_data) < self.sequence_length + 1:
                logger.error(f"Insufficient test data for {asset_id}")
                return None
            
            model = self.models[asset_id]
            scaler = self.scalers[asset_id]
            
            # Prepare test data
            X, y, _ = self._prepare_data(test_data)
            X = X.reshape(X.shape[0], X.shape[1], 1)
            
            # Make predictions
            predictions = model.predict(X, verbose=0)
            
            # Inverse transform
            y_actual = scaler.inverse_transform(y.reshape(-1, 1))
            y_pred = scaler.inverse_transform(predictions)
            
            # Calculate metrics
            mae = self._mae(y_actual, y_pred)
            mse = self._mse(y_actual, y_pred)
            rmse = np.sqrt(mse)
            
            # Calculate accuracy
            tolerance = 0.05
            accurate_predictions = np.abs((y_pred - y_actual) / y_actual) <= tolerance
            accuracy = np.mean(accurate_predictions) * 100
            
            return {
                'mae': float(mae),
                'mse': float(mse),
                'rmse': float(rmse),
                'accuracy': float(accuracy),
                'predictions': len(predictions),
                'validated_at': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Failed to validate model for {asset_id}: {e}")
            return None
    
    def _simple_technical_prediction(self, asset_id: str, recent_prices: List[float]) -> Optional[Prediction]:
        """Generate prediction using simple technical analysis when no ML model is available."""
        try:
            if len(recent_prices) < 20:
                logger.error(f"Insufficient price data for technical prediction: {len(recent_prices)}")
                return None
            
            current_price = recent_prices[-1]
            
            # Calculate moving averages
            ma_5 = np.mean(recent_prices[-5:])
            ma_10 = np.mean(recent_prices[-10:])
            ma_20 = np.mean(recent_prices[-20:])
            
            # Calculate price momentum
            momentum_5 = (current_price - recent_prices[-6]) / recent_prices[-6] * 100 if len(recent_prices) > 5 else 0
            momentum_10 = (current_price - recent_prices[-11]) / recent_prices[-11] * 100 if len(recent_prices) > 10 else 0
            
            # Simple trend analysis
            short_trend = ma_5 - ma_10  # Short-term trend
            long_trend = ma_10 - ma_20  # Long-term trend
            
            # Generate prediction based on trends and momentum
            prediction_factor = 0
            confidence = 60.0  # Base confidence for technical analysis
            
            # Trend-based prediction
            if short_trend > 0 and long_trend > 0:
                # Bullish trend
                prediction_factor = 0.02 + (momentum_5 * 0.001)  # 2% base + momentum
                confidence += 10
            elif short_trend < 0 and long_trend < 0:
                # Bearish trend  
                prediction_factor = -0.02 + (momentum_5 * 0.001)  # -2% base + momentum
                confidence += 10
            else:
                # Mixed signals
                prediction_factor = momentum_10 * 0.001  # Rely on longer momentum
                confidence -= 5
            
            # Apply volatility adjustment
            volatility = np.std(recent_prices[-10:]) / np.mean(recent_prices[-10:])
            if volatility > 0.05:  # High volatility
                confidence -= 15
                prediction_factor *= 0.7  # Reduce prediction magnitude
            
            # Calculate predicted price
            predicted_price = current_price * (1 + prediction_factor)
            price_change = (predicted_price - current_price) / current_price * 100
            
            # Clamp confidence between 50-75% for technical analysis
            confidence = max(50.0, min(75.0, confidence))
            
            logger.info(f"Technical prediction for {asset_id}: {price_change:+.2f}% (confidence: {confidence:.1f}%)")
            
            return Prediction(
                asset_id=asset_id,
                predicted_price=float(predicted_price),
                current_price=current_price,
                price_change=float(price_change),
                confidence=float(confidence),
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Failed to generate technical prediction for {asset_id}: {e}")
            return None
    
    def auto_train_model_if_needed(self, asset_id: str, historical_data: List[PriceData], 
                                 min_data_points: int = 100) -> bool:
        """Automatically train a model if none exists and sufficient data is available."""
        try:
            # Check if model already exists
            if self.model_exists(asset_id):
                logger.info(f"Model already exists for {asset_id}")
                return True
            
            # Check if we have enough data
            if len(historical_data) < min_data_points:
                logger.info(f"Insufficient data for auto-training {asset_id}: {len(historical_data)} < {min_data_points}")
                return False
            
            logger.info(f"Auto-training model for {asset_id} with {len(historical_data)} data points...")
            
            # Use reduced epochs for auto-training to save time
            success = self.train_model(asset_id, historical_data, epochs=20, batch_size=16)
            
            if success:
                logger.info(f"✅ Auto-trained model successfully for {asset_id}")
            else:
                logger.warning(f"❌ Auto-training failed for {asset_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to auto-train model for {asset_id}: {e}")
            return False