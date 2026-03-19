# Manual Data Updates
We have some manual data updates that we need to handle, including our QBO report, which 
the user will want to see updated quickly in the app.

## General Operations
* We collect CSV files in an offline data warehouse
* From the files that warehouse, we create a data graph json file
* From the warehouse, we push the generated graph to staging or production servers.

## Updates
* We can update the csv files from Stripe and DonorBox automatically on a schedule, and then update the graph and sync.
* However, we cannot automatically download Benevity reports, so they will be manually updated.
* We may not be able to download our QBO report CSV with automation
* Important: In the normal workflow, the bookkeeper will use our app to make additions and corrections to sales receipts
in QBO. They will want to see their changes in the app in short order.

## Workflow 1
* User manually downloads some CSV reports to a shared location accessible to the warehouse
* The warehouse learns by polling or something more modern that files have been updated
* The warehouse updates the graph and syncs the data.


## Google Drive
The best solution for users would be to use Google Drive, as part of Google for Workplace (Non-Profits)

In order of preference, the warehouse could run on:
1. A raspberry pi without a desktop manager
2. A raspberry pi with Gnome Desktop Manager
3. A Mac with Google Drive Finder extension

Case 1 might require use of the Google API, or new Goole Office CLI, and an involved setup process on Google.
Case 2 might require unwelcome setup and resource use for Gnome.
Case 3 probably works fine, but might not behave exactly like a local file system.

## Questions
### Some options for detecting new data
1. Record and compare the latest last-modified date of all the files in the warehouse.  Probably easiest if the
last-modified date is reliable on Google Drive.
2. Record a manifest of all the files used to generate the graph, with checksums of their contents.

It probably makes sense to record these data directly in the generated graph. Then the semantics become simply: "Are
there any files newer than the graph?"

## Scheduled Refresh with systemd (Raspberry Pi)

Two files are needed: a service unit (what to run) and a timer unit (when to run it).

### Service unit: `/etc/systemd/system/donorpipe-refresh.service`

```ini
[Unit]
Description=DonorPipe warehouse refresh
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
User=pi
WorkingDirectory=/home/pi/donorpipe
ExecStart=/home/pi/donorpipe/warehouse/refresh.sh
# PATH must include uv and python3
Environment=PATH=/home/pi/.local/bin:/usr/local/bin:/usr/bin:/bin
StandardOutput=journal
StandardError=journal
```

Adjust `User=` and `WorkingDirectory=` to match the installation path on the Pi.
`uv` installs to `~/.local/bin` by default; confirm with `which uv` on the Pi and update `PATH` if needed.

### Timer unit: `/etc/systemd/system/donorpipe-refresh.timer`

```ini
[Unit]
Description=Run DonorPipe warehouse refresh on a schedule

[Timer]
OnCalendar=*:0/15
RandomizedDelaySec=60
Persistent=true

[Install]
WantedBy=timers.target
```

`OnCalendar=*:0/15` runs every 15 minutes. Change to `*:0/30` for every 30 minutes.
`RandomizedDelaySec=60` staggers the start by up to 60 seconds.
`Persistent=true` means if the Pi was off, it runs once when it comes back up.

### Enable and start

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now donorpipe-refresh.timer

# Verify the timer is active
systemctl list-timers donorpipe-refresh.timer
```

### Trigger a manual run

```bash
sudo systemctl start donorpipe-refresh.service
```

Useful when the bookkeeper uploads a new file and doesn't want to wait for the next scheduled run.

### Check logs

```bash
journalctl -u donorpipe-refresh.service        # all recent runs
journalctl -u donorpipe-refresh.service -f     # follow live
journalctl -u donorpipe-refresh.service -n 50  # last run only
```

### The command

The service calls `warehouse/refresh.sh` with no arguments — it reads `config.json` from the
working directory. To use a specific config path:

```ini
ExecStart=/home/pi/donorpipe/warehouse/refresh.sh --config /home/pi/donorpipe/config.json
```

With change detection in place, most runs will print "No changes detected. Skipping rebuild
and sync." and exit in a second or two. A full rebuild only runs when files have actually changed.
