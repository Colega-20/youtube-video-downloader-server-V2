# gunicorn_config.py
import multiprocessing

# ============================================
# RED Y BINDING
# ============================================
bind = "127.0.0.1:5012"
backlog = 2048

# ============================================
# WORKERS Y THREADS
# ============================================
workers = 2 # nucleos del procesador
worker_class = "sync"
threads = 2 #hilos

# ============================================
# TIMEOUTS
# ============================================
# timeout = 300      # 5 minutos para descargas largas
# graceful_timeout = 30
# keepalive = 5

# ============================================
# LOGGING
# ============================================
accesslog = "-"    # stdout
errorlog = "-"     # stdout
loglevel = "info"  # debug, info, warning, error, critical

# ============================================
# PROCESO
# ============================================
daemon = True
pidfile = "gunicorn.pid"
umask = 0o022
tmp_upload_dir = None

# ============================================
# SEGURIDAD
# ============================================
limit_request_line = 8192
limit_request_fields = 100
limit_request_field_size = 8190

# ============================================
# PERFORMANCE (opcional pero recomendado)
# ============================================
preload_app = True            # Carga app antes de fork (ahorra RAM)
# max_requests = 1000         # Reiniciar worker cada 1000 requests
# max_requests_jitter = 50    # Aleatorizar reinicios