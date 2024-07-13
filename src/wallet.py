from nacl.encoding import Base64Encoder
from nacl.encoding import HexEncoder
from nacl.signing import SigningKey
from nacl.signing import VerifyKey
import nacl.utils
from nacl.public import PrivateKey
import txin
import txout
import utxo
import transaction

def generateKeyPair():
    privateKeyObj = SigningKey.generate()
    publicKeyObj = privateKeyObj.verify_key
    privateKey = privateKeyObj.encode(encoder=nacl.encoding.HexEncoder)
    # get it back: signing_key = SigningKey(privateKeyObj, encoder=nacl.encoding.HexEncoder)
    # Real public key
    publicKey = publicKeyObj.encode(encoder=nacl.encoding.HexEncoder)
    return [privateKey, publicKey]

def keyPairToStr(keyPair):
    return str(keyPair[0]) + " " + str(keyPair[1])

# Wallet balance
def getBalance(address, unspentTxOuts):
    sum = 0
    for utxo in unspentTxOuts:
        if utxo.address == address:
            sum = sum + utxo.amount
    return sum

# TxIns created from your uTxOs, first index is balance to be returned as uTxO
def getTxOutSplit(amount, myUnspentTxOuts):
    amt = 0
    unspentTxOuts = []
    for utxo in myUnspentTxOuts:
        unspentTxOuts.append(utxo)
        amt = amt + utxo.amount
        if amt >= amount:
            return [convertUTxOsToTxIns(unspentTxOuts), amt-amount] #at min it will be 0, all unsigned
    return [[], -1]

def convertToTxIn(uTxO):
    newTxIn = txin.TxIn(uTxO.txoutid, uTxO.txoutidx, '') #unsigned
    return newTxIn

# Critical function that converts TxOuts (uTxOs) of previous transactions
# to TxIns of new transactions

def convertUTxOsToTxIns(unspentTxOuts):
    txInArr = []
    for utxo in unspentTxOuts:
        txInArr.append(convertToTxIn(utxo))
    return txInArr

# Critical function for making the TxOuts of a transaction, at least one for receiver
# second one to pay excess back to self
def createTxOuts(receiverAddr, senderAddr, amt, leftover):
    newTxOut = txout.TxOut(receiverAddr, amt)
    if leftover == 0:
        return [newTxOut]
    else:
        myTxOut = txout.TxOut(senderAddr, leftover)
        return [newTxOut, myTxOut]

# remove used up uTxOs from the uTxO pool
def filterFromPool(pool, allUTxOs):
    for tx in pool: #every transaction
        for txIn in tx.txins: #look at all txins
            i = 0
            for utxo in allUTxOs: #search all utxos
                # if the TxIn matches one, remove
                if txIn.txoutid == utxo.txoutid and txIn.txoutidx == utxo.txoutidx:
                    allUTxOs.pop(i)
                    break
                i = i + 1

    return


def createTransaction(receiverAddr, myKeyPair, amount, unspentTxOuts, transactionPool):
    myAddr = myKeyPair[1] # public key in hex is address here
    myUnspentTxOuts = [] # filter uTxOs belonging to my address
    for utxo in unspentTxOuts:
        if utxo.address == myAddr:
            myUnspentTxOuts.append(utxo)


    #you do NOT own those uTxOs that are in the transactionPool (double spending)
    filterFromPool(transactionPool, myUnspentTxOuts)
    
    txOutSplit = getTxOutSplit(amount, myUnspentTxOuts)
    # list of txins on left, list of txouts on right
    tx = transaction.Transaction(txOutSplit[0], createTxOuts(receiverAddr, myAddr, amount, txOutSplit[1]))
    # all these txins are from "my" address so I need to sign them
    privateKeyObj = SigningKey(myKeyPair[0], HexEncoder)

    # Sign all txins
    i = 0
    for txins in tx.txins:
        txins.signature = txin.signTxIn(tx, i, privateKeyObj, unspentTxOuts)
        i = i + 1

    return tx
