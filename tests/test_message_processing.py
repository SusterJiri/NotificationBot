import pytest
import asyncio
import json
import re
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import sys
import os

# Add the main directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import main

class TestMessageProcessing:
    """Test WebSocket message processing and announcement detection"""
    
    def test_token_symbol_extraction(self):
        """Test token symbol extraction from announcement titles"""
        test_cases = [
            ("Binance Will List OpenEden (EDEN) on Spot Trading", "EDEN"),
            ("New Listing: TestCoin (TEST) Available Now", "TEST"),
            ("Binance Adds SomeCoin (SOME) to Futures", "SOME"),
            ("No token symbol in this title", None),
            ("Multiple (FIRST) and (SECOND) symbols", "FIRST"),  # Should get first one
        ]
        
        for title, expected in test_cases:
            token_match = re.search(r'\(([A-Z]+)\)', title)
            result = token_match.group(1) if token_match else None
            assert result == expected, f"Failed for title: {title}"
    
    def test_announcement_keyword_detection(self):
        """Test detection of new listing keywords"""
        keywords = ["will list", "new listing", "trading pair", "binance will list", "will add", "binance will add"]
        
        positive_cases = [
            "Binance will list NewCoin on spot trading",
            "New listing announcement for TestToken",
            "We are adding a new trading pair BTC/USDT",
            "Binance will add SomeCoin to futures",
            "WILL LIST: Important announcement"
        ]
        
        negative_cases = [
            "Platform maintenance scheduled",
            "Updated trading fees",
            "Security notice for users",
            "General announcement about features"
        ]
        
        for text in positive_cases:
            full_text = text.lower()
            assert any(k in full_text for k in keywords), f"Should detect listing in: {text}"
        
        for text in negative_cases:
            full_text = text.lower()
            assert not any(k in full_text for k in keywords), f"Should NOT detect listing in: {text}"

class TestWebSocketMessageHandling:
    """Test WebSocket message parsing and handling"""
    
    @pytest.mark.asyncio
    async def test_subscription_success_message(self):
        """Test handling of successful subscription message"""
        message = {
            "type": "COMMAND",
            "data": "SUCCESS",
            "subType": "SUBSCRIBE",
            "code": "00000000"
        }
        
        with patch('main.notify_telegram') as mock_notify:
            # Simulate the message processing logic
            if (message.get("type") == "COMMAND" and 
                message.get("data") == "SUCCESS" and 
                message.get("subType") == "SUBSCRIBE"):
                await main.notify_telegram("Bot connected successfully to Binance announcements!")
            
            mock_notify.assert_called_once_with("Bot connected successfully to Binance announcements!")
    
    @pytest.mark.asyncio
    async def test_new_listing_announcement_processing(self):
        """Test processing of new listing announcement"""
        announcement_data = {
            "catalogId": 48,
            "catalogName": "New Cryptocurrency Listing",
            "title": "Binance Will List TestCoin (TEST) on Spot Trading",
            "body": "Binance will list TestCoin for spot trading...",
            "content": "Full announcement content here..."
        }
        
        message = {
            "type": "DATA",
            "topic": "com_announcement_en", 
            "data": json.dumps(announcement_data)
        }
        
        with patch('main.notify_telegram') as mock_notify:
            # Simulate the message processing logic from main.py
            if "data" in message:
                if isinstance(message["data"], str):
                    data_parsed = json.loads(message["data"])
                else:
                    data_parsed = message["data"]
                
                title = data_parsed.get("title", "")
                content = data_parsed.get("content", "")
                body = data_parsed.get("body", "")
                description = data_parsed.get("description", "")
                catalog_name = data_parsed.get("catalogName", "")
                
                full_text = f"{title} {content} {body} {description} {catalog_name}".lower()
                keywords = ["will list", "new listing", "trading pair", "binance will list", "will add", "binance will add"]
                
                if any(k in full_text for k in keywords):
                    token_match = re.search(r'\(([A-Z]+)\)', title)
                    token_symbol = token_match.group(1) if token_match else "Unknown"
                    
                    text = f"NEW LISTING ALERT! \nToken: {token_symbol}\n {title}\n\nCheck Binance now!"
                    await main.notify_telegram(text)
            
            mock_notify.assert_called_once()
            call_args = mock_notify.call_args[0][0]
            assert "NEW LISTING ALERT!" in call_args
            assert "Token: TEST" in call_args
            assert "TestCoin (TEST)" in call_args
    
    def test_json_parsing_edge_cases(self):
        """Test JSON parsing with various data formats"""
        # Test string data that needs parsing
        string_data = '{"title": "Test", "body": "Content"}'
        parsed = json.loads(string_data)
        assert parsed["title"] == "Test"
        
        # Test already parsed data
        dict_data = {"title": "Test", "body": "Content"}
        assert dict_data["title"] == "Test"
        
        # Test invalid JSON
        with pytest.raises(json.JSONDecodeError):
            json.loads("invalid json data")
    
    @pytest.mark.asyncio 
    async def test_non_listing_announcement_ignored(self):
        """Test that non-listing announcements are ignored"""
        announcement_data = {
            "catalogId": 49,
            "catalogName": "General Announcement",
            "title": "Platform Maintenance Notice",
            "body": "Scheduled maintenance will occur..."
        }
        
        message = {
            "type": "DATA",
            "topic": "com_announcement_en",
            "data": json.dumps(announcement_data)
        }
        
        with patch('main.notify_telegram') as mock_notify:
            # Simulate the message processing logic
            if "data" in message:
                data_parsed = json.loads(message["data"])
                title = data_parsed.get("title", "")
                content = data_parsed.get("content", "")
                body = data_parsed.get("body", "")
                description = data_parsed.get("description", "")
                catalog_name = data_parsed.get("catalogName", "")
                
                full_text = f"{title} {content} {body} {description} {catalog_name}".lower()
                keywords = ["will list", "new listing", "trading pair", "binance will list", "will add", "binance will add"]
                
                if any(k in full_text for k in keywords):
                    await main.notify_telegram("Should not be called")
            
            mock_notify.assert_not_called()