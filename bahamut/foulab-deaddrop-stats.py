#!/usr/bin/python3
import mattermostdriver, os, json, tempfile, random, sys

# TODO: clean up 'daily'
track = sys.argv[1]

try:
  f = open(f'/usr/local/state/foulab-deaddrop-state-{track}.json')
except FileNotFoundError:
  state = {}
else:
  state = json.load(f)

daily = []

delta = []
new_state = {}
with os.scandir('/srv/dev-disk-by-id-wwn-0x6848f690ea02b0002d5d2b875414ebb8-part1/shared/') as it:
  for top in sorted(it, key=lambda e: e.name):
    if top.is_dir() and not top.name.startswith('.') and top.name != 'lost+found':
      prev_count = state.get(top.name, 0)

      treei = os.walk(top)
      file_count = sum(len(filenames) for dirname, _, filenames in treei if
        # Ignore this, has high churn every day.
        '/BACKUPS/automated' not in dirname
      )

      # testing
      # if top.name == 'TEMP': file_count = prev_count + 1
      # elif top.name == 'COMICS': file_count = prev_count + 1

      print(f'{top.name}: {prev_count} -> {file_count} (+ {file_count - prev_count})')
      text = f'{top.name}: '
      if prev_count == file_count:
        text += f'{file_count}'
      else:
        text = ':arrow_forward: ' + text + f'{prev_count} -> {file_count} (+ {file_count - prev_count})'
      daily.append(text)
      
      if file_count > prev_count:
        delta.append((top.name, file_count - prev_count))
      new_state[top.name] = file_count

mattermost = mattermostdriver.Driver({
  'url': 'test.foulab.org',
  'port': 443,
  'login_id': 'bahamut',
  'token': open('/usr/local/etc/foulab-deaddrop-mattermost-token').read().strip(),
})
mattermost.login()

if track == 'daily':
  message = ', '.join(daily)
  print(f'Daily: {message}')
  mattermost.posts.create_post({
    'channel_id': 'na45qgqrsidcpjo6rorar4excy',  # DM to eigma
    'message': message,
  })

if track == 'weekly':
  if delta:
    delta.sort(key=lambda kv: kv[1], reverse=True)
    top = delta[0]
    quote = random.choice([
      'Lo and behold',
      'By the light of truth',
      'With justice for all',
    ])
    message = f'{quote}, there are {top[1]} new files in {top[0]}'
    if len(delta) >= 2:
      others = sum(file_count for _, file_count in delta[1:])
      message += f', and {others} other new files'
    message += '. From the Lab network: http://bahamut.lab/'
    print(f'Weekly: {message}')

    mattermost.posts.create_post({
      'channel_id': 'mhfjtejsdb8epfon6gt3sfeizh',  # FOULAB
      'message': message,
    })

with tempfile.NamedTemporaryFile(
    mode='w', dir='/usr/local/state/',
    prefix=f'foulab-deaddrop-state-{track}-', suffix='.json',
    delete=False, encoding='utf-8') as f:
  json.dump(new_state, f, indent=2)
os.rename(f.name, f'/usr/local/state/foulab-deaddrop-state-{track}.json')
