import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '10s', target: 5 },
    { duration: '20s', target: 10 },
    { duration: '10s', target: 0 },
  ],
  thresholds: {
    http_req_failed: ['rate<0.01'],
    http_req_duration: ['p(95)<800'],
  },
};

export default function () {
  const url = __ENV.HALO_HEALTH_URL || 'https://staging.example/api/health';
  const res = http.get(url);
  check(res, { 'status is 200': (r) => r.status === 200 });
  sleep(1);
}
