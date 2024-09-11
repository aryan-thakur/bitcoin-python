from nacl.encoding import Base64Encoder
from nacl.encoding import HexEncoder
from nacl.signing import SigningKey
from nacl.signing import VerifyKey
import nacl.utils
from nacl.public import PrivateKey
import txin, txout, utxo, transaction

# Static file


def generateKeyPair():
    """
    Generates and returns the private-public key pair
    """
    privateKeyObj = SigningKey.generate()
    publicKeyObj = privateKeyObj.verify_key
    privateKey = privateKeyObj.encode(encoder=nacl.encoding.HexEncoder)

    # Real public key
    publicKey = publicKeyObj.encode(encoder=nacl.encoding.HexEncoder)
    return [privateKey, publicKey]


def keyPairToStr(keyPair):
    return str(keyPair[0]) + " " + str(keyPair[1])


def getBalance(address, unspentTxOuts):
    """
    Returns the wallet balance referencing the uTxO pool
    """
    sum = 0
    for utxo in unspentTxOuts:
        if utxo.address == address:
            sum = sum + utxo.amount
    return sum


def getTxOutSplit(amount, myUnspentTxOuts):
    """
    References your uTxOs and creates TxIns equal to the amount passed in as a parameter, creates a uTxO of the remaining excess
    """
    amt = 0
    unspentTxOuts = []
    for utxo in myUnspentTxOuts:
        unspentTxOuts.append(utxo)
        amt = amt + utxo.amount
        if amt >= amount:
            return [
                convertUTxOsToTxIns(unspentTxOuts),  # TxIns to be sent
                amt - amount,  # left over
            ]  # at min it will be 0, all unsigned
    return [[], -1]


def convertToTxIn(uTxO):
    newTxIn = txin.TxIn(uTxO.txoutid, uTxO.txoutidx, "")  # unsigned TxIn
    return newTxIn


def convertUTxOsToTxIns(unspentTxOuts):
    """
    Critical function that converts uTxOs of previous transactions to TxIns of new transactions
    """
    txInArr = []
    for utxo in unspentTxOuts:
        txInArr.append(convertToTxIn(utxo))
    return txInArr


def createTxOuts(receiverAddr, senderAddr, amt, leftover):
    """
    Critical function for making the TxOuts of a transaction, at least one for receiver second one to pay excess back to self
    Follows the getTxOutSplit() function, that returns TxIns and an amount to pay (amt)
    """
    newTxOut = txout.TxOut(receiverAddr, amt)
    if leftover == 0:
        return [newTxOut]
    else:
        myTxOut = txout.TxOut(senderAddr, leftover)
        return [newTxOut, myTxOut]


def filterFromPool(pool, allUTxOs):
    """
    Remove used up uTxOs from the uTxO pool
    """
    for tx in pool:  # every transaction
        for txIn in tx.txins:  # look at all txins
            i = 0
            for utxo in allUTxOs:  # search all utxos
                # if the TxIn matches one, remove
                if txIn.txoutid == utxo.txoutid and txIn.txoutidx == utxo.txoutidx:
                    allUTxOs.pop(i)
                    break
                i = i + 1
    return


def createTransaction(receiverAddr, myKeyPair, amount, unspentTxOuts, transactionPool):
    """
    Create a transaction, find your uTxOs, get the correct split, make TxIns, make TxOuts and sign the TxIns
    """
    myAddr = myKeyPair[1]  # public key in hex is address here
    myUnspentTxOuts = []  # filter uTxOs belonging to my address
    for utxo in unspentTxOuts:
        if utxo.address == myAddr:
            myUnspentTxOuts.append(utxo)  # my uTxOs

    # you do NOT own those uTxOs that are in the transactionPool (double spending)
    filterFromPool(transactionPool, myUnspentTxOuts)

    txOutSplit = getTxOutSplit(amount, myUnspentTxOuts)
    # list of txins on left (coming from old uTxOs), list of txouts on right (2)
    tx = transaction.Transaction(
        txOutSplit[0], createTxOuts(receiverAddr, myAddr, amount, txOutSplit[1])
    )
    # all these txins are from "my" address so I need to sign them
    privateKeyObj = SigningKey(myKeyPair[0], HexEncoder)

    # Sign all txins proving they all are yours
    i = 0
    for txins in tx.txins:
        txins.signature = txin.signTxIn(tx, i, privateKeyObj, unspentTxOuts)
        i = i + 1

    return tx
