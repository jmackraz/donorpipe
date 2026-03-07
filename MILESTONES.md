# Milestone Plan for DonorPipe

## Overview
All steps should be implemented in line with the memorized plan.

The first milestone will help us set up some durable test data files.  All further milestones can
use these files for their automated tests.

Completed milestones (1–11) have been moved to [docs/COMPLETED_MILESTONES.md](docs/COMPLETED_MILESTONES.md).

## Active Milestones

### Milestone 13: Public Deployment (AWS Lightsail)

**Goal:** Make the app publicly accessible over HTTPS to a small audience.

**Platform:** AWS Lightsail (existing instance), ~$10/month (2GB RAM).
Domain name already owned.

**Architecture:** Identical to M12 — same Docker Compose setup — with two additions:
1. nginx config gains TLS (port 443) via Let's Encrypt certificate
2. Port 80 redirects to 443

**HTTPS approach:**
- Certbot obtains a free Let's Encrypt certificate proving domain ownership
- Certificate files mounted into the nginx container as a volume
- Certbot renewal cron job runs on the host and reloads nginx on renewal:
  `docker compose exec nginx nginx -s reload`
- No load balancer, no ACM, no additional AWS cost for TLS

**AWS bill of materials (~$10/month total):**
- Lightsail instance (2GB/1vCPU/60GB): $10/month
- Static IP (attached to running instance): free
- TLS certificate (Let's Encrypt): free
- Data transfer (3TB/month included): free
- Lightsail DNS zone: free
- Domain name: already owned

**Reproducibility:**
- Lightsail instance provisioning documented as a CloudFormation template or
  launch script covering: instance creation, Docker install, repo clone, initial Certbot run
- `scripts/deploy.sh` used for all subsequent deploys (same as M12)

**Done when:**
- App reachable at `https://yourdomain.com`
- TLS certificate valid; HTTP redirects to HTTPS
- Auth (M11) works end-to-end over HTTPS
- `scripts/deploy.sh` deploys an update from developer laptop in one command
- CloudFormation template or `scripts/provision.sh` can provision a fresh instance from scratch
- `GET /health` returns 200

**Modified files from M12:**
- `nginx/nginx.conf` — add port 443, TLS cert paths, HTTP→HTTPS redirect
- `src/donorpipe/api/app.py` — update CORS allowed origins to include production domain
- New: CloudFormation template or `scripts/provision.sh`


# Backlog
* ops manual
  * include CMS
  * ops scripts (dev, stage, prod) from CLAUDE.md
  * include arch overview
  * include dev/stage/prod push processes
  * keep updated, occasionally validate
* baby CI/CD just to make pushes easier for me?
* Add notice about proprietary data
* Logging, alarms
* tune keyboard shortcuts, document
* CMS system
  * REST interface for uploading (sanity checks?)
  * Separate engine for automated downloading
  * Trigger reload
  * Works well for dev iterations
* Canonical relationship topology with highlighting
* Realistic fake data
* Merge in csvstore
* test mobile form factor
* Filter out cash donations when appropriate