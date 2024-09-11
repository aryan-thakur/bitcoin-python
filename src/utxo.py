import json


class UTxO:
    def __init__(self, _txoutid, _txoutidx, _addr, _amt):
        self.txoutid = _txoutid
        self.txoutidx = _txoutidx
        self.address = _addr
        self.amount = _amt

    # gets the json representation of this uTxO
    def jsonRep(self):
        rep = {}
        rep["txoutid"] = str(self.txoutid)[2:-1]
        rep["txoutidx"] = self.txoutidx
        rep["address"] = str(self.address)[2:-1]
        rep["amount"] = self.amount
        return json.dumps(rep)

    # gets the dict representation of this uTxO
    def readableObject(self):
        rep = {}
        rep["txoutid"] = str(self.txoutid)[2:-1]
        rep["txoutidx"] = self.txoutidx
        rep["address"] = str(self.address)[2:-1]
        rep["amount"] = self.amount
        return rep
