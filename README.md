# OpsWatch

A small, dependency-free Python CLI that does three things a DevOps support analyst does every day:

1. **Analyse logs**: level counts, noisiest services, most frequent errors (with IPs/IDs/numbers normalised so similar errors group together), and per-minute error spike detection with a suggested priority (P1-P4).
2. **Health-check services**: HTTP URLs or `host:port` TCP targets, with latency. Exit code is non-zero on failure, so it works in scripts and cron.
3. **Write ticket notes**: turns a log analysis into a consistent markdown note that always includes the ticket number.

## Quick start

```bash
git clone <your-repo-url> && cd opswatch
python -m opswatch analyze sample/app.log
python -m opswatch analyze sample/app.log --json
python -m opswatch check https://example.com 127.0.0.1:5432
python -m opswatch ticket sample/app.log --ticket INC12345 --summary "Payments timing out"
```

Or install it: `pip install .` then run `opswatch --help`.

### Docker

```bash
docker build -t opswatch .
docker run --rm -v "$PWD/sample:/data" opswatch analyze /data/app.log
```

## Log format

```
2026-10-05 09:12:01 ERROR payment-api Timeout connecting to db-primary 10.0.4.12:5432
```

Lines that don't match are counted as "unparseable" rather than crashing the run.

## Tests and CI

```bash
python -m unittest discover -s tests -v
```

GitHub Actions runs the tests and a CLI smoke test on Python 3.10 and 3.12 for every push and PR.

## Ideas to extend it (good talking points in interviews)

- Add a `--since 30m` filter and support for JSON-structured logs
- Push the `check` results to Prometheus (Pushgateway) or post alerts to Teams/Slack
- Add a `runbook` command that maps known error patterns to documented fixes
- Package as a container and run on a schedule with a GitHub Actions cron or Kubernetes CronJob

## Why this project

It shows practical skills for a DevOps support analyst role: log triage, incident prioritisation, service monitoring, clear ticket documentation, tests, CI and containerisation, using only the standard library.
