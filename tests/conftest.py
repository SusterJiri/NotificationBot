import pytest
import asyncio
import json
import os
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from dotenv import load_dotenv
import sys

# Add the main directory to the path so we can import main.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import main

@pytest.fixture
def mock_env_vars():
    """Mock environment variables for testing"""
    return {
        "BINANCE_API_KEY": "test_api_key_123456789",
        "BINANCE_API_SECRET": "test_api_secret_123456789",
        "TELEGRAM_BOT_TOKEN": "123456789:TEST_BOT_TOKEN",
        "TELEGRAM_CHAT_ID": "123456789"
    }

@pytest.fixture
def mock_config(mock_env_vars):
    """Mock the configuration loading"""
    with patch.dict(os.environ, mock_env_vars):
        # Reload the main module to pick up the mocked env vars
        import importlib
        importlib.reload(main)
        yield main

@pytest.fixture
def sample_announcement_data():
    """Sample announcement data for testing"""
    return {
        "catalogId": 48,
        "catalogName": "New Cryptocurrency Listing", 
        "publishDate": 1759228202485,
        "title": "Binance Will List OpenEden (EDEN) on Earn, Buy Crypto, Convert, Margin & Futures",
        "body": "Binance is excited to announce that OpenEden (EDEN) will be added to Binance Simple Earn..."
    }

@pytest.fixture
def sample_websocket_messages():
    """Sample WebSocket messages for testing"""
    return {
        "subscribe_success": {
            "type": "COMMAND",
            "data": "SUCCESS", 
            "subType": "SUBSCRIBE",
            "code": "00000000"
        },
        "new_listing_announcement": {
            "type": "DATA",
            "topic": "com_announcement_en",
            "data": json.dumps({
                "catalogId": 48,
                "catalogName": "New Cryptocurrency Listing",
                "title": "Binance Will List TestCoin (TEST) on Spot Trading",
                "body": "Binance will list TestCoin (TEST) for spot trading..."
            })
        },
        "regular_announcement": {
            "type": "DATA", 
            "topic": "com_announcement_en",
            "data": json.dumps({
                "catalogId": 49,
                "catalogName": "General Announcement",
                "title": "Platform Maintenance Notice",
                "body": "Scheduled maintenance will occur..."
            })
        }
    }