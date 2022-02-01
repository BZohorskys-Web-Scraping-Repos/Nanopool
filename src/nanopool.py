import launcher

import asyncio
import curses
import itertools
import json
import logging
import webbrowser

import aiohttp
from lxml import html

NANOPOOL_SITE = 'nanopool.org'
RAVEN_EXPLORER_API_CALL = 'https://explorer.ravencoin.org/api/addr/'
COIN_MARKET_CAP_SITE = 'https://coinmarketcap.com/currencies/'

logging.basicConfig(
    level=logging.WARN,
    format='%(asctime)-15s [%(levelname)s] %(funcName)s: %(message)s',
)
# Sample logging call
# logging.WARN(locals())

async def search():
    wallets= parseWalletAddressFile()
    walletDetailsTaskList = []
    for wallet in wallets:
        walletDetailsTaskList.append(asyncio.create_task(get_wallet_details(wallet)))
    await idleAnimation(asyncio.gather(*walletDetailsTaskList))
    walletDetailsList= []
    for walletDetails in walletDetailsTaskList:
        if not walletDetails.result()['error']:
            walletDetailsList.append(walletDetails.result())
        else:
            print(f"Error: received an error {walletDetails.response()['address']}.")
    curses.wrapper(interactive_console, walletDetailsList)

def parseWalletAddressFile():
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
            data = {
                'nanoapi': ''.join(['https://', coin_map[coin.lower()], '.', NANOPOOL_SITE, '/api/v1/load_account/', wallet_address]),
                'nanourl': ''.join(['https://', coin_map[coin.lower()], '.', NANOPOOL_SITE, '/account/', wallet_address]),
                'address': wallet_address
            }
            if coin.lower() == 'ravencoin':
                data['explorerapi'] = RAVEN_EXPLORER_API_CALL + data['address']
            data['coinmarketcapurl'] = COIN_MARKET_CAP_SITE + coin.lower()
            wallets.append(data)
    return wallets

async def get_wallet_details(data):
    wallet_details = {
        'error': False
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(data['nanoapi']) as response:
            if response.status != 200:
                wallet_details['error'] = True
            else:
                nano_api_json = await response.text()
                json_result = json.loads(nano_api_json)
                wallet_details['avg_hash'] = json_result['data']['avgHashRate']['h6']
                wallet_details['mining_balance'] = json_result['data']['userParams']['balance']
                wallet_details['current_hash'] = json_result['data']['userParams']['hashrate']
                wallet_details['nanourl'] = data['nanourl']

        if 'explorerapi' in data:
            async with session.get(data['explorerapi']) as response:
                if response.status != 200:
                    wallet_details['error'] = True
                else:
                    explorer_api_json = await response.text()
                    json_result = json.loads(explorer_api_json)
                    wallet_details['wallet_balance'] = json_result['balance']

        async with session.get(data['coinmarketcapurl']) as response:
            if response.status != 200:
                wallet_details['error'] = True
            else:
                html_str = await response.text()
                html_tree = html.fromstring(html_str)
                wallet_details['coin_value'] = html_tree.xpath('//div[@class="priceValue "]/span/text()')[0]

    return wallet_details


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
        screen.addstr("Coin Value: {0}\n".format(data[pos]['coin_value']))
        if 'wallet_balance' in data[pos]:
            screen.addstr("Wallet Balance: {0}\n".format(data[pos]['wallet_balance']))
            screen.addstr("Wallet Value: ${0}\n".format(float(data[pos]['wallet_balance']) * float(data[pos]['coin_value'][1:])))
        screen.addstr("Mining Balance: {0}\n".format(data[pos]['mining_balance']))
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
                webbrowser.open(data[pos]['nanourl'])
            elif user_respone == 'q':
                valid_response = True
                pos = len(data)
