import asyncio
import datetime
import os
import time
from binance import AsyncClient, BinanceSocketManager
from dateutil.parser import parse

count = 0


data_dir = "./data/"
if not os.path.exists(data_dir):
    os.makedirs(data_dir)
    print(f"Directory '{data_dir}' created.")
else:
    print(f"Directory '{data_dir}' already exists.")



async def main():
    global count
    active_file_time = int(round(time.time()) / 60)

    new_local_data_file_path = data_dir + str(int(active_file_time * 60)) + '.tsv'
    #
    f = open(new_local_data_file_path, 'w')
    client = await AsyncClient.create()
    bm = BinanceSocketManager(client)
    trade_socket = bm.trade_socket('BTCUSDT')
    # BTCUSDT parametresindeki market hareketlerinin datasını istiyoruz.
    async with trade_socket as tscm:
        while True:
            res = await tscm.recv()
            new_file_time = int(res['T'] / (1000 * 60))
            # Gelen datanın içindeki unixtime'ı (milisecond cinsinden) dakikaya çeviriyoruz.
            # print(res)
            if new_file_time != active_file_time:
                f.close()
                # Eğer mesajın içindeki Unix dakikası active_file_time'a eşit değil ise 1dk'lık biriktirme süresi,
                # dolmuş ve biriktirilen datanın bucket'a yüklenmesi gerekli.

                
                if count > 99:
                    exit(1)
                count += 1
                active_file_time = new_file_time
                new_local_data_file_path = data_dir + str(int(active_file_time * 60)) + '.tsv'

                f = open(new_local_data_file_path, 'w')

            timestamp = res['T']
            maker = '0'
            print(res)
            if res['m']:  # Satın almış ise 1, satış yaptı ise 0.
                maker = '1'

            line = str(res['t']) + '\t'
            line += str(res['s']) + '\t'
            line += res['p']+'\t'
            line += str(res['q'])+ '\t'
            line += str(timestamp) + '\t'
            line += str(maker) + '\n'
            print(line)
            f.write(line)
            # Line oluşturuldu
            # print(line)
            # print(res)

    await client.close_connection()


loop = asyncio.get_event_loop()
loop.run_until_complete(main())