#!/usr/bin/python3 -u
"""Checks backups for consistency and completness

Intended to be installed on bahamut.lab in /usr/local/bin, and must be run
in a venv which has package 'mattermostdriver'.
"""
import argparse, duplicity, os, datetime, email.message
import re
import subprocess, mattermostdriver, glob

import gettext
gettext.install("duplicity", names=["ngettext"])
import duplicity.backend
import duplicity.backends.localbackend
import duplicity.config
import duplicity.dup_collections
import duplicity.log
import duplicity.path

HOSTS = [
  'bahamut.lab',
  'foulab.org',
  'manning.lab',
  'test.foulab.org',
]
assert len(HOSTS) == len(set(HOSTS))
assert HOSTS == sorted(HOSTS)

mail = ''

def print_tee(text):
  global mail
  print(text)
  mail += text + '\n'

def check(dir_path):
  got = set(os.listdir(dir_path))
  got.remove('client_temp')

  now = datetime.datetime.now(datetime.UTC)

  for host in HOSTS:
    text = f'- {host}: '
    parsed_url = duplicity.backend.ParsedUrl('file://' + os.path.join(dir_path, host))
    local_backend = duplicity.backends.localbackend.LocalBackend(parsed_url)
    backend = duplicity.backend.BackendWrapper(local_backend)
    col_stats = duplicity.dup_collections.CollectionsStatus(backend, duplicity.config.archive_dir_path).set_values()
    
    chain = col_stats.get_last_backup_chain()
    if not chain:
      text += '❗ No chain'
    else:
      def _set_str(s):
        t = datetime.datetime.fromtimestamp(s.get_time(), tz=datetime.UTC)
        info = backend.query_info(s.volume_name_dict.values())
        size = sum(i['size'] for i in info.values())
        # TODO: size sanity check
        return f'{t.strftime("%b %-d")} ({(now - t).days} days ago, {size / 1024 / 1024 / 1024:.01f} GB)'
      fullset = chain.get_first()
      text += f'Full: {_set_str(fullset)}'
      if datetime.datetime.fromtimestamp(fullset.get_time(), tz=datetime.UTC) < now - datetime.timedelta(days=37):
        text += f' ❗ Older than 37 days'
      lastset = chain.get_last()
      if lastset is not fullset:
        text += f', Incremental: {_set_str(lastset)}'
        if datetime.datetime.fromtimestamp(lastset.get_time(), tz=datetime.UTC) < now - datetime.timedelta(days=3):
          text += f' ❗ Older than 3 days'
    print_tee(text)

  extra = got - set(HOSTS) - set(['wifi.lab', 'cinderblock.lab'])
  for host in sorted(extra):
    print_tee(f'Extra host: {host}')

def check_wifi(dir_path):
  now = datetime.datetime.now(datetime.UTC)
  host = 'wifi.lab'
  text = '- wifi.lab: '

  def _set_str(label, regexp, scale):
    files = [f for f in os.listdir(f'{dir_path}/wifi.lab/') if re.match(regexp, f)]

    text = f'{label}: '
    if not files:
      text += '❗ No backup'
    else:
      last = max(files)
      m = re.match(regexp, last)
      t = datetime.datetime.fromisoformat(m.group(1))
      size = os.path.getsize(f'{dir_path}/wifi.lab/{last}')
      # TODO: size sanity check
      bytes = {'KB': 1024, 'MB': 1024 * 1024, 'GB': 1024 * 1024 * 1024}[scale]
      text += f'{t.strftime("%b %-d")} ({(now - t).days} days ago, {size / bytes:.01f} {scale})'
      if t < now - datetime.timedelta(days=7):
        text += f' ❗ Older than 7 days'
    return text

  text += _set_str('MTD Full', re.compile(r'mtd-full.(.*).img.p7m'), 'MB')
  text += ', '
  text += _set_str('Sysupgrade Full', re.compile(r'sysupgrade-full.(.*).tar.gz.p7m'), 'KB')
  print_tee(text)

def check_cinderblock(dir_path):
  now = datetime.datetime.now(datetime.UTC)
  host = 'cinderblock.lab'
  text = '- cinderblock.lab: '

  def _set_str(label, regexp, scale):
    files = [f for f in os.listdir(f'{dir_path}/cinderblock.lab/') if re.match(regexp, f)]

    text = f'{label}: '
    if not files:
      text += '❗ No backup'
    else:
      last = max(files)
      m = re.match(regexp, last)
      t = datetime.datetime.fromisoformat(m.group(1))
      size = os.path.getsize(f'{dir_path}/cinderblock.lab/{last}')
      # TODO: size sanity check
      bytes = {'KB': 1024, 'MB': 1024 * 1024, 'GB': 1024 * 1024 * 1024}[scale]
      text += f'{t.strftime("%b %-d")} ({(now - t).days} days ago, {size / bytes:.01f} {scale})'
      if t < now - datetime.timedelta(days=7):
        text += f' ❗ Older than 7 days'
    return text

  text += _set_str('ZFS Full', re.compile(r'zroot-full.(.*).zfs.p7m'), 'GB')
  text += ', '
  text += _set_str('ZFS Incremental', re.compile(r'zroot-inc.(.*).zfs.p7m'), 'GB')
  text += ', '
  text += _set_str('Conf Full', re.compile(r'conf.(.*).tar.p7m'), 'MB')
  print_tee(text)

def main():
  parser = argparse.ArgumentParser(
                    prog='foulab-backup-check',
                    description='Checks backups for consistency and completness')
  parser.add_argument('-d', required=True, help='Root directory of backups')
  parser.add_argument('-e', action='store_true', help='Send e-mail')
  parser.add_argument('-m', action='store_true', help='Post to Mattermost')

  args = parser.parse_args()

  duplicity.log.setup()
  duplicity.config.archive_dir_path = duplicity.path.Path('/tmp')

  # In case one host is completely missing, prevent
  # dup_collections.CollectionsStatus() (-> backend.list()) from throwing an
  # exception (eg. FileNotFoundError) and killing the process. After commit
  # af2cfef0 (3.0.6.dev7), drop this, and use try/catch around
  # CollectionsStatus.
  duplicity.config.are_errors_fatal = {'list': (False, [])}

  check(args.d)
  check_wifi(args.d)
  check_cinderblock(args.d)

  if args.e:
    m = email.message.EmailMessage()
    m['To'] = 'root'
    m['Subject'] = 'Foulab Backup Check'
    m.set_content(mail)

    subprocess.run(['/sbin/sendmail', '-t', '-oi'], input=m.as_string(), encoding='ascii', check=True)

  if args.m:
    mattermost = mattermostdriver.Driver({
      'url': 'test.foulab.org',
      'port': 443,
      'login_id': 'bahamut',
      'token': open('/usr/local/etc/foulab-deaddrop-mattermost-token').read().strip(),
    })
    mattermost.login()

    mattermost.posts.create_post({
      # 'channel_id': 'na45qgqrsidcpjo6rorar4excy',  # DM to eigma
      'channel_id': 'wnh3qnh4xp8h5qa3ic7gkaiy5c',  # Tech Support
      'message': '**Backup Check**:\n\n' + mail,
    })

if __name__ == '__main__':
  main()
