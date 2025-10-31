"""
Telegram Service
================

Handles all Telegram bot communication and message formatting.
"""

import os
import logging
from typing import Optional
import asyncio
from datetime import datetime

from ..models import PriceData, TradingSignal, Prediction, BacktestResult

logger = logging.getLogger(__name__)


class TelegramService:
    """Service for sending trading signals and updates via Telegram."""
    
    def __init__(self):
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        self.enabled = bool(self.bot_token and self.chat_id)
        
        if not self.enabled:
            logger.warning("Telegram not configured - bot_token or chat_id missing")
        else:
            logger.info("Telegram service initialized")
    
    def is_enabled(self) -> bool:
        """Check if Telegram service is properly configured."""
        return self.enabled
    
    async def send_message(self, message: str) -> bool:
        """Send a message to Telegram."""
        if not self.enabled:
            logger.debug(f"Telegram disabled - would send: {message}")
            return False
        
        try:
            import requests
            
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            data = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            
            response = requests.post(url, data=data, timeout=10)
            response.raise_for_status()
            
            logger.info("Telegram message sent successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False
    
    def format_trading_signal(self, signal: TradingSignal, prediction: Prediction, 
                            current_price: float) -> str:
        """Format trading signal for Telegram."""
        emoji_map = {
            'BUY': '🟢',
            'SELL': '🔴',
            'HOLD': '🟡'
        }
        
        signal_emoji = emoji_map.get(signal.action, '⚪')
        
        message = f"""
{signal_emoji} <b>{signal.asset_symbol} Trading Signal</b>

<b>Action:</b> {signal.action}
<b>Current Price:</b> ${current_price:.2f}
<b>Predicted Price:</b> ${prediction.predicted_price:.2f}
<b>Price Change:</b> {prediction.price_change:+.2f}%
<b>Confidence:</b> {prediction.confidence:.1f}%

<b>Signal Strength:</b> {self._get_strength_indicator(prediction.confidence)}

<b>Analysis:</b>
• Price trend: {self._get_trend_description(prediction.price_change)}
• Model confidence: {self._get_confidence_description(prediction.confidence)}
• Signal triggered: {signal.reason}

<b>Timestamp:</b> {signal.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
        """.strip()
        
        return message
    
    def format_price_update(self, asset_symbol: str, price_data: PriceData) -> str:
        """Format price update for Telegram."""
        price_change_24h = price_data.price_change_24h or 0.0
        market_cap = price_data.market_cap or 0.0
        change_emoji = "📈" if price_change_24h >= 0 else "📉"
        
        message = f"""
{change_emoji} <b>{asset_symbol} Price Update</b>

<b>Current Price:</b> ${price_data.price:.2f}
<b>24h Change:</b> {price_change_24h:+.2f}%
<b>24h Volume:</b> ${price_data.volume:,.0f}
<b>Market Cap:</b> ${market_cap:,.0f}

<b>Timestamp:</b> {price_data.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
        """.strip()
        
        return message
    
    def format_backtest_results(self, asset_symbol: str, results: BacktestResult) -> str:
        """Format backtesting results for Telegram."""
        performance_emoji = "🎯" if results.total_return > 0 else "❌"
        
        message = f"""
{performance_emoji} <b>{asset_symbol} Backtest Results</b>

<b>Performance:</b>
• Total Return: {results.total_return:+.2f}%
• Sharpe Ratio: {results.sharpe_ratio:.2f}
• Max Drawdown: {results.max_drawdown:.2f}%
• Win Rate: {results.win_rate:.1f}%

<b>Trading Activity:</b>
• Total Trades: {results.total_trades}
• Winning Trades: {int(results.total_trades * results.win_rate / 100)}
• Average Trade: {results.total_return / max(results.total_trades, 1):.2f}%

<b>Period:</b> {results.start_date.strftime('%Y-%m-%d')} to {results.end_date.strftime('%Y-%m-%d')}
        """.strip()
        
        return message
    
    def format_system_status(self, status: dict) -> str:
        """Format system status for Telegram."""
        status_emoji = "✅" if status.get('healthy', False) else "⚠️"
        
        message = f"""
{status_emoji} <b>System Status Update</b>

<b>Overall Health:</b> {'Healthy' if status.get('healthy', False) else 'Issues Detected'}
<b>Active Assets:</b> {status.get('active_assets', 0)}
<b>Data Freshness:</b> {status.get('data_age', 'Unknown')}
<b>API Status:</b> {status.get('api_status', 'Unknown')}

<b>Last Update:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """.strip()
        
        return message
    
    def format_error_alert(self, error_type: str, error_message: str, asset: Optional[str] = None) -> str:
        """Format error alert for Telegram."""
        asset_info = f" ({asset})" if asset else ""
        
        message = f"""
🚨 <b>System Error Alert{asset_info}</b>

<b>Error Type:</b> {error_type}
<b>Message:</b> {error_message}
<b>Timestamp:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Please check system logs for details.
        """.strip()
        
        return message
    
    def _get_strength_indicator(self, confidence: float) -> str:
        """Get signal strength indicator based on confidence."""
        if confidence >= 90:
            return "🔥 Very Strong"
        elif confidence >= 80:
            return "💪 Strong"
        elif confidence >= 70:
            return "👍 Moderate"
        elif confidence >= 60:
            return "🤏 Weak"
        else:
            return "❓ Very Weak"
    
    def _get_trend_description(self, price_change: float) -> str:
        """Get trend description based on price change."""
        if abs(price_change) < 0.5:
            return "Sideways movement"
        elif price_change > 2:
            return "Strong bullish"
        elif price_change > 0:
            return "Bullish"
        elif price_change < -2:
            return "Strong bearish"
        else:
            return "Bearish"
    
    def _get_confidence_description(self, confidence: float) -> str:
        """Get confidence level description."""
        if confidence >= 85:
            return "Very high confidence"
        elif confidence >= 75:
            return "High confidence"
        elif confidence >= 65:
            return "Moderate confidence"
        elif confidence >= 55:
            return "Low confidence"
        else:
            return "Very low confidence"
    
    async def send_trading_signal(self, signal: TradingSignal, prediction: Prediction, 
                                current_price: float) -> bool:
        """Send a trading signal message."""
        message = self.format_trading_signal(signal, prediction, current_price)
        return await self.send_message(message)
    
    async def send_price_update(self, asset_symbol: str, price_data: PriceData) -> bool:
        """Send a price update message."""
        message = self.format_price_update(asset_symbol, price_data)
        return await self.send_message(message)
    
    async def send_backtest_results(self, asset_symbol: str, results: BacktestResult) -> bool:
        """Send backtest results message."""
        message = self.format_backtest_results(asset_symbol, results)
        return await self.send_message(message)
    
    async def send_system_status(self, status: dict) -> bool:
        """Send system status message."""
        message = self.format_system_status(status)
        return await self.send_message(message)
    
    async def send_error_alert(self, error_type: str, error_message: str, 
                             asset: Optional[str] = None) -> bool:
        """Send error alert message."""
        message = self.format_error_alert(error_type, error_message, asset)
        return await self.send_message(message)