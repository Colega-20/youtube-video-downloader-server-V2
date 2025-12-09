# waitress_server.py
from waitress import serve
from app import app
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler()  # stdout
    ]
)

if __name__ == '__main__':
    print("🚀 Iniciando Waitress server en http://127.0.0.1:5012")
    
    serve(
        app,
        # RED Y BINDING
        host='127.0.0.1',
        port=5012,
        
        # WORKERS Y THREADS
        threads=4,              # 2 workers * 2 threads = 4 (equivalente a tu config)
        
        # TIMEOUTS
        # channel_timeout=300,    # 5 minutos (equivalente a timeout)
        
        # SEGURIDAD
        url_scheme='http',
        max_request_header_size=8192,     # limit_request_line
        # max_request_body_size=1073741824, # 1GB para videos grandes
        expose_tracebacks = False,           # No mostrar errores al cliente
        
        # PERFORMANCE
        backlog=2048,
        recv_bytes=8192,
        send_bytes=8192,
        
        # LOGGING
        _profile=False,
        _quiet=False,  # Mostrar logs
    )


