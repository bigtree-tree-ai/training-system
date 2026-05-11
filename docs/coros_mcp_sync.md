# COROS MCP Daily Sync

## Commands

```bash
python -m training.cli coros-login
python -m training.cli coros-sync 14
python -m training.cli coros-overview
```

`coros-login` stores OAuth credentials in `.coros_auth.json`, which is ignored by Git. Daily jobs use the refresh token from that file and do not require repeated login.

## Daily Cron

```cron
15 5 * * * cd /opt/training-system && /usr/bin/python3 -m training.cli coros-sync 14 >> logs/coros-sync.log 2>&1
```

The sync writes structured data into these groups:

- Training: fitness assessment, training load, upcoming schedule.
- Daily life: steps, calories, non-workout activity, stress summary.
- Health recovery: recovery percentage, sleep, HRV, resting heart rate, average heart rate.
- Planning and devices: user profile, bound COROS devices, sync runs.
