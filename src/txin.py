from nacl.encoding import HexEncoder
from nacl.encoding import Base64Encoder
from nacl.signing import SigningKey
from nacl.signing import VerifyKey
from transaction import Transaction, getUnspentTxOut
import json, pickle, random, os


class TxIn:
    def __init__(self, _txoutid, _txoutidx, _sign):
        self.txoutid = _txoutid
        self.txoutidx = _txoutidx
        self.signature = _sign

    # get a json representation of the TxIn
    def jsonRep(self):
        rep = {}
        rep["txoutid"] = str(self.txoutid)[2:-1]
        rep["txoutidx"] = self.txoutidx
        rep["signature"] = str(self.signature)[2:-1]
        return json.dumps(rep)

    # get a dict representation of the TxIn
    def readableObject(self):
        rep = {}
        rep["txoutid"] = str(self.txoutid)[2:-1]
        rep["txoutidx"] = self.txoutidx

        filepaths = None
        while not filepaths or os.path.exists(filepaths):
            filepathNum = random.randint(1, 99999999)
            filepaths = "bin/" + str(filepathNum)

        pickle.dump(self.signature, open(filepaths, "wb"))
        rep["signature"] = filepaths  # need a persistent location for the signature
        return rep

    def validateTxIn(self, allUTxOs):
        """
        Validates if the TxIn was signed correctly
        """
        # find uTxO that was made into this TxIn
        referencedUnspentTxOut = getUnspentTxOut(self.txoutid, self.txoutidx, allUTxOs)
        if referencedUnspentTxOut == None:
            return False

        addr = referencedUnspentTxOut.address
        # create a verification key from this address, apparently addr is the
        # hex representation of the public key itself
        key = VerifyKey(addr, HexEncoder)

        # verify that the person or key who signed this TxIn is the same person who this uTxO belongs to
        try:
            signature_bytes = HexEncoder.decode(self.signature.signature)
            key.verify(self.signature.message, signature_bytes, HexEncoder)
        except:
            print("SIGNATURE VERIFICATION ERROR")
            return False
        else:
            return True


def signTxIn(
    transactionObj: Transaction, txinidx, privateKey: SigningKey, unspentTxOuts
):
    """
    Signs the TxIn with the private key and returns the signature
    """
    txIn = transactionObj.txins[txinidx]
    unsigned = transactionObj.getTransactionId()
    referencedUnspentTxOut = getUnspentTxOut(txIn.txoutid, txIn.txoutidx, unspentTxOuts)

    # sanity check to see if the uTxO actually exists
    if referencedUnspentTxOut == None:
        return ""

    referencedAddress = referencedUnspentTxOut.address
    if referencedAddress != privateKey.verify_key.encode(
        HexEncoder
    ):  # checking if the uTxO belongs to the private key holder
        return ""

    # sign the transaction id
    signed = privateKey.sign(unsigned, HexEncoder)
    return signed
