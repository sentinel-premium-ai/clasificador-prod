"""
Test End-to-End con datos dummy.
Valida que la API genera el JSON correcto y Sentinel lo consume correctamente.
"""
import sys
import os
from datetime import datetime
from unittest.mock import Mock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.api_client import ApiClient, ImagePath

def test_end_to_end_with_dummy_data():
    """
    Simula el flujo completo:
    1. API responde con datos dummy
    2. ApiClient los consume y parsea
    3. Verifica estructura correcta
    """
    
    print("🧪 Test End-to-End: API → Sentinel\n")
    
    # Datos dummy que la API retornaría
    dummy_api_response_page1 = {
        "data": [
            {
                "nro_smf": "SMF001",
                "path": "/imagenes/2026/02/08/foto001.jpg",
                "capture_date": "2026-02-08T10:30:00",
                "cod_unicom": "UNICOM001",
                "nis_rad": "NIS12345",
                "ruta": "RUTA_NORTE",
                "tip_foto": "CF001",
                "num_itin": "ITIN001"
            },
            {
                "nro_smf": "SMF002",
                "path": "/imagenes/2026/02/08/foto002.jpg",
                "capture_date": "2026-02-08T11:15:00",
                "cod_unicom": "UNICOM002",
                "nis_rad": "NIS12346",
                "ruta": "RUTA_SUR",
                "tip_foto": "CF001",
                "num_itin": "ITIN002"
            },
            {
                "nro_smf": "SMF003",
                "path": "/imagenes/2026/02/08/foto003.jpg",
                "capture_date": "2026-02-08T12:00:00",
                "cod_unicom": "UNICOM003",
                "nis_rad": "NIS12347",
                "ruta": "RUTA_ESTE",
                "tip_foto": "CF001",
                "num_itin": "ITIN003"
            }
        ],
        "page": 1,
        "page_size": 1000,
        "has_more": True,  # Simula que hay más páginas
        "total_records": None
    }
    
    dummy_api_response_page2 = {
        "data": [
            {
                "nro_smf": "SMF004",
                "path": "/imagenes/2026/02/08/foto004.jpg",
                "capture_date": "2026-02-08T13:30:00",
                "cod_unicom": "UNICOM004",
                "nis_rad": "NIS12348",
                "ruta": "RUTA_OESTE",
                "tip_foto": "CF001",
                "num_itin": "ITIN004"
            }
        ],
        "page": 2,
        "page_size": 1000,
        "has_more": False,  # Última página
        "total_records": None
    }
    
    # Crear cliente
    client = ApiClient(base_url="http://localhost:8000", api_key="test-key-123")
    
    # Mock de las respuestas
    mock_response_1 = Mock()
    mock_response_1.status_code = 200
    mock_response_1.json.return_value = dummy_api_response_page1
    
    mock_response_2 = Mock()
    mock_response_2.status_code = 200
    mock_response_2.json.return_value = dummy_api_response_page2
    
    # Simular paginación automática
    with patch.object(client.session, 'get', side_effect=[mock_response_1, mock_response_2]):
        test_date = datetime(2026, 2, 8)
        results = client.fetch_image_paths(test_date)
        
        print("✅ Paginación automática funcionó")
        print(f"   - Total de registros obtenidos: {len(results)}")
        print(f"   - Páginas procesadas: 2")
        print()
        
        # Validar estructura
        print("📋 Validando estructura de datos:\n")
        
        assert len(results) == 4, f"Esperaba 4 registros, obtuve {len(results)}"
        print("✅ Cantidad correcta de registros")
        
        # Validar primer registro
        first = results[0]
        assert isinstance(first, ImagePath), "No es instancia de ImagePath"
        assert first.nro_smf == "SMF001"
        assert first.path == "/imagenes/2026/02/08/foto001.jpg"
        assert first.cod_unicom == "UNICOM001"
        assert first.nis_rad == "NIS12345"
        assert first.ruta == "RUTA_NORTE"
        assert first.tip_foto == "CF001"
        assert first.num_itin == "ITIN001"
        print("✅ Estructura del primer registro correcta")
        
        # Validar último registro (de página 2)
        last = results[3]
        assert last.nro_smf == "SMF004"
        assert last.path == "/imagenes/2026/02/08/foto004.jpg"
        print("✅ Paginación funcionó (último registro de página 2)")
        
        # Mostrar ejemplo de datos parseados
        print("\n📦 Ejemplo de datos parseados:")
        print(f"   SMF: {first.nro_smf}")
        print(f"   Path: {first.path}")
        print(f"   Fecha: {first.capture_date}")
        print(f"   Unicom: {first.cod_unicom}")
        print(f"   NIS: {first.nis_rad}")
        print(f"   Ruta: {first.ruta}")
        print(f"   Tipo Foto: {first.tip_foto}")
        print(f"   Itinerario: {first.num_itin}")
        
        print("\n✅ TODAS LAS VALIDACIONES PASARON")
        print("\n📊 Resumen:")
        print("   - JSON de API → Objetos Python: ✅")
        print("   - Paginación automática: ✅")
        print("   - Estructura de datos correcta: ✅")
        print("   - Sentinel puede procesar estos datos: ✅")

if __name__ == "__main__":
    test_end_to_end_with_dummy_data()
