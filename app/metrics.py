from threading import Lock
from collections import defaultdict

class MetricsRegistry:
    def __init__(self):
        self._lock = Lock()
        self.http_requests_total = defaultdict(int)
        self.webhook_requests_total = defaultdict(int)
        # Latency buckets for simplicity: "100", "500", "+Inf"
        self.request_latency_ms_bucket = defaultdict(int)
        self.request_latency_ms_count = 0
        self.request_latency_ms_sum = 0.0

    def inc_http_request(self, path: str, status: str):
        with self._lock:
            self.http_requests_total[(path, status)] += 1

    def inc_webhook_request(self, result: str):
        with self._lock:
            self.webhook_requests_total[result] += 1

    def observe_latency(self, latency_ms: float):
        with self._lock:
            self.request_latency_ms_count += 1
            self.request_latency_ms_sum += latency_ms
            if latency_ms <= 100:
                self.request_latency_ms_bucket["100"] += 1
                self.request_latency_ms_bucket["500"] += 1
                self.request_latency_ms_bucket["+Inf"] += 1
            elif latency_ms <= 500:
                self.request_latency_ms_bucket["500"] += 1
                self.request_latency_ms_bucket["+Inf"] += 1
            else:
                self.request_latency_ms_bucket["+Inf"] += 1

    def generate_output(self) -> str:
        lines = []
        with self._lock:
            # http_requests_total
            lines.append("# HELP http_requests_total Total HTTP requests")
            lines.append("# TYPE http_requests_total counter")
            for (path, status), count in self.http_requests_total.items():
                lines.append(f'http_requests_total{{path="{path}",status="{status}"}} {count}')
            
            # webhook_requests_total
            lines.append("# HELP webhook_requests_total Webhook processing outcomes")
            lines.append("# TYPE webhook_requests_total counter")
            for result, count in self.webhook_requests_total.items():
                lines.append(f'webhook_requests_total{{result="{result}"}} {count}')
                
            # request_latency_ms
            lines.append("# HELP request_latency_ms_bucket Request latency in milliseconds")
            lines.append("# TYPE request_latency_ms_bucket histogram")
            for le in ["100", "500", "+Inf"]:
                lines.append(f'request_latency_ms_bucket{{le="{le}"}} {self.request_latency_ms_bucket[le]}')
            lines.append(f'request_latency_ms_count {self.request_latency_ms_count}')
            lines.append(f'request_latency_ms_sum {self.request_latency_ms_sum}')
            
        return "\n".join(lines) + "\n"

metrics = MetricsRegistry()
