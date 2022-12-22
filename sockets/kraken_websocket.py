from consts import KRAKEN_SUB_FILE, KRAKEN_STREAM_NAME, KRAKEN_SYMBOLS
from sockets.base_websocket import BaseWebsocket
from requests import get


class KrakenWebsocket(BaseWebsocket):
    """Сокет для Kraken'а"""
    def __init__(self, *args) -> None:
        super().__init__(KRAKEN_SUB_FILE, KRAKEN_STREAM_NAME, *args)
        self.list_of_symbols = self.get_top_pairs()
        self.add_pattern_to_resent()

    def get_top_pairs(self) -> dict:
        resp = get(KRAKEN_SYMBOLS).json()["result"]
        ans = dict()
        for val in resp.values():
            ans[val["wsname"]] = (*self.rename(val["wsname"].split("/")),
                                  list(map(lambda x: (float(x[0]), float(x[1])), val["fees"])))
        return ans

    def define_fee(self, symb: str, vol) -> float:
        """Возвращает комиссию, соответствующую объему ордера"""
        vol = float(vol)
        fees = self.list_of_symbols[symb][-1]
        for i in range(len(fees) - 1):
            if fees[i][0] <= vol <= fees[i + 1][0]:
                return fees[i][1] / 100

    def made_sub_json(self) -> dict:
        """Создание параметров соединения"""
        sub_json = super().made_sub_json()
        #symbs = [i[:-1] for i in self.list_of_symbols.values()]
        #sub_json["pair"] = list(map(lambda x: "/".join(x), symbs))
        sub_json["pair"] = list(self.list_of_symbols.keys())
        return sub_json

    def process(self, message: list) -> None:
        """Обработка данных"""
        if isinstance(message, dict):
            return
        symb = message[3]
        cur1, cur2 = self.list_of_symbols[symb][:-1]
        if 'as' in message[1].keys():
            bids, asks = message[1]["bs"], message[1]["as"]
            if not bids:
                bids = [[0, 0]]
            if not asks:
                asks = [[0, 0]]
            self.update_resent(
                symb, base=cur1, quote=cur2, exchange="kraken",
                bidPrice=float(bids[0][0]), bidQty=float(bids[0][1]),
                askPrice=float(asks[0][0]), askQty=float(asks[0][1]),
                takerFee=self.define_fee(symb, min(float(asks[0][1]), float(bids[0][1])))
            )
        else:
            if 'a' in message[1].keys():
                asks = message[1]["a"]
                if not asks:
                    asks = [[0, 0]]
                self.update_resent(
                    symb, askPrice=float(asks[0][0]), askQty=float(asks[0][1]),
                    takerFee=self.define_fee(symb, min(float(asks[0][1]), self.resent[symb]["bidQty"]))
                )
            if 'b' in message[1].keys():
                bids = message[1]["b"]
                if not bids:
                    bids = [[0, 0]]
                self.update_resent(
                    symb, bidPrice=float(bids[0][0]), bidQty=float(bids[0][1]),
                    takerFee=self.define_fee(symb, min(float(bids[0][1]), self.resent[symb]["askQty"]))
                )