from nacl.encoding import HexEncoder
from nacl.encoding import Base64Encoder
from nacl.signing import SigningKey
from nacl.signing import VerifyKey
import transaction
import json
import pickle
import random

class TxIn:
    def __init__(self, _txoutid, _txoutidx, _sign):
        self.txoutid = _txoutid
        self.txoutidx = _txoutidx
        self.signature = _sign

    def jsonRep(self):
        rep = {}
        rep['txoutid'] = str(self.txoutid)[2:-1]
        rep['txoutidx'] = self.txoutidx
        rep['signature'] = str(self.signature)[2:-1]
        return json.dumps(rep)

    def readableObject(self):
        rep = {}
        rep['txoutid'] = str(self.txoutid)[2:-1]
        rep['txoutidx'] = self.txoutidx
        filepathNum = random.randint(1, 99999999)
        filepaths = "bin/"+str(filepathNum)
        pickle.dump(self.signature, open(filepaths, "wb"))
        rep['signature'] = filepaths
        return rep


# sign the TxIn with the private key
def signTxIn(transactions, txinidx, privateKey: SigningKey, unspentTxOuts):
    txIn = transactions.txins[txinidx]
    unsigned = transactions.getTransactionId()
    referencedUnspentTxOut = transaction.getUnspentTxOut(txIn.txoutid, txIn.txoutidx, unspentTxOuts)
    if referencedUnspentTxOut == None:
        return ''
    referencedAddress = referencedUnspentTxOut.address
    if referencedAddress != privateKey.verify_key.encode(HexEncoder): #recheck
        return ''
    signed = privateKey.sign(unsigned, HexEncoder)
    return signed

# validate if the TxIn was signed correctly

def validateTxIn(txIn, transactions, allUTxOs):
    # find uTxO that was made into this TxIn
    referencedUnspentTxOut = transaction.getUnspentTxOut(txIn.txoutid, txIn.txoutidx, allUTxOs)
    if referencedUnspentTxOut == None:
        return False

    addr = referencedUnspentTxOut.address
    # create a verification key from this address, apparently addr is the
    # hex representation of the public key itself
    key = VerifyKey(addr,HexEncoder)

    # the id is the "message", the signature is obviously the signature
    try:
        signature_bytes = HexEncoder.decode(txIn.signature.signature)
        key.verify(txIn.signature.message, signature_bytes, HexEncoder)
    except:
        print("SIGNATURE VERIFICATION ERROR")
        return False
    else:
        return True
