import pytest
import asyncio
import json
import time
from unittest.mock import Mock, patch, AsyncMock
import sys
import os

# Add the main directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import main

class TestBinanceAPI:
    """Test Binance API integration"""
    
    @patch('main.requests.get')
    def test_get_binance_server_time_success(self, mock_get):
        """Test successful server time retrieval"""
        mock_response = Mock()
        mock_response.json.return_value = {"serverTime": 1634567890123}
        mock_get.return_value = mock_response
        
        result = main.get_binance_server_time()
        
        assert result == 1634567890123
        mock_get.assert_called_once_with("https://api.binance.com/api/v3/time", timeout=5)
    
    @patch('main.requests.get')
    @patch('main.time.time')
    def test_get_binance_server_time_failure_fallback(self, mock_time, mock_get):
        """Test fallback to local time when server time fails"""
        mock_get.side_effect = Exception("Connection failed")
        mock_time.return_value = 1634567890.123
        
        result = main.get_binance_server_time()
        
        assert result == 1634567890123  # Local time * 1000
    
    def test_generate_random_string(self):
        """Test random string generation"""
        result = main.generate_random_string(16)
        
        assert len(result) == 16
        assert result.islower()
        assert result.isalnum()
        
        # Test different lengths
        assert len(main.generate_random_string(32)) == 32
        assert len(main.generate_random_string(8)) == 8
    
    def test_create_signed_url(self):
        """Test WebSocket URL creation with signature"""
        # Test the function directly without complex mocking
        with patch.dict(os.environ, {
            'BINANCE_API_SECRET': 'test_secret_key_123456789',
            'BINANCE_API_KEY': 'test_api_key_123456789'
        }):
            import importlib
            importlib.reload(main)
            
            result = main.create_signed_url()
            
            assert "wss://api.binance.com/sapi/wss" in result
            assert "topic=com_announcement_en" in result
            assert "signature=" in result
            assert "timestamp=" in result
            assert "random=" in result
            assert "recvWindow=30000" in result
    
    def test_create_signed_url_missing_secret(self):
        """Test error when API secret is missing"""
        with patch.dict(os.environ, {'BINANCE_API_SECRET': ''}, clear=True):
            import importlib
            importlib.reload(main)
            
            with pytest.raises(RuntimeError, match="BINANCE_API_SECRET missing"):
                main.create_signed_url()