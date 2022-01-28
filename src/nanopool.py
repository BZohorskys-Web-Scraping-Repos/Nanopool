import launcher

import asyncio
import curses
import itertools
import json
import logging
import webbrowser

import aiohttp

SITE = 'nanopool.org'

logging.basicConfig(
    level=logging.WARN,
    format='%(asctime)-15s [%(levelname)s] %(funcName)s: %(message)s',
)
# Sample logging call
# logging.WARN(locals())

async def search():
    urls = getUrls()
    urlTasks = []
    for link in urls:
        urlTasks.append(asyncio.create_task(get_account_details(link['api'], link['url'])))
    await idleAnimation(asyncio.gather(*urlTasks))
    dataList = []
    for task in urlTasks:
        if task.result()['code'] == 200:
            json_result = json.loads(task.result()['json'])
            data = {
                'avg_hash': json_result['data']['avgHashRate']['h6'],
                'balance': json_result['data']['userParams']['balance'],
                'current_hash': json_result['data']['userParams']['hashrate'],
                'url': task.result()['url']
            }
            dataList.append(data)
        else:
            print(f"Error: received a {task.response()['code']} for {task.response()['url']}.")
    curses.wrapper(interactive_console, dataList)

def getUrls():
    coin_map = {
        'ethereum': 'eth',
        'ethereum classic': 'etc',
        'zcash': 'zec',
        'monero': 'xmr',
        'ravencoin': 'rvn',
        'conflux': 'cfx',
        'ergo': 'ergo'
    }
    wallets = []
    with open(launcher.get_resource_path('wallet_addresses.txt')) as f:
        for line in f:
            if line[0] == '#' or line[0] == '\\':
                continue
            coin, wallet_address = line.split(maxsplit=1)
            coin_subdivision = ''
            if len(wallet_address.split()) > 1:
                coin_subdivision, wallet_address = wallet_address.split(maxsplit=1)
                coin = ''.join([coin, ' ', coin_subdivision])
            links = {
                'api': ''.join(['https://', coin_map[coin.lower()], '.', SITE, '/api/v1/load_account/', wallet_address]),
                'url': ''.join(['https://', coin_map[coin.lower()], '.', SITE, '/account/', wallet_address])
            }
            wallets.append(links)
    return wallets

async def get_account_details(apiurl, url):
    async with aiohttp.ClientSession() as session:
        async with session.get(apiurl) as response:
            code = response.status
            json = await response.text()
            return {'code':code,'json':json, 'url':url}

async def idleAnimation(task):
    for frame in itertools.cycle(r'-\|/-\|/'):
        if task.done():
            print('\r', '', sep='', end='', flush=True)
            break
        print('\r', frame, sep='', end='', flush=True)
        await asyncio.sleep(0.2)

def interactive_console(screen, data):
    pos = 0
    while pos < len(data):
        screen.clear()
        screen.addstr("({0}/{1}) Wallets\n".format(pos+1, len(data)))
        screen.addstr("Balance: {0}\n".format(data[pos]['balance']))
        screen.addstr("Curent Hashrate: {0}\n".format(data[pos]['current_hash']))
        screen.addstr("Avg Hashrate: {0}\n".format(data[pos]['avg_hash']))
        screen.addstr("Next, Previous, Open, or Quit? (j,k,o,q)")

        valid_response = False
        while not valid_response:
            user_respone = screen.getkey()
            if user_respone == 'j':
                valid_response = True
                pos += 1
            elif user_respone == 'k':
                if pos != 0:
                    valid_response = True
                    pos -= 1
                else:
                    user_respone = screen.getkey()
            elif user_respone == 'o':
                webbrowser.open(data[pos]['url'])
            elif user_respone == 'q':
                valid_response = True
                pos = len(data)
