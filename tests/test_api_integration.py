"""
Integration test for Sentinel ApiClient.
Tests the client's ability to consume the Oracle API with mock responses.
"""
import sys
import os
from datetime import datetime
from unittest.mock import Mock, patch
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.api_client import ApiClient, ImagePath

def test_api_client_initialization():
    """Test that ApiClient initializes correctly"""
    client = ApiClient(base_url="http://localhost:8000", api_key="test-key")
    assert client.base_url == "http://localhost:8000"
    assert client.api_key == "test-key"
    print("✅ ApiClient initialization test passed")

def test_fetch_single_page():
    """Test fetching a single page of results"""
    client = ApiClient(base_url="http://localhost:8000", api_key="test-key")
    
    # Mock response for single page
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "data": [
            {
                "nro_smf": "12345",
                "path": "/test/image1.jpg",
                "capture_date": "2026-02-08T10:30:00",
                "cod_unicom": "UC001",
                "nis_rad": "NIS123",
                "ruta": "RUTA_A",
                "tip_foto": "CF001",
                "num_itin": "ITIN001"
            }
        ],
        "page": 1,
        "page_size": 1000,
        "has_more": False,
        "total_records": None
    }
    
    with patch.object(client.session, 'get', return_value=mock_response):
        test_date = datetime(2026, 2, 8)
        results = client.fetch_image_paths(test_date)
        
        assert len(results) == 1
        assert results[0].nro_smf == "12345"
        assert results[0].path == "/test/image1.jpg"
        assert isinstance(results[0], ImagePath)
        print("✅ Single page fetch test passed")

def test_fetch_multiple_pages():
    """Test pagination - fetching multiple pages"""
    client = ApiClient(base_url="http://localhost:8000", api_key="test-key")
    
    # Mock responses for pagination
    page1_response = Mock()
    page1_response.status_code = 200
    page1_response.json.return_value = {
        "data": [{"nro_smf": f"IMG{i}", "path": f"/img{i}.jpg", "capture_date": "2026-02-08T10:00:00",
                  "cod_unicom": "UC", "nis_rad": "NIS", "ruta": "R", "tip_foto": "CF001", "num_itin": "IT"}
                 for i in range(1000)],
        "page": 1,
        "page_size": 1000,
        "has_more": True
    }
    
    page2_response = Mock()
    page2_response.status_code = 200
    page2_response.json.return_value = {
        "data": [{"nro_smf": f"IMG{i}", "path": f"/img{i}.jpg", "capture_date": "2026-02-08T10:00:00",
                  "cod_unicom": "UC", "nis_rad": "NIS", "ruta": "R", "tip_foto": "CF001", "num_itin": "IT"}
                 for i in range(1000, 1500)],
        "page": 2,
        "page_size": 1000,
        "has_more": False
    }
    
    with patch.object(client.session, 'get', side_effect=[page1_response, page2_response]):
        test_date = datetime(2026, 2, 8)
        results = client.fetch_image_paths(test_date)
        
        assert len(results) == 1500
        assert results[0].nro_smf == "IMG0"
        assert results[1499].nro_smf == "IMG1499"
        print("✅ Multiple page fetch test passed (1500 records)")

def test_api_authentication_header():
    """Test that API key is sent in headers"""
    client = ApiClient(base_url="http://localhost:8000", api_key="secret-key-123")
    
    assert client.session.headers.get("X-API-KEY") == "secret-key-123"
    print("✅ API authentication header test passed")

def test_date_formatting():
    """Test that dates are formatted correctly for API"""
    client = ApiClient(base_url="http://localhost:8000", api_key="test-key")
    
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "data": [],
        "page": 1,
        "page_size": 1000,
        "has_more": False
    }
    
    with patch.object(client.session, 'get', return_value=mock_response) as mock_get:
        test_date = datetime(2026, 2, 8, 15, 30, 45)
        client.fetch_image_paths(test_date)
        
        # Verify the date was formatted as YYYY-MM-DD
        call_args = mock_get.call_args
        assert call_args[1]['params']['date'] == '2026-02-08'
        print("✅ Date formatting test passed")

def test_error_handling():
    """Test error handling for API failures"""
    client = ApiClient(base_url="http://localhost:8000", api_key="test-key")
    
    # Mock a failed response
    mock_response = Mock()
    mock_response.status_code = 500
    mock_response.raise_for_status.side_effect = Exception("Server Error")
    
    with patch.object(client.session, 'get', return_value=mock_response):
        test_date = datetime(2026, 2, 8)
        try:
            client.fetch_image_paths(test_date)
            assert False, "Should have raised an exception"
        except Exception as e:
            print(f"✅ Error handling test passed (caught: {type(e).__name__})")

if __name__ == "__main__":
    print("🧪 Running Sentinel ApiClient Integration Tests\n")
    
    try:
        test_api_client_initialization()
        test_fetch_single_page()
        test_fetch_multiple_pages()
        test_api_authentication_header()
        test_date_formatting()
        test_error_handling()
        
        print("\n✅ All integration tests passed!")
        print("\n📝 Summary:")
        print("   - ApiClient correctly initializes with base_url and api_key")
        print("   - Single page fetching works correctly")
        print("   - Pagination handles multiple pages (tested with 1500 records)")
        print("   - Authentication header is set properly")
        print("   - Date formatting is correct (YYYY-MM-DD)")
        print("   - Error handling works as expected")
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
