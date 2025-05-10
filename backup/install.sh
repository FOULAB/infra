#!/bin/bash
set -ex

# TODO: switch to gpgsm once https://gitlab.com/duplicity/duplicity/-/commit/8dc698a38a119c12b3160a076959a834cd701e01 is released
sudo apt install gpg
# Private key is on eigma's personal machine at home, password protected.
sudo gpg --import eigma.gpg

# https://serverfault.com/a/1010716/213110
echo -e "5\ny\n" | sudo gpg --command-fd 0 --edit-key eigma@foulab.org trust

# 3.0.5.dev5
# TODO: switch to apt package once our needed features are released
sudo apt install snapd
sudo snap install duplicity --revision=566 --edge --classic

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
