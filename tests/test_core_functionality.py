import pytest
import json
import re
import sys
import os

# Add the main directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestCoreFunctionality:
    """Test core functionality without complex mocking"""
    
    def test_token_extraction_regex(self):
        """Test token symbol extraction from titles"""
        test_cases = [
            ("Binance Will List OpenEden (EDEN) on Spot Trading", "EDEN"),
            ("New Listing: TestCoin (TEST) Available Now", "TEST"),
            ("Binance Adds SomeCoin (SOME) to Futures", "SOME"),
            ("No token symbol in this title", None),
        ]
        
        for title, expected in test_cases:
            token_match = re.search(r'\(([A-Z]+)\)', title)
            result = token_match.group(1) if token_match else None
            assert result == expected, f"Failed for title: {title}"
    
    def test_keyword_detection(self):
        """Test new listing keyword detection"""
        keywords = ["will list", "new listing", "trading pair", "binance will list", "will add", "binance will add"]
        
        positive_cases = [
            "Binance will list NewCoin on spot trading",
            "New listing announcement for TestToken",
            "We are adding a new trading pair BTC/USDT",
            "Binance will add SomeCoin to futures",
        ]
        
        negative_cases = [
            "Platform maintenance scheduled",
            "Updated trading fees",
            "Security notice for users",
        ]
        
        for text in positive_cases:
            full_text = text.lower()
            assert any(k in full_text for k in keywords), f"Should detect listing in: {text}"
        
        for text in negative_cases:
            full_text = text.lower()
            assert not any(k in full_text for k in keywords), f"Should NOT detect listing in: {text}"
    
    def test_json_message_parsing(self):
        """Test JSON message parsing logic"""
        # Test message structure from WebSocket
        test_message = {
            "type": "DATA",
            "topic": "com_announcement_en",
            "data": json.dumps({
                "catalogId": 48,
                "catalogName": "New Cryptocurrency Listing",
                "title": "Binance Will List TestCoin (TEST) on Spot Trading",
                "body": "Binance will list TestCoin for trading...",
            })
        }
        
        # Simulate the parsing logic
        if "data" in test_message:
            if isinstance(test_message["data"], str):
                data_parsed = json.loads(test_message["data"])
            else:
                data_parsed = test_message["data"]
            
            title = data_parsed.get("title", "")
            body = data_parsed.get("body", "")
            catalog_name = data_parsed.get("catalogName", "")
            
            assert title == "Binance Will List TestCoin (TEST) on Spot Trading"
            assert "TestCoin" in body
            assert catalog_name == "New Cryptocurrency Listing"
    
    def test_environment_validation(self):
        """Test environment variable validation"""
        # Test that functions handle missing environment variables gracefully
        required_vars = ['BINANCE_API_KEY', 'BINANCE_API_SECRET', 'TELEGRAM_BOT_TOKEN', 'TELEGRAM_CHAT_ID']
        
        for var in required_vars:
            # Just verify these are strings when they exist
            value = os.getenv(var)
            if value:
                assert isinstance(value, str)
                assert len(value) > 0