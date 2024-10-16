import asyncio
import time
import datetime
import os
from binance import AsyncClient, BinanceSocketManager


async def main():
    active_file_time = int(round(time.time()) / 60)
    new_local_data_file_path = './' + str(int(active_file_time * 60)) + '.tsv'

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
            print(res)
            if new_file_time != active_file_time:
                f.close()
                # Eğer mesajın içindeki Unix dakikası active_file_time'a eşit değil ise 1dk'lık biriktirme süresi,
                # dolmuş ve biriktirilen datanın bucket'a yüklenmesi gerekli.

                active_file_time = new_file_time
                new_local_data_file_path = './' + str(int(active_file_time * 60)) + '.tsv'

                f = open(new_local_data_file_path, 'w')
                print(' #' * 50)
                print(' #' * 50)
                print(' #' * 50)
                print(' #' * 20 + ' new file:' + new_local_data_file_path + ' #' * 20)
                print(' #' * 50)
                print(' #' * 50)
                print(' #' * 50)

            timestamp = f"{datetime.datetime.fromtimestamp(int(res['T'] / 1000)):%Y-%m-%d %H:%M:%S}"
            maker = '0'
            if res['m']:  # Satın almış ise 1, satış yaptı ise 0.
                maker = '1'

            line = str(res['t']) + '\t'
            line += str(res['s']) + '\t'
            line += '{:.2f}'.format(round(float(res['p']), 2)) + '\t'
            line += str(res['q'])[0:-3] + '\t'
            line += str(timestamp) + '\t'
            line += str(maker) + '\n'
            f.write(line)
            # Line oluşturuldu
            print(line)
            # print(res)

    await client.close_connection()


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
