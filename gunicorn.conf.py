bind = "0.0.0.0:8080"
# Single worker: prometheus-client's default in-memory registry is not
# process-shared. Scale via multiple Pods/replicas in Kubernetes instead.
workers = 1
threads = 4
worker_class = "gthread"
timeout = 30
accesslog = "-"
errorlog = "-"
loglevel = "info"
