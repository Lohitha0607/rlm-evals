## Description
`/app/access_log.sh` prints yesterday's web server access log, one request per line:

```
2026-11-02T14:05:09Z GET /api/orders 500 312ms
```

The fields are: timestamp (UTC), method, path, status code, duration.

## Requirements
- Count the requests with status code `500` whose timestamp is between `14:00:00` and `14:59:59` (inclusive).
- Write only the count, as a number, to `/app/answer.txt`.
- Do not modify `/app/access_log.sh`.

## Interface
`/app/answer.txt`: a single line containing an integer.
