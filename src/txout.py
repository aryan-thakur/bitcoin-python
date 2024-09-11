import json


class TxOut:
    def __init__(self, _addr, _amt):
        self.address = _addr
        self.amount = _amt

    # gets the json representation of this TxOut
    def jsonRep(self):
        rep = {}
        rep["address"] = str(self.address)[2:-1]
        rep["amount"] = self.amount
        return json.dumps(rep)

    # gets the dict representation of this TxOut
    def readableObject(self):
        rep = {}
        rep["address"] = str(self.address)[2:-1]
        rep["amount"] = self.amount
        return rep
