"""
Trading Service
===============

Handles trading signal generation, backtesting, and trading logic.
"""

import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from dataclasses import asdict

from ..models import (
    AssetConfig, PriceData, Prediction, TradingSignal, 
    BacktestResult, Trade, ModelMetrics
)

logger = logging.getLogger(__name__)


class TradingService:
    """Service for trading signal generation and backtesting."""
    
    def __init__(self):
        self.signal_history: Dict[str, List[TradingSignal]] = {}
        self.trade_history: Dict[str, List[Trade]] = {}
    
    def generate_signal(self, asset_config: AssetConfig, prediction: Prediction, 
                       current_price: PriceData) -> Optional[TradingSignal]:
        """Generate trading signal based on prediction and asset configuration."""
        try:
            # Check confidence threshold
            if prediction.confidence < asset_config.min_confidence:
                return TradingSignal(
                    asset_id=asset_config.id,
                    asset_symbol=asset_config.symbol,
                    action='HOLD',
                    confidence=prediction.confidence,
                    price=current_price.price,
                    reason=f"Low confidence: {prediction.confidence:.1f}% < {asset_config.min_confidence}%",
                    timestamp=datetime.now()
                )
            
            # Check price change threshold
            if abs(prediction.price_change) < asset_config.min_price_change:
                return TradingSignal(
                    asset_id=asset_config.id,
                    asset_symbol=asset_config.symbol,
                    action='HOLD',
                    confidence=prediction.confidence,
                    price=current_price.price,
                    reason=f"Small price change: {prediction.price_change:.2f}% < {asset_config.min_price_change}%",
                    timestamp=datetime.now()
                )
            
            # Generate signal based on price change direction
            if prediction.price_change > 0:
                action = 'BUY'
                reason = f"Predicted {prediction.price_change:.2f}% increase with {prediction.confidence:.1f}% confidence"
            else:
                action = 'SELL'
                reason = f"Predicted {prediction.price_change:.2f}% decrease with {prediction.confidence:.1f}% confidence"
            
            signal = TradingSignal(
                asset_id=asset_config.id,
                asset_symbol=asset_config.symbol,
                action=action,
                confidence=prediction.confidence,
                price=current_price.price,
                reason=reason,
                timestamp=datetime.now()
            )
            
            # Store signal in history
            if asset_config.id not in self.signal_history:
                self.signal_history[asset_config.id] = []
            self.signal_history[asset_config.id].append(signal)
            
            # Keep only last 100 signals per asset
            self.signal_history[asset_config.id] = self.signal_history[asset_config.id][-100:]
            
            return signal
            
        except Exception as e:
            logger.error(f"Failed to generate signal for {asset_config.id}: {e}")
            return None
    
    def should_send_signal(self, asset_id: str, new_signal: TradingSignal, 
                          cooldown_minutes: int = 60) -> bool:
        """Check if signal should be sent based on cooldown and duplicates."""
        if asset_id not in self.signal_history:
            return True
        
        recent_signals = self.signal_history[asset_id]
        if not recent_signals:
            return True
        
        last_signal = recent_signals[-1]
        
        # Check cooldown period
        time_diff = new_signal.timestamp - last_signal.timestamp
        if time_diff.total_seconds() < cooldown_minutes * 60:
            logger.debug(f"Signal for {asset_id} in cooldown period")
            return False
        
        # Check if same signal was recently sent
        if (last_signal.action == new_signal.action and 
            abs(last_signal.confidence - new_signal.confidence) < 5.0):
            logger.debug(f"Similar signal for {asset_id} recently sent")
            return False
        
        return True
    
    def get_signal_history(self, asset_id: str, limit: int = 10) -> List[TradingSignal]:
        """Get recent signal history for an asset."""
        if asset_id not in self.signal_history:
            return []
        return self.signal_history[asset_id][-limit:]
    
    def calculate_portfolio_metrics(self, trades: List[Trade]) -> Dict[str, float]:
        """Calculate portfolio performance metrics."""
        if not trades:
            return {
                'total_return': 0.0,
                'total_trades': 0,
                'win_rate': 0.0,
                'avg_return': 0.0,
                'max_drawdown': 0.0,
                'sharpe_ratio': 0.0
            }
        
        # Calculate returns
        returns = [trade.profit_loss_pct for trade in trades if trade.profit_loss_pct is not None]
        
        if not returns:
            return {
                'total_return': 0.0,
                'total_trades': len(trades),
                'win_rate': 0.0,
                'avg_return': 0.0,
                'max_drawdown': 0.0,
                'sharpe_ratio': 0.0
            }
        
        total_return = np.prod([1 + r/100 for r in returns]) - 1
        win_rate = len([r for r in returns if r > 0]) / len(returns) * 100
        avg_return = np.mean(returns)
        
        # Calculate max drawdown
        cumulative_returns = np.cumprod([1 + r/100 for r in returns])
        running_max = np.maximum.accumulate(cumulative_returns)
        drawdowns = (cumulative_returns - running_max) / running_max
        max_drawdown = abs(np.min(drawdowns)) * 100
        
        # Calculate Sharpe ratio (simplified)
        if np.std(returns) > 0:
            sharpe_ratio = avg_return / np.std(returns)
        else:
            sharpe_ratio = 0.0
        
        return {
            'total_return': total_return * 100,
            'total_trades': len(trades),
            'win_rate': win_rate,
            'avg_return': avg_return,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe_ratio
        }
    
    def backtest_strategy(self, asset_config: AssetConfig, historical_data: List[PriceData],
                         predictions: List[Prediction], initial_balance: float = 10000.0) -> BacktestResult:
        """Backtest trading strategy on historical data."""
        try:
            if len(historical_data) != len(predictions):
                logger.error("Historical data and predictions length mismatch")
                return self._create_empty_backtest_result(asset_config.id, historical_data)
            
            trades = []
            balance = initial_balance
            position = 0.0  # Current position size
            position_price = 0.0  # Price at which position was opened
            
            for i, (price_data, prediction) in enumerate(zip(historical_data, predictions)):
                # Generate signal
                signal = self.generate_signal(asset_config, prediction, price_data)
                if not signal:
                    continue
                
                current_price = price_data.price
                
                # Execute trades based on signal
                if signal.action == 'BUY' and position <= 0:
                    # Close short position if any
                    if position < 0:
                        profit_loss = (position_price - current_price) * abs(position)
                        profit_loss_pct = (profit_loss / balance) * 100
                        balance += profit_loss
                        
                        trades.append(Trade(
                            asset_id=asset_config.id,
                            action='COVER',
                            price=current_price,
                            quantity=abs(position),
                            timestamp=price_data.timestamp,
                            profit_loss=profit_loss,
                            profit_loss_pct=profit_loss_pct
                        ))
                    
                    # Open long position
                    position_size = balance * 0.95  # Use 95% of balance
                    position = position_size / current_price
                    position_price = current_price
                    
                    trades.append(Trade(
                        asset_id=asset_config.id,
                        action='BUY',
                        price=current_price,
                        quantity=position,
                        timestamp=price_data.timestamp
                    ))
                
                elif signal.action == 'SELL' and position >= 0:
                    # Close long position if any
                    if position > 0:
                        profit_loss = (current_price - position_price) * position
                        profit_loss_pct = (profit_loss / balance) * 100
                        balance += profit_loss
                        
                        trades.append(Trade(
                            asset_id=asset_config.id,
                            action='SELL',
                            price=current_price,
                            quantity=position,
                            timestamp=price_data.timestamp,
                            profit_loss=profit_loss,
                            profit_loss_pct=profit_loss_pct
                        ))
                    
                    # Open short position
                    position_size = balance * 0.95
                    position = -(position_size / current_price)
                    position_price = current_price
                    
                    trades.append(Trade(
                        asset_id=asset_config.id,
                        action='SHORT',
                        price=current_price,
                        quantity=abs(position),
                        timestamp=price_data.timestamp
                    ))
            
            # Close any remaining position
            if position != 0 and historical_data:
                final_price = historical_data[-1].price
                if position > 0:
                    profit_loss = (final_price - position_price) * position
                else:
                    profit_loss = (position_price - final_price) * abs(position)
                
                profit_loss_pct = (profit_loss / balance) * 100
                balance += profit_loss
                
                trades.append(Trade(
                    asset_id=asset_config.id,
                    action='CLOSE',
                    price=final_price,
                    quantity=abs(position),
                    timestamp=historical_data[-1].timestamp,
                    profit_loss=profit_loss,
                    profit_loss_pct=profit_loss_pct
                ))
            
            # Calculate metrics
            metrics = self.calculate_portfolio_metrics(trades)
            
            return BacktestResult(
                asset_id=asset_config.id,
                start_date=historical_data[0].timestamp if historical_data else datetime.now(),
                end_date=historical_data[-1].timestamp if historical_data else datetime.now(),
                initial_balance=initial_balance,
                final_balance=balance,
                total_return=metrics['total_return'],
                total_trades=metrics['total_trades'],
                win_rate=metrics['win_rate'],
                max_drawdown=metrics['max_drawdown'],
                sharpe_ratio=metrics['sharpe_ratio'],
                trades=trades
            )
            
        except Exception as e:
            logger.error(f"Backtesting failed for {asset_config.id}: {e}")
            return self._create_empty_backtest_result(asset_config.id, historical_data)
    
    def _create_empty_backtest_result(self, asset_id: str, historical_data: List[PriceData]) -> BacktestResult:
        """Create empty backtest result for error cases."""
        start_date = historical_data[0].timestamp if historical_data else datetime.now()
        end_date = historical_data[-1].timestamp if historical_data else datetime.now()
        
        return BacktestResult(
            asset_id=asset_id,
            start_date=start_date,
            end_date=end_date,
            initial_balance=10000.0,
            final_balance=10000.0,
            total_return=0.0,
            total_trades=0,
            win_rate=0.0,
            max_drawdown=0.0,
            sharpe_ratio=0.0,
            trades=[]
        )
    
    def get_trade_history(self, asset_id: str, limit: int = 50) -> List[Trade]:
        """Get trade history for an asset."""
        if asset_id not in self.trade_history:
            return []
        return self.trade_history[asset_id][-limit:]
    
    def clear_history(self, asset_id: Optional[str] = None):
        """Clear signal and trade history."""
        if asset_id:
            self.signal_history.pop(asset_id, None)
            self.trade_history.pop(asset_id, None)
            logger.info(f"Cleared history for {asset_id}")
        else:
            self.signal_history.clear()
            self.trade_history.clear()
            logger.info("Cleared all trading history")
    
    def get_portfolio_summary(self) -> Dict[str, any]:
        """Get overall portfolio performance summary."""
        all_trades = []
        for trades in self.trade_history.values():
            all_trades.extend(trades)
        
        if not all_trades:
            return {
                'total_assets': 0,
                'total_trades': 0,
                'overall_performance': 0.0,
                'best_performing_asset': None,
                'worst_performing_asset': None
            }
        
        # Calculate per-asset performance
        asset_performance = {}
        for asset_id, trades in self.trade_history.items():
            metrics = self.calculate_portfolio_metrics(trades)
            asset_performance[asset_id] = metrics['total_return']
        
        best_asset = max(asset_performance.items(), key=lambda x: x[1]) if asset_performance else None
        worst_asset = min(asset_performance.items(), key=lambda x: x[1]) if asset_performance else None
        
        overall_metrics = self.calculate_portfolio_metrics(all_trades)
        
        return {
            'total_assets': len(self.trade_history),
            'total_trades': len(all_trades),
            'overall_performance': overall_metrics['total_return'],
            'win_rate': overall_metrics['win_rate'],
            'sharpe_ratio': overall_metrics['sharpe_ratio'],
            'max_drawdown': overall_metrics['max_drawdown'],
            'best_performing_asset': best_asset[0] if best_asset else None,
            'best_performance': best_asset[1] if best_asset else 0.0,
            'worst_performing_asset': worst_asset[0] if worst_asset else None,
            'worst_performance': worst_asset[1] if worst_asset else 0.0,
            'asset_performance': asset_performance
        }