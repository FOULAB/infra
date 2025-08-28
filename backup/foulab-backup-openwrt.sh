#!/bin/sh
{
  CONFIG="--user wifi.lab:$(cat /usr/local/etc/backup-password)"
  DATE="$(TZ=UTC date +%Y%m%dT%H%M%SZ)"

  for HOST in backup.foulab.org:8084 foulab-backup.nanobit.org:8084; do
    sysupgrade -o -b - | openssl smime -encrypt -binary -aes256 -stream -outform DER /usr/local/etc/eigma@foulab.org.pem | curl -i -K <(echo "${CONFIG}") -T - http://${HOST}/webdav/wifi.lab/sysupgrade-full.${DATE}.tar.gz.p7m

    for MTD in /dev/mtd[0-9] /dev/mtd[0-9][0-9]; do
      cat "${MTD}"
    done | openssl smime -encrypt -binary -aes256 -stream -outform DER /usr/local/etc/eigma@foulab.org.pem | curl -i -K <(echo "${CONFIG}") -T - http://${HOST}/webdav/wifi.lab/mtd-full.${DATE}.img.p7m
  done
} 2>&1 | logger -t foulab-backup-openwrt.sh
