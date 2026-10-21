# AWS deployment

`deploy/ec2-stack.json` provisions the single-instance course MVP in an existing VPC/subnet: Amazon Linux 2023, t3.small (standard CPU credits), 20 GB encrypted root disk, a separate retained 5 GB encrypted data volume, Elastic IP, HTTP/HTTPS security group, private versioned release bucket, and an instance role limited to release downloads plus Systems Manager. SSH is closed. `deploy/bootstrap.sh` is the readable source of the user data embedded in the template; keep them synchronized.

The server builds the committed source archive, imports the reviewed Onetricks observations idempotently, and runs the API/frontend and Caddy containers. SQLite and TLS state live on the data volume at `/srv/draftwise`. A free `<elastic-ip>.sslip.io` hostname provides the demo URL; it depends on that external DNS service. Caddy obtains and renews HTTPS certificates. Local saved drafts are not uploaded.

## Release procedure

1. Authenticate with `aws login --profile draftwise --region us-east-2`. This uses short-lived credentials and avoids permanent access keys.
2. Run CI and archive the tested commit with `git archive --format=tar.gz -o .cache/release.tar.gz HEAD`.
3. Validate the CloudFormation template. Supply ArtifactBucket, ReleaseKey (commit SHA), VpcId, SubnetId, AvailabilityZone, and the current official AL2023 ImageId.
4. Create the stack with `CAPABILITY_IAM`. Once its private bucket exists, upload the archive to `s3://<bucket>/releases/<commit>.tar.gz`. Bootstrap waits up to 15 minutes for the archive.
5. Check CloudFormation, `/var/log/draftwise-bootstrap.log` through SSM, and the public HTTPS health endpoint. Verify saving and loading a draft across container restart.

For a later application release, upload its archive to the same private release prefix. Through an authorized SSM command, download it to `/opt/draftwise/source.tar.gz`, extract into `/opt/draftwise`, and run `bash deploy/run-server.sh <commit>`. The old application remains running during the build. The container replacement causes a short interruption. A previous source archive can be redeployed to roll back; database schema compatibility must be reviewed first. CI runs on GitHub pushes; automatic production deployment is not enabled.

## Operations and costs

Baseline estimate: about $21/month before credits for continuous t3.small compute, one public IPv4, and 25 GB gp3 storage in Ohio, plus S3 requests/storage and any billable traffic. This is an estimate, not a spending cap. Monitor AWS Settings credit balance. Stopping compute leaves disk/IP/storage charges; deleting the stack retains the data volume and release bucket intentionally. Review backups and explicitly remove retained resources only when no longer needed.

The public service has shared limits of 20 analyses/minute, four concurrent analyses, and 30 draft writes/minute. These single-process demo limits return HTTP 429 with Retry-After; they are not a full DDoS protection service. Caddy caps request bodies at 64 KB. Secure, HttpOnly, SameSite cookies scope anonymous saved drafts to the browser. AI explanations use local templates and do not incur model API charges.

Back up SQLite using its backup API, not by copying a live WAL database file. A retained volume survives instance/stack removal but is not an independent backup. A multi-instance deployment requires a shared database and distributed traffic controls.

## Existing local container setup

## Local container rehearsal

Install Docker, then run `docker compose up --build -d app`. Visit http://localhost:8000. SQLite lives in the named `draftwise-data` volume. `docker compose down` preserves it; **do not use `down -v`** unless intentionally discarding data. The Windows Python/Vite preview uses its separate `.data/draftwise.sqlite3` file.

Import reviewed observations inside the running container:

```sh
docker compose exec app python backend/scripts/import_onetricks.py backend/app/data/onetricks_reviewed.json
```

## EC2 steps for a later deployment

1. Provision an Ubuntu EC2 instance with enough memory to build the frontend (start with 2 GB), install Docker Engine and the Compose plugin. Attach persistent EBS storage and keep its delete-on-termination setting appropriate for your backup policy.
2. Clone the private GitHub repository using your account access. Do not bake GitHub credentials into the image.
3. Point a domain's DNS at the instance. Allow inbound HTTPS/HTTP on 443/80 and restrict SSH to your IP. Port 8000 is bound to loopback only.
4. Set `DOMAIN=your-domain.example` and `COOKIE_SECURE=true` in the server's root `.env`; run `docker compose --profile cloud up --build -d`. Caddy obtains the HTTPS certificate. Keep the app and proxy on the same Docker network.
5. Import reviewed observations, then verify health, save/load across a container restart, and all source labels through HTTPS.
6. Back up SQLite with its backup API to a separate durable destination. Copying only the main database file while WAL writes are active can lose data. Restore-test a backup before relying on it.

SQLite supports this single-instance course MVP. Multiple app instances require a shared database such as PostgreSQL and a proper migration plan. Anonymous saved drafts are scoped to an unguessable HttpOnly browser cookie; clearing it loses access. This is not account authentication or cross-device sync. Before public traffic, add abuse controls/rate limits and decide whether account login is needed.

## Continuous integration

`.github/workflows/ci.yml` runs on pushes and pull requests: isolated backend tests, frontend formatting/build, deterministic Playwright flows, Docker build, and save/restart/load persistence smoke test. Tests disable external stats and paid AI. No auto-deploy workflow exists. A green CI run is evidence for the tested commit, not proof that a cloud deployment occurred.
