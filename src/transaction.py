from nacl.encoding import Base64Encoder
from nacl.hash import sha256
import utxo
import txout
import json


class Transaction:
    def __init__(self, _txins, _txouts, _id=""):
        self.txins = _txins
        self.txouts = _txouts
        self.id = _id

    def getTransactionId(self):
        if self.id != "":
            return self.id

        # make a string consisting of all txins appeneded together
        txinstr = ""
        for txin in self.txins:
            txinstr = txinstr + str(txin.txoutid) + str(txin.txoutidx)

        # make a string consisting of all txouts appeneded together
        txoutstr = ""
        for txouts in self.txouts:
            txoutstr = txoutstr + str(txouts.address) + str(txouts.amount)

        # thus, generate a unique hash
        return sha256(str.encode((txinstr + txoutstr)), Base64Encoder)

    # get a json representation of the transaction
    def jsonRep(self):
        rep = {}
        txinJson = []
        for txins in self.txins:
            txinJson.append(txins.jsonRep())
        txoutJson = []
        for txouts in self.txouts:
            txinJson.append(txouts.jsonRep())
        rep["txins"] = txinJson
        rep["txouts"] = txoutJson
        rep["id"] = str(self.getTransactionId())[2:-1]
        return json.dumps(rep)

    # get a dict representation of the transaction
    def readableObject(self):
        rep = {}
        txinJson = []
        for txins in self.txins:
            txinJson.append(txins.readableObject())
        txoutJson = []
        for txouts in self.txouts:
            txoutJson.append(txouts.readableObject())
        rep["txins"] = txinJson
        rep["txouts"] = txoutJson
        rep["id"] = str(self.getTransactionId())[2:-1]
        return rep

    def validateTransactionBalance(self, allUnspentTxOs):
        """
        Returns whether the txins total amount match the txouts total amount
        """
        txintotal = 0
        for txins in self.txins:
            txinamt = getTxInAmt(txins, allUnspentTxOs)
            txintotal = txintotal + txinamt

        txouttotal = 0
        for txouts in self.txouts:
            txouttotal = txouttotal + txouts.amount

        return txintotal == txouttotal

    def isValidTxForPool(self, pool):
        """
        Returns false if the transaction is using a TxIn already referenced by some transaction in the pool
        """
        for pooltx in pool:
            for txins in pooltx.txins:
                for txins2 in self.txins:
                    if (
                        txins.txoutid == txins2.txoutid
                        and txins.txoutidx == txins2.txoutidx
                    ):
                        return False
        return True

    def validateTransaction(self, allUnspentTxOs):
        """
        Check signature of input txins, check balances
        """
        import txin

        # id is always correct
        # validate inputs by validating the signature of the signer
        for txins in self.txins:
            if not txins.validateTxIn(allUnspentTxOs):
                return False  # a single failure is a big issue, the uTxO might not belong to the signer

        # TxOuts are always correct, just check the balancing
        if not self.validateTransactionBalance(allUnspentTxOs):
            return False

        return True


COINBASE_AMT = 50


# find a particular uTxO in a list of uTxOs
def findUnspentTxOut(tOId, tOIndex, allUTxOs):
    for utxo in allUTxOs:
        if utxo.txoutid == tOId and utxo.txoutidx == tOIndex:
            return True  # found
    return False


# return a particular TxIn in a list of uTxOs
def getUnspentTxOut(tOId, tOIndex, allUTxOs):
    for utxo in allUTxOs:
        if utxo.txoutid == tOId and utxo.txoutidx == tOIndex:
            return utxo  # found
    return None


# return how much is the TxIn worth as a uTxO amount. Note that TxIns and uTxOs have a 1-1 match.
def getTxInAmt(txins, allUTxOs):
    return getUnspentTxOut(txins.txoutid, txins.txoutidx, allUTxOs).amount


def newUTxOs(transactions):
    """
    Returns a list of all the new UTxOs that were detected in these transactions, built from TxOuts
    """
    utxos = []
    for transaction in transactions:
        idx = 0
        for txo in transaction.txouts:
            utxos.append(
                utxo.UTxO(transaction.getTransactionId(), idx, txo.address, txo.amount)
            )
            idx = idx + 1
    return utxos


def consumedUTxOs(transactions):
    """
    Returns a list of consumed UTxOs detected in these transactions (basically all TxIns)
    """
    utxos = []
    for transaction in transactions:
        for txins in transaction.txins:
            utxos.append(utxo.UTxO(txins.txoutid, txins.txoutidx, "", 0))

    return utxos


def updateUnspentTxOs(newTransactions, allUnspentTxOs):
    """
    Will update your UTxOs array according to the array of transactions provided
    """
    # new uTxOs created
    newutxos = newUTxOs(newTransactions)
    # consumed uTxOs
    consumedutxos = consumedUTxOs(newTransactions)

    filteredutxos = []

    for utxo in allUnspentTxOs:
        if not findUnspentTxOut(
            utxo.txoutid, utxo.txoutidx, consumedutxos
        ):  # if found in consumed REMOVE from the all uTxO list
            filteredutxos.append(utxo)

    returnutxos = [*filteredutxos, *newutxos]
    return returnutxos


# returns true if validated the coinbase transaction
def validateCoinbase(transaction, blockIdx):
    if len(transaction.txins) != 1:
        return False
    if transaction.txins[0].txoutidx != blockIdx:
        return False
    if len(transaction.txouts) != 1:
        return False
    if transaction.txouts[0].amount != COINBASE_AMT:
        return False
    return True


# validate your array of transactions before making a block
def validateAllTransactions(allTx, allUnspentTxOs, blockIdx):
    if not validateCoinbase(allTx[0], blockIdx):
        return False  # immediate termination

    for idx in range(len(allTx)):
        if idx == 0:
            continue
        else:
            if not allTx[idx].validateTransaction(allUnspentTxOs):
                return False
    return True


def processTransactions(transactions, allUTxOs, blockIdx):
    """
    Validates transactions and updates the global uTxO list with it, that was passed in as a parameter
    """
    if not validateAllTransactions(transactions, allUTxOs, blockIdx):
        return None
    return updateUnspentTxOs(transactions, allUTxOs)


# VERY IMPORTANT: When you make a block with many transactions, validate all
# using the above function, then you MUST update your global UTxO array as well


def makeCoinbaseTransaction(receiverAddr, blockIdx):
    """
    Makes the coinbase transaction and returns it
    """
    import txin

    tx = Transaction([], [])
    newTxIn = txin.TxIn("", blockIdx, "")
    # no id, no signature

    tx.txins = [newTxIn]
    tx.txouts = [txout.TxOut(receiverAddr, COINBASE_AMT)]
    return tx
