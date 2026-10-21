#!/bin/bash
set -euo pipefail
exec > >(tee -a /var/log/draftwise-bootstrap.log) 2>&1
for attempt in $(seq 1 12); do dnf install -y docker awscli-2 && break || sleep 10; done
systemctl enable --now docker
systemctl enable --now amazon-ssm-agent
# A separate retained EBS volume keeps database and TLS data across instance replacement.
DISK=/dev/disk/by-id/nvme-Amazon_Elastic_Block_Store_${DataVolumeId}
DISK=$(echo "$DISK" | sed 's/vol-/vol/')
for attempt in $(seq 1 120); do [ -b "$DISK" ] && break || sleep 5; done
[ -b "$DISK" ]
if ! blkid "$DISK"; then mkfs.ext4 "$DISK"; fi
mkdir -p /srv/draftwise
UUID=$(blkid -s UUID -o value "$DISK")
grep -q "$UUID" /etc/fstab || echo "UUID=$UUID /srv/draftwise ext4 defaults,nofail 0 2" >> /etc/fstab
mount /srv/draftwise
mkdir -p /etc/systemd/system/docker.service.d
printf '[Unit]\nRequiresMountsFor=/srv/draftwise\n' > /etc/systemd/system/docker.service.d/draftwise-storage.conf
systemctl daemon-reload
mkdir -p /srv/draftwise/database /srv/draftwise/caddy /srv/draftwise/caddy-config /opt/draftwise
chown 10001:10001 /srv/draftwise/database
# Standard CPU credits avoid unlimited-mode CPU surplus charges.
for attempt in $(seq 1 90); do aws s3 cp s3://${ArtifactBucket}/releases/${ReleaseKey}.tar.gz /opt/draftwise/source.tar.gz --region ${AWS::Region} && break || sleep 10; done
tar -xzf /opt/draftwise/source.tar.gz -C /opt/draftwise
cd /opt/draftwise
printf '%s\n' '${PublicIp}.sslip.io' > /srv/draftwise/domain
bash deploy/run-server.sh '${ReleaseKey}'
