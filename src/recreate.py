import pickle, os
import transaction, txin, txout, utxo, block


def recreateBlock(b):
    """
    Takes in a json representation of a block and returns a block object
    """
    dataArr = b["data"]
    emptyTxArr = []
    for tx in dataArr:
        realtx = recreateTransaction(tx)
        emptyTxArr.append(realtx)
    # all transactions fixed
    idx = int(b["index"])
    time = float(b["timestamp"])
    prevHash = bytes(b["previoushash"], "utf-8")
    difficulty = int(b["difficulty"])
    nonce = int(b["nonce"])
    hash = bytes(b["hash"], "utf-8")
    realBlock = block.Block(idx, time, emptyTxArr, prevHash, difficulty, nonce, hash)
    return realBlock


def recreateBlockchain(chain):
    """
    Takes in a json representation of a blockchain and returns a block list
    """
    blockArr = chain["chain"]

    realChain = []
    for b in blockArr:
        dataArr = b["data"]
        emptyTxArr = []
        for tx in dataArr:
            realtx = recreateTransaction(tx)
            emptyTxArr.append(realtx)
        # all transactions fixed
        idx = int(b["index"])
        time = float(b["timestamp"])
        prevHash = bytes(b["previoushash"], "utf-8")
        difficulty = int(b["difficulty"])
        nonce = int(b["nonce"])
        hash = bytes(b["hash"], "utf-8")
        realBlock = block.Block(
            idx, time, emptyTxArr, prevHash, difficulty, nonce, hash
        )
        realChain.append(realBlock)
    return realChain


def recreateUTxOs(utxos):
    """
    Takes in a json representation of a UTxO list and returns a UTxO list
    """
    utxoarr = []
    for autxo in utxos:
        realutxo = recreateUTxO(autxo)
        utxoarr.append(realutxo)
    return utxoarr


def recreatePool(pool):
    """
    Takes in a json representation of a transaction pool and returns a list of transactions
    """
    txarr = []
    for tx in pool:
        realtx = recreateTransaction(tx)
        txarr.append(realtx)
    return txarr


def recreateTransaction(tx):
    """
    Takes in a json representation of a transaction  and returns a transaction
    """
    txoutarr = []
    txinarr = []
    try:
        for txouts in tx["txouts"]:
            realtxout = recreateTxOut(txouts)
            txoutarr.append(realtxout)
    except Exception as e:
        return None
    try:
        for txins in tx["txins"]:
            realtxin = recreateTxIn(txins)
            txinarr.append(realtxin)
    except:
        return None
    try:
        id = bytes(tx["id"], "utf-8")
    except:
        return None
    return transaction.Transaction(txinarr, txoutarr, id)


def recreateTxIn(atxin):
    """
    Takes in a json representation of a transaction input and returns a txin object
    """
    infile = open(atxin["signature"], "rb")
    new_dict = pickle.load(infile)
    infile.close()
    os.remove(atxin["signature"])
    sign = new_dict
    txoutid = bytes(atxin["txoutid"], "utf-8")
    txoutidx = int(atxin["txoutidx"])
    return txin.TxIn(txoutid, txoutidx, sign)


def recreateTxOut(atxout):
    """
    Takes in a json representation of a transaction output and returns a txout object
    """
    addr = bytes(atxout["address"], "utf-8")
    amt = int(atxout["amount"])
    return txout.TxOut(addr, amt)


def recreateUTxO(autxo):
    """
    Takes in a json representation of an unspent transaciton output pool and returns a UTxO object
    """
    addr = bytes(autxo["address"], "utf-8")
    amt = int(autxo["amount"])
    id = bytes(autxo["txoutid"], "utf-8")
    idx = int(autxo["txoutidx"])
    return utxo.UTxO(id, idx, addr, amt)
