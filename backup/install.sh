#!/bin/bash
set -ex

sudo apt install gpgsm
# Private key is on eigma's personal machine at home, password protected.
# gpgsm --export --armor 0x22D4E07B > eigma@foulab.org.pem
sudo gpgsm --import eigma@foulab.org.pem

# https://gnupg-users.gnupg.narkive.com/NuUU1DOL/tutorial-for-gpgsm#post2
sudo mkdir -p /root/.gnupg
echo '57:E2:BB:72:5C:99:13:E0:4C:92:FA:C6:34:3B:7A:E0:22:D4:E0:7B' | sudo tee /root/.gnupg/trustlist.txt

# 3.0.5.dev8
# TODO: switch to apt package once our needed features are released
sudo apt install snapd
sudo snap install duplicity --revision=593 --edge --classic

sudo install -d /usr/local/etc
sudo install -m 0600 duplicity-password /usr/local/etc
sudo install -m 0644 duplicity-multi.json /usr/local/etc

sudo install -d /usr/local/etc/systemd/system
sudo install -m 0644 duplicity-daily.service duplicity-daily.timer duplicity-monthly.service duplicity-monthly.timer /usr/local/etc/systemd/system

sudo systemctl enable \
  /usr/local/etc/systemd/system/duplicity-daily.service \
  /usr/local/etc/systemd/system/duplicity-daily.timer \
  /usr/local/etc/systemd/system/duplicity-monthly.service \
  /usr/local/etc/systemd/system/duplicity-monthly.timer

sudo systemctl start duplicity-daily.timer duplicity-monthly.timer

cat <<'EOF' >&2
  create a htpasswd account on bahamut.lab and update /usr/local/etc/duplicity-password

  P=$(pwgen 10 1)
  echo $P | sudo htpasswd -i /etc/nginx/foulab-backups-htpasswd example.lab
  sudo install -d -g www-data -m 2775 /srv/dev-disk-by-id-wwn-0x6848f690ea02b0002d5d2b875414ebb8-part1/shared/BACKUPS/automated/example.lab
  echo "password: $P"
EOF
