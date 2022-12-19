from scheduler import Scheduler
from sockets.binance_websocket import BinanceWebsocket
from sockets.poloniex_websocket import PoloniexWebsocket
from sockets.kraken_websocket import KrakenWebsocket
from sockets.gate_websocket import GateWebsocket
from sockets.huobi_websocket import HuobiWebsocket
from argparse import ArgumentParser
import threading

parser = ArgumentParser("Получение исторических данных за промежуток времени")
parser.add_argument("--duration", type=int, default=60, nargs='?')
parser.add_argument("--filename", default="logs.tsv", nargs="?")


if __name__ == '__main__':
    args = parser.parse_args()
    event = threading.Event()
    to_start = [BinanceWebsocket(), PoloniexWebsocket(), KrakenWebsocket(),
                GateWebsocket(), HuobiWebsocket()]
    [socket.start() for socket in to_start]
    scheduler = Scheduler(*to_start, duration=args.duration, event=event,
                          filename=args.filename)
    scheduler.start()
    scheduler.schedule_thread.join(args.duration)
    event.set()
    scheduler.schedule_thread.join()