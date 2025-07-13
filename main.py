import os
from pathlib import Path
import jdatetime
from datetime import datetime
import json
import requests
from bs4 import BeautifulSoup
import re
import base64
import wget
import math
import string
import random
from title import check_modify_config, create_country, create_country_table, create_internet_protocol

def get_absolute_paths(directory):
    for dirpath, _, filenames in os.walk(directory):
        for f in filenames:
            yield os.path.abspath(os.path.join(dirpath, f))

def json_load(file):
    with open(file, 'r', encoding='utf-8') as f:
        return json.load(f)

def tg_channel_messages(channel, last_update, proxies=None):
    url = f"https://t.me/s/{channel.replace('@', '')}"
    try:
        response = requests.get(url, proxies=proxies)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        messages = soup.find_all('div', class_='tgme_widget_message')
        result = []
        for message in messages:
            message_time = tg_message_time(message)
            if message_time and message_time > last_update:
                message_text = tg_message_text(message)
                if message_text:
                    result.append({'time': message_time, 'text': message_text})
        return result
    except requests.RequestException:
        return []

def find_matches(text):
    matches = []
    patterns = [
        r'(vmess://[^\s]+)', r'(vless://[^\s]+)', r'(trojan://[^\s]+)', r'(ss://[^\s]+)',
        r'(ssr://[^\s]+)', r'(reality://[^\s]+)', r'(tuic://[^\s]+)', r'(hysteria://[^\s]+)',
        r'(juicity://[^\s]+)'
    ]
    for pattern in patterns:
        matches.extend(re.findall(pattern, text))
    return matches

def tg_message_time(message):
    try:
        time_tag = message.find('time', class_='datetime')
        if time_tag and 'datetime' in time_tag.attrs:
            message_time = datetime.strptime(time_tag['datetime'], '%Y-%m-%dT%H:%M:%S%z')
            return message_time
    except:
        return None

def tg_message_text(message):
    try:
        text = message.find('div', class_='tgme_widget_message_text').get_text(separator=' ')
        return text
    except:
        return ''

def tg_username_extract(url):
    match = re.search(r't\.me/([^\s/]+)', url)
    return f"@{match.group(1)}" if match else None

def html_content(url, proxies=None):
    try:
        response = requests.get(url, proxies=proxies)
        response.raise_for_status()
        return response.text
    except requests.RequestException:
        return ''

def is_valid_base64(s):
    try:
        base64.b64decode(s, validate=True)
        return True
    except:
        return False

def decode_string(encoded_string):
    if is_valid_base64(encoded_string):
        try:
            decoded = base64.b64decode(encoded_string).decode('utf-8')
            return decoded
        except:
            return ''
    return ''

def decode_vmess(encoded_string):
    try:
        decoded = json.loads(decode_string(encoded_string[8:]))
        decoded['ps'] = decoded.get('ps', '').replace('/', '-').replace('\\', '-')
        return decoded
    except:
        return {}

def remove_duplicate_modified(configs):
    seen = set()
    result = []
    for config in configs:
        key = config.replace('/', '-').replace('\\', '-')
        if key not in seen:
            seen.add(key)
            result.append(config)
    return result

def remove_duplicate(configs):
    return list(dict.fromkeys(configs))

if not os.path.exists('geoip-lite'):
    os.makedirs('geoip-lite')

if not os.path.exists('geoip-lite/GeoLite2-Country.mmdb'):
    url = 'https://github.com/P3TERX/GeoLite.mmdb/raw/download/GeoLite2-Country.mmdb'
    wget.download(url, './geoip-lite/GeoLite2-Country.mmdb')

if os.path.exists('last update'):
    with open('last update', 'r') as f:
        last_update = datetime.strptime(f.read().strip(), '%Y-%m-%d %H:%M:%S.%f%z')
else:
    last_update = datetime.strptime('1970-01-01 00:00:00.000000+0330', '%Y-%m-%d %H:%M:%S.%f%z')

current_time = datetime.now().astimezone(last_update.tzinfo)
with open('last update', 'w') as f:
    f.write(current_time.strftime('%Y-%m-%d %H:%M:%S.%f%z'))

if current_time.day in [1, 15] and current_time.hour == 0:
    for path in get_absolute_paths('.'):
        if os.path.basename(path) != 'last update':
            os.remove(path)

# Load telegram channels from local file
telegram_proxies_channel = json_load('./telegram channels.json')

invalid_channels = json_load('invalid telegram channels.json')
channels_configs = []
channels_messages = []

for channel in telegram_proxies_channel:
    messages = tg_channel_messages(channel, last_update)
    if not messages:
        invalid_channels.append(channel)
        continue
    for message in messages:
        configs = find_matches(message['text'])
        if configs:
            channels_configs.extend(configs)
        urls = re.findall(r'https://t\.me/[^\s]+', message['text'])
        for url in urls:
            username = tg_username_extract(url)
            if username and username not in telegram_proxies_channel + invalid_channels:
                telegram_proxies_channel.append(username)
        channels_messages.append({'channel': channel, 'time': message['time'], 'configs': configs})

with open('telegram channels.json', 'w', encoding='utf-8') as f:
    json.dump(telegram_proxies_channel, f, indent=2, ensure_ascii=False)

with open('invalid telegram channels.json', 'w', encoding='utf-8') as f:
    json.dump(list(dict.fromkeys(invalid_channels)), f, indent=2, ensure_ascii=False)

