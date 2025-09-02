#!/bin/sh
set -ex
{
  DATE="$(TZ=UTC date +%Y%m%dT%H%M%SZ)"

  # For testing, this can be a smaller one, like zroot/var/log
  DATASET=zroot

  if [ "$(date +%d)" = "01" ]; then
    zfs destroy -r ${DATASET}@daily || true
  fi

  zfs destroy -r ${DATASET}@daily-tmp || true
  zfs snapshot -r ${DATASET}@daily-tmp

  if zfs get -t snapshot name ${DATASET}@daily; then
    SEND="-i ${DATASET}@daily"
    TYPE="inc"
  else
    TYPE="full"
  fi

  OK=
  for HOST in backup.foulab.org:8084 foulab-backup.nanobit.org:8084; do
    zfs send -c -R ${SEND} ${DATASET}@daily-tmp | openssl smime -encrypt -binary -aes256 -stream -outform DER /usr/local/etc/eigma@foulab.org.pem | curl --no-progress-meter -i --netrc-file /usr/local/etc/backup.netrc -T - -f http://${HOST}/webdav/cinderblock.lab/zroot-${TYPE}.${DATE}.zfs.p7m && OK=1
  done

  if [ "$OK" ]; then
    zfs destroy -r ${DATASET}@daily || true
    zfs rename -r ${DATASET}@daily-tmp @daily
  fi

  # /conf
  for HOST in backup.foulab.org:8084 foulab-backup.nanobit.org:8084; do
    tar c /conf | openssl smime -encrypt -binary -aes256 -stream -outform DER /usr/local/etc/eigma@foulab.org.pem | curl --no-progress-meter -i --netrc-file /usr/local/etc/backup.netrc -T - -f http://${HOST}/webdav/cinderblock.lab/conf-full.${DATE}.tar.p7m
  done
} 2>&1 | logger -t foulab-backup-opnsense.sh
