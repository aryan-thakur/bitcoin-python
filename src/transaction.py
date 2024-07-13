from nacl.encoding import Base64Encoder
from nacl.hash import sha256
import utxo
import txin
import txout
import json

class Transaction:
    def __init__(self, _txins, _txouts, _id=''):
        self.txins = _txins
        self.txouts = _txouts
        self.id = _id

    def getTransactionId(self):
        if self.id != '':
            return self.id
            
        txinstr = ""
        for txin in self.txins:
            txinstr = txinstr + str(txin.txoutid) + str(txin.txoutidx)

        txoutstr = ""
        for txouts in self.txouts:
            txoutstr = txoutstr + str(txouts.address) + str(txouts.amount)

        return sha256(str.encode((txinstr+txoutstr)), Base64Encoder)

    def jsonRep(self):
        rep = {}
        txinJson = []
        for txins in self.txins:
            txinJson.append(txins.jsonRep())
        txoutJson = []
        for txouts in self.txouts:
            txinJson.append(txouts.jsonRep())
        rep['txins'] = txinJson
        rep['txouts'] = txoutJson
        rep['id'] = str(self.getTransactionId())[2:-1]
        return json.dumps(rep)

    def readableObject(self):
        rep = {}
        txinJson = []
        for txins in self.txins:
            txinJson.append(txins.readableObject())
        txoutJson = []
        for txouts in self.txouts:
            txoutJson.append(txouts.readableObject())
        rep['txins'] = txinJson
        rep['txouts'] = txoutJson
        rep['id'] = str(self.getTransactionId())[2:-1]
        return rep

COINBASE_AMT = 50

# helper
def findUnspentTxOut(tOId, tOIndex, allUTxOs):
    for utxo in allUTxOs:
        if utxo.txoutid == tOId and utxo.txoutidx == tOIndex:
            return True #found
    return False

# helper
def getUnspentTxOut(tOId, tOIndex, allUTxOs):
    for utxo in allUTxOs:
        if utxo.txoutid == tOId and utxo.txoutidx == tOIndex:
            return utxo #found
    return None

# helper
def getTxInAmt(txins, allUTxOs):
    return getUnspentTxOut(txins.txoutid, txins.txoutidx, allUTxOs).amount

# the new UTxOs that were detected in these transactions (multiple)
def newUTxOs(transactions):
    utxos = []
    for transaction in transactions:
        idx = 0
        for txo in transaction.txouts:
            utxos.append(utxo.UTxO(transaction.getTransactionId(), idx, txo.address, txo.amount))
            idx = idx + 1
    return utxos

# consumed UTxOs detected in these transactions (basically all TxIns)
def consumedUTxOs(transactions):
    utxos = []
    for transaction in transactions:
        for txins in transaction.txins:
            utxos.append(utxo.UTxO(txins.txoutid, txins.txoutidx, '', 0))

    return utxos

# will update your UTxOs array according to the array of transactions provided using 2 fns above
def updateUnspentTxOs(newTransactions, allUnspentTxOs):
    newutxos = newUTxOs(newTransactions)
    consumedutxos = consumedUTxOs(newTransactions)

    filteredutxos = []

    for utxo in allUnspentTxOs:
        if not findUnspentTxOut(utxo.txoutid, utxo.txoutidx, consumedutxos): #if found in consumed REMOVE
             filteredutxos.append(utxo)

    returnutxos = [*filteredutxos, *newutxos]
    return returnutxos

# does the txins total amount match the txouts total amount
def validateTransactionBalance(transaction, allUnspentTxOs):
    txintotal = 0
    for txins in transaction.txins:
        txinamt = getTxInAmt(txins, allUnspentTxOs)
        txintotal = txintotal + txinamt

    txouttotal = 0
    for txouts in transaction.txouts:
        txouttotal = txouttotal + txouts.amount

    return txintotal == txouttotal

# validate the coinbase transaction
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

def isValidTxForPool(tx, pool):
    for pooltx in pool:
        for txins in pooltx.txins:
            for txins2 in tx.txins:
                if txins.txoutid == txins2.txoutid and txins.txoutidx == txins2.txoutidx:
                    return False
    return True

def validateTransaction(tx, allUnspentTxOs):
    # id is always correct

    # validate inputs by validating the signature of the signer
    for txins in tx.txins:
        if not txin.validateTxIn(txins, tx, allUnspentTxOs):
            return False # a single failure is a big issue

    # TxOuts are always correct, just check the balancing
    if not validateTransactionBalance(tx, allUnspentTxOs):
        return False

    return True

# validate your array of transactions before making a block
def validateAllTransactions(allTx, allUnspentTxOs, blockIdx):
    if not validateCoinbase(allTx[0], blockIdx):
        return False # immediate termination
    for idx in range(len(allTx)):
        if idx == 0:
            continue
        else:
            if not validateTransaction(allTx[idx], allUnspentTxOs):
                return False
    return True

# VERY IMPORTANT: When you make a block with many transactions, validate all
# using the above function, then you MUST update your global UTxO array as well

def makeCoinbaseTransaction(receiverAddr, blockIdx):
    tx = Transaction([],[])
    newTxIn = txin.TxIn('', blockIdx, '')
    # no id, no signature

    tx.txins = [newTxIn]
    tx.txouts = [txout.TxOut(receiverAddr, COINBASE_AMT)]
    return tx

def processTransactions(transactions, allUTxOs, blockIdx):
    if not validateAllTransactions(transactions, allUTxOs, blockIdx):
        return None
    return updateUnspentTxOs(transactions, allUTxOs)