subscribe_configs = []
subscribe_urls = json_load('subscription links.json')
for url in subscribe_urls:
    content = html_content(url)
    decoded_content = decode_string(content.strip())
    if decoded_content:
        configs = decoded_content.splitlines()
        subscribe_configs.extend([config for config in configs if any(config.startswith(prefix) for prefix in ['vmess://', 'vless://', 'trojan://', 'ss://', 'ssr://', 'reality://', 'tuic://', 'hysteria://', 'juicity://'])])

configs = channels_configs + subscribe_configs
configs = remove_duplicate(configs)
modified_configs = remove_duplicate_modified([check_modify_config(config) for config in configs])

if not os.path.exists('splitted'): os.makedirs('splitted')
if not os.path.exists('countries'): os.makedirs('countries')
if not os.path.exists('layers'): os.makedirs('layers')
if not os.path.exists('protocols'): os.makedirs('protocols')
if not os.path.exists('security'): os.makedirs('security')
if not os.path.exists('networks'): os.makedirs('networks')
if not os.path.exists('channels'): os.makedirs('channels')
if not os.path.exists('subscribe'): os.makedirs('subscribe')

vmess_configs = [config for config in modified_configs if config.startswith('vmess://')]
vless_configs = [config for config in modified_configs if config.startswith('vless://')]
trojan_configs = [config for config in modified_configs if config.startswith('trojan://')]
shadowsocks_configs = [config for config in modified_configs if config.startswith('ss://')]
ssr_configs = [config for config in modified_configs if config.startswith('ssr://')]
reality_configs = [config for config in modified_configs if config.startswith('reality://')]
tuic_configs = [config for config in modified_configs if config.startswith('tuic://')]
hysteria_configs = [config for config in modified_configs if config.startswith('hysteria://')]
juicity_configs = [config for config in modified_configs if config.startswith('juicity://')]

protocols = {
    'vmess': vmess_configs, 'vless': vless_configs, 'trojan': trojan_configs,
    'shadowsocks': shadowsocks_configs, 'ssr': ssr_configs, 'reality': reality_configs,
    'tuic': tuic_configs, 'hysteria': hysteria_configs, 'juicity': juicity_configs
}

for protocol, configs in protocols.items():
    if configs:
        with open(f'protocols/{protocol}', 'w', encoding='utf-8') as f:
            f.write('\n'.join(configs))

tcp_configs = [config for config in modified_configs if 'type=tcp' in config]
ws_configs = [config for config in modified_configs if 'type=ws' in config]
http_configs = [config for config in modified_configs if 'type=http' in config]
grpc_configs = [config for config in modified_configs if 'type=grpc' in config]

networks = {'tcp': tcp_configs, 'ws': ws_configs, 'http': http_configs, 'grpc': grpc_configs}

for network, configs in networks.items():
    if configs:
        with open(f'networks/{network}', 'w', encoding='utf-8') as f:
            f.write('\n'.join(configs))

tls_configs = [config for config in modified_configs if 'security=tls' in config]
non_tls_configs = [config for config in modified_configs if 'security=tls' not in config]

security = {'tls': tls_configs, 'non-tls': non_tls_configs}

for sec, configs in security.items():
    if configs:
        with open(f'security/{sec}', 'w', encoding='utf-8') as f:
            f.write('\n'.join(configs))

countries_configs = create_country(modified_configs)
for country, configs in countries_configs.items():
    if configs:
        if not os.path.exists(f'countries/{country}'):
            os.makedirs(f'countries/{country}')
        with open(f'countries/{country}/mixed', 'w', encoding='utf-8') as f:
            f.write('\n'.join(configs))

internet_protocols = create_internet_protocol(modified_configs)
for ip, configs in internet_protocols.items():
    with open(f'layers/{ip}', 'w', encoding='utf-8') as f:
        f.write('\n'.join(configs))

split_count = math.ceil(len(modified_configs) / 10)
for i in range(10):
    split_configs = modified_configs[i * split_count:(i + 1) * split_count]
    if split_configs:
        with open(f'splitted/mixed-{i}', 'w', encoding='utf-8') as f:
            f.write('\n'.join(split_configs))

for message in channels_messages:
    channel = message['channel'].replace('@', '')
    if message['configs']:
        if not os.path.exists(f'channels/{channel}'):
            os.makedirs(f'channels/{channel}')
        with open(f'channels/{channel}/mixed', 'w', encoding='utf-8') as f:
            f.write('\n'.join(message['configs']))

for i, config in enumerate(subscribe_configs):
    with open(f'subscribe/mixed-{i}', 'w', encoding='utf-8') as f:
        f.write(config)

with open('splitted/mixed', 'w', encoding='utf-8') as f:
    f.write('\n'.join(modified_configs))

encoded_configs = base64.b64encode('\n'.join(modified_configs).encode('utf-8')).decode('utf-8')
with open('splitted/mixed.base64', 'w', encoding='utf-8') as f:
    f.write(encoded_configs)

with open('splitted/channels', 'w', encoding='utf-8') as f:
    f.write('\n'.join(channels_configs))

with open('splitted/subscribe', 'w', encoding='utf-8') as f:
    f.write('\n'.join(subscribe_configs))

def create_title():
    title = f"# Telegram Configs Collector\n\n"
    title += f"Last Update: {jdatetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S')} IRST\n"
    title += "Developer: Soroush Mirzaei\n"
    title += "Signature: @soroushmirzaei\n"
    title += "Advertisement: @v2rayng_config\n\n"
    title += "## Countries\n\n"
    title += create_country_table(countries_configs)
    return title

with open('readme.md', 'w', encoding='utf-8') as f:
    f.write(create_title())
