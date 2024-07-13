import json
class TxOut:
    def __init__(self, _addr, _amt):
        self.address = _addr
        self.amount = _amt

    def jsonRep(self):
        rep = {}
        rep['address'] = str(self.address)[2:-1]
        rep['amount'] = self.amount
        return json.dumps(rep)

    def readableObject(self):
        rep = {}
        rep['address'] = str(self.address)[2:-1]
        rep['amount'] = self.amount
        return rep
