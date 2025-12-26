wsgi_app = "masterfilter.wsgi:application"
bind = "0.0.0.0:8000"
workers = 4
errorlog = "/opt/masterfilter/gunicorn-error.log"
accesslog = "/opt/masterfilter/gunicorn-access.log"
loglevel = "debug"
reload = True
accesslog = errorlog = "/var/log/gunicorn/dev.log"
capture_output = True
pidfile = "/var/run/gunicorn/dev.pid"
daemon = True
