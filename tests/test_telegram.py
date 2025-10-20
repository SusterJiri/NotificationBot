import pytest
import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock
import sys
import os

# Add the main directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import main

class TestTelegramIntegration:
    """Test Telegram bot integration"""
    
    @patch.dict(os.environ, {
        'TELEGRAM_BOT_TOKEN': '123456789:TEST_BOT_TOKEN',
        'TELEGRAM_CHAT_ID': '123456789'
    })
    @patch('main.requests.post')
    @pytest.mark.asyncio
    async def test_notify_telegram_success(self, mock_post):
        """Test successful Telegram notification"""
        # Reload main to pick up env vars
        import importlib
        importlib.reload(main)
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        await main.notify_telegram("Test message")
        
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[1]['data']['chat_id'] == '123456789'
        assert call_args[1]['data']['text'] == 'Test message'
        assert 'bot123456789:TEST_BOT_TOKEN' in call_args[0][0]
    
    @patch.dict(os.environ, {
        'TELEGRAM_BOT_TOKEN': '123456789:TEST_BOT_TOKEN',
        'TELEGRAM_CHAT_ID': '123456789'
    })
    @patch('main.requests.post')
    @pytest.mark.asyncio
    async def test_notify_telegram_api_error(self, mock_post):
        """Test Telegram API error handling"""
        import importlib
        importlib.reload(main)
        
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_post.return_value = mock_response
        
        # Should not raise exception, just log error
        await main.notify_telegram("Test message")
        
        mock_post.assert_called_once()
    
    @patch.dict(os.environ, {
        'TELEGRAM_BOT_TOKEN': '',
        'TELEGRAM_CHAT_ID': ''
    }, clear=False)
    @pytest.mark.asyncio
    async def test_notify_telegram_missing_config(self):
        """Test behavior when Telegram config is missing"""
        import importlib
        importlib.reload(main)
        
        # Should return early without making any requests
        with patch('main.requests.post') as mock_post:
            await main.notify_telegram("Test message")
            mock_post.assert_not_called()
    
    @patch.dict(os.environ, {
        'TELEGRAM_BOT_TOKEN': '123456789:TEST_BOT_TOKEN',
        'TELEGRAM_CHAT_ID': '123456789'
    })
    @patch('main.requests.post')
    @pytest.mark.asyncio
    async def test_notify_telegram_network_error(self, mock_post):
        """Test network error handling"""
        import importlib
        importlib.reload(main)
        
        mock_post.side_effect = Exception("Network error")
        
        # Should not raise exception, just log error
        await main.notify_telegram("Test message")
        
        mock_post.assert_called_once()