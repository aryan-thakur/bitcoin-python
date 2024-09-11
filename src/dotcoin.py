import time
from flask import Flask, request, jsonify, make_response, send_from_directory
import blockchain as bc
import json
import block
import transaction
import utxo
import txin
import txout
import datetime
import requests
import node
import wallet
from recreate import *
import threading
from nacl.encoding import HexEncoder
from nacl.encoding import Base64Encoder
from nacl.signing import SigningKey
from nacl.signing import VerifyKey

app = Flask(__name__, static_folder="./app/")
app.debug = True
thisNode = None
stop_event = threading.Event()
proc = None


@app.route("/")
def serve():
    return send_from_directory(app.static_folder, "index.html")


## GENERATION ENDPOINTS


# The initial generation of the blockchain
@app.route("/start")
def start():
    dict_data = generate()
    startConstantAsyncMine()
    jsonobj = jsonify(dict_data)
    jsonobj.headers.add("Access-Control-Allow-Origin", "*")
    return jsonobj


# Generates a node that is not the genesis node
@app.route("/generateNode")  # sender
def makeNewConnection():
    port = request.args.get("port")
    jsonobj = jsonify(
        makeANewConnection(port)
    )  # generation work, either thisNode is already setup, or its not
    jsonobj.headers.add("Access-Control-Allow-Origin", "*")
    return jsonobj


# Get all the data from a generated node
@app.route("/getAll")  # receiver
def copyToNode():
    port = request.args.get("port")

    # if port is a peer, get nothing
    if port in thisNode.peers:
        jsonobj = jsonify({})
        jsonobj.headers.add("Access-Control-Allow-Origin", "*")
        return jsonobj

    thisNode.peers.append(port)
    chain = getReadableChain()
    utxos = getReadableUnspentTxOut()
    pool = getPool()  #
    rawObj = {}
    rawObj["blockchain"] = chain
    rawObj["utxos"] = utxos
    rawObj["pool"] = pool
    jsonobj = jsonify(rawObj)
    jsonobj.headers.add("Access-Control-Allow-Origin", "*")
    return jsonobj


# using getAll, post it to the new peer
@app.route("/receiveAll", methods=["POST", "OPTIONS"])
def receiveAll():
    if request.method == "POST":
        receivedData = request.json  # if we are not initialized already
        if (
            len(thisNode.blockchain) == 0
            and len(thisNode.transactionPool) == 0
            and len(thisNode.utxos) == 0
        ):
            chain = receivedData["blockchain"]
            utxos = receivedData["utxos"]
            pool = receivedData["pool"]
            pChain = recreateBlockchain(chain)
            pUTxOs = recreateUTxOs(utxos)
            pPool = recreatePool(pool)
            thisNode.blockchain = pChain
            thisNode.utxos = pUTxOs
            thisNode.transactionPool = pPool
            startConstantAsyncMine()  # start the mining thread too

        rawObj = {}
        jsonobj = jsonify(rawObj)
        jsonobj.headers.add("Access-Control-Allow-Origin", "*")
        return jsonobj

    if request.method == "OPTIONS":
        rawObj = {}
        jsonobj = jsonify(rawObj)
        jsonobj.headers.add("Access-Control-Allow-Origin", "*")
        jsonobj.headers.add("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE")
        jsonobj.headers.add("Access-Control-Allow-Headers", "Content-Type")
        jsonobj.headers.add("Access-Control-Max-Age", "300")
        return jsonobj


## BLOCK ENDPOINTS


# Tries to generate the next block
@app.route("/mineBlock")
def mineBlock():
    blck = thisNode.generateNextBlock()
    if blck is not None:  # failed to get it in time
        floodBlock(blck)  # otherwise flood

    poolNumber = {"block": blck.readableObject()}
    jsonobj = jsonify(poolNumber)
    jsonobj.headers.add("Access-Control-Allow-Origin", "*")
    return jsonobj


# Endpoint that receives a new block
@app.route("/sendBlock", methods=["POST", "OPTIONS"])
def sendBlock():
    if request.method == "POST":
        receivedData = request.json
        blck = receivedData["block"]
        realblock = recreateBlock(blck)

        # Simplified bitcoin works on indices, not timestamps
        if realblock.index <= thisNode.blockchain[len(thisNode.blockchain) - 1].index:
            rawObj = {
                "accepted": False,
                "chain": getReadableChain(),
                "utxos": getReadableUnspentTxOut(),
            }
            jsonobj = jsonify(rawObj)
            jsonobj.headers.add("Access-Control-Allow-Origin", "*")
            return jsonobj

        # a good, new block so kill our mining thread and flood it to our peers
        stopConstantAsyncMine()

        # validate it, if passes, add to our blockchain
        if realblock.validateBlock(thisNode.blockchain[len(thisNode.blockchain) - 1]):
            thisNode.blockchain.append(realblock)

            # validate our blockchain now
            if bc.validateBlockchain(thisNode.blockchain):
                thisNode.blockchain.pop()
                thisNode.addToBlockchain(
                    realblock
                )  # allowed now, so update values and all to blockchain
                floodBlock(realblock)
                startConstantAsyncMine()  # all values updated, now we can start our async mine again

                rawObj = {"accepted": True}
                jsonobj = jsonify(rawObj)
                jsonobj.headers.add("Access-Control-Allow-Origin", "*")
                return jsonobj

            else:
                thisNode.blockchain.pop()

        startConstantAsyncMine()

        rawObj = {
            "accepted": False,
            "chain": getReadableChain(),
            "utxos": getReadableUnspentTxOut(),
        }
        jsonobj = jsonify(rawObj)
        jsonobj.headers.add("Access-Control-Allow-Origin", "*")
        return jsonobj

    if request.method == "OPTIONS":
        rawObj = {}
        jsonobj = jsonify(rawObj)
        jsonobj.headers.add("Access-Control-Allow-Origin", "*")
        jsonobj.headers.add("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE")
        jsonobj.headers.add("Access-Control-Allow-Headers", "Content-Type")
        jsonobj.headers.add("Access-Control-Max-Age", "300")
        return jsonobj


## TRANSACTION ENDPOINTS


@app.route("/sendTransaction", methods=["POST", "OPTIONS"])
def result():
    if request.method == "POST":
        receivedData = request.json
        key = receivedData["key"]
        amount = int(receivedData["amt"])
        address = receivedData["addr"]
        keyBytes = bytes(key, "utf-8")
        addressBytes = bytes(address, "utf-8")
        tx1 = makeTransaction(
            keyBytes, amount, addressBytes
        )  # calls a function to make a transaction

        if tx1 is not None:
            rawObj = tx1.readableObject()
            thisNode.recentTxId = tx1.id  # to prevent flooding infinitely
            for peer in thisNode.peers:
                endpoint = "http://172.17.0.1:" + peer + "/receiveTransaction"
                sendObj = {}
                sendObj["tx"] = rawObj
                res = requests.post(endpoint, json=sendObj)

        rawObj = {}
        jsonobj = jsonify(rawObj)
        jsonobj.headers.add("Access-Control-Allow-Origin", "*")
        return jsonobj

    if request.method == "OPTIONS":
        rawObj = {}
        jsonobj = jsonify(rawObj)
        jsonobj.headers.add("Access-Control-Allow-Origin", "*")
        jsonobj.headers.add("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE")
        jsonobj.headers.add("Access-Control-Allow-Headers", "Content-Type")
        jsonobj.headers.add("Access-Control-Max-Age", "300")
        return jsonobj


@app.route("/receiveTransaction", methods=["POST", "OPTIONS"])
def resultTx():
    if request.method == "POST":
        receivedData = request.json
        tx = receivedData
        realTx = recreateTransaction(tx["tx"])
        floodTx(realTx)  # flood if you haven't received it, will check for receive

        if realTx is None:
            rawObj = {"accepted": False}
            jsonobj = jsonify(rawObj)
            jsonobj.headers.add("Access-Control-Allow-Origin", "*")
            return jsonobj

        if thisNode.addToPool(realTx, getUnspentTxOut()):  # if valid, accepted
            rawObj = {"accepted": True}
            jsonobj = jsonify(rawObj)
            jsonobj.headers.add("Access-Control-Allow-Origin", "*")
            return jsonobj

        rawObj = {"accepted": False}
        jsonobj = jsonify(rawObj)
        jsonobj.headers.add("Access-Control-Allow-Origin", "*")
        return jsonobj

    if request.method == "OPTIONS":
        rawObj = {}
        jsonobj = jsonify(rawObj)
        jsonobj.headers.add("Access-Control-Allow-Origin", "*")
        jsonobj.headers.add("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE")
        jsonobj.headers.add("Access-Control-Allow-Headers", "Content-Type")
        jsonobj.headers.add("Access-Control-Max-Age", "300")
        return jsonobj


## GETTERS


# Gets your balance
@app.route("/getBalance")
def balance():
    dict_data = getBalance()
    jsonobj = jsonify(dict_data)
    jsonobj.headers.add("Access-Control-Allow-Origin", "*")
    return jsonobj


# Simply gets our transaction pool
@app.route("/getPool")
def poolNumber():
    pool = []
    pool = getPool()
    jsonobj = jsonify(pool)
    jsonobj.headers.add("Access-Control-Allow-Origin", "*")
    return jsonobj


# Simply gets the blockchain
@app.route("/getBlockchain")
def getBlockchain():
    jsonobj = jsonify(getReadableChain())
    jsonobj.headers.add("Access-Control-Allow-Origin", "*")
    return jsonobj


# Simply gets all peers
@app.route("/getAllPeers")
def getAllPeers():
    jsonobj = jsonify(thisNode.peers)
    jsonobj.headers.add("Access-Control-Allow-Origin", "*")
    return jsonobj


## MISCELLANEOUS


# Adds a peer
@app.route("/addPeer", methods=["POST", "OPTIONS"])
def addAPeer():
    if request.method == "POST":
        receivedData = request.json
        peer = receivedData["peer"]
        for apeer in thisNode.peers:  # if peer already exists
            if apeer == peer:
                rawObj = {}
                rawObj["accepted"] = False
                jsonobj = jsonify(rawObj)
                jsonobj.headers.add("Access-Control-Allow-Origin", "*")
                return jsonobj

        thisNode.peers.append(peer)
        rawObj = {}
        rawObj["accepted"] = True
        jsonobj = jsonify(rawObj)
        jsonobj.headers.add("Access-Control-Allow-Origin", "*")
        return jsonobj

    if request.method == "OPTIONS":
        rawObj = {}
        jsonobj = jsonify(rawObj)
        jsonobj.headers.add("Access-Control-Allow-Origin", "*")
        jsonobj.headers.add("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE")
        jsonobj.headers.add("Access-Control-Allow-Headers", "Content-Type")
        jsonobj.headers.add("Access-Control-Max-Age", "300")
        return jsonobj


## HELPERS


# Only for the first node ever generated, refernced from generate ()
def start():
    clientKeys = wallet.generateKeyPair()
    client = node.Node(None, clientKeys[1])
    global thisNode
    thisNode = client

    genesisTxIns = [txin.TxIn("", 0, "")]
    # Paying ourselves for starting the blockchain
    genesisTxOuts = [txout.TxOut(thisNode.walletAddr, 50)]
    genesisTransaction = [transaction.Transaction(genesisTxIns, genesisTxOuts)]

    # GENESIS block creation and mining
    GENESIS = block.Block(
        0, datetime.datetime.now().timestamp(), genesisTransaction, None, 19, 0, ""
    )
    GENESIS.runMine()

    thisNode.blockchain.append(GENESIS)

    # Basically processing the GENESIS itself
    thisNode.utxos = transaction.processTransactions(thisNode.blockchain[0].data, [], 0)
    return clientKeys[0]


def generate():
    """
    Helper function to generate the first node
    """
    privateKey = start()
    returndetails = {
        "clientKey": str(privateKey),
        "clientAddr": str(thisNode.walletAddr),
    }
    return returndetails


def makeTransaction(key, amt, addr):
    """
    Helper function to make a transaction
    """
    signkey = SigningKey(key, HexEncoder)
    verkey = signkey.verify_key
    addrToMatch = verkey.encode(HexEncoder)

    if not thisNode.walletAddr == addrToMatch:
        return {}
    tx = {}

    try:
        tx = thisNode.sendTransaction(
            addr, amt, key
        )  # will only add to your pool if valid
        return tx

    except Exception as e:
        return None


def makeANewConnection(port):
    """
    Helper function to make a connection, or generate a non-genesis node
    """
    clientKeys = ["", ""]
    donotadd = 0
    global thisNode
    if thisNode is None:  # generating when a genesis node already exists
        clientKeys = wallet.generateKeyPair()
        client = node.Node(None, clientKeys[1])
        thisNode = client
    else:  # an additional peer or probably the same one again
        for aport in thisNode.peers:
            if aport == port:
                donotadd = 1  # don't add again
                break
    if donotadd == 0:
        thisNode.peers.append(port)
    retObj = {}
    retObj["clientKey"] = str(clientKeys[0])
    retObj["clientAddr"] = str(clientKeys[1])
    return retObj


## GETTER HELPERS


def getReadableChain():
    """
    Returns a readable blockchain
    """
    read = []
    chain = thisNode.blockchain
    for b in chain:
        read.append(b.readableObject())
    res = {}
    res["chain"] = read
    return res


def getBalance():
    """
    Finds balance using your public key/ wallet address and your uTxO array (copy)
    """
    money = wallet.getBalance(thisNode.walletAddr, getUnspentTxOut())
    returndetails = {"amount": money}
    return returndetails


def getGenesis():
    return thisNode.blockchain[0]


def getPool():
    """
    Returns current transaction pool
    """
    fixedPool = []
    for tx in thisNode.transactionPool:
        fixedPool.append(tx.readableObject())
    return fixedPool


def getReadableUnspentTxOut():
    """
    Get a readable version of your utxo array
    """
    unspentTxOuts = getUnspentTxOut()
    readableUtxos = []
    for utxo in unspentTxOuts:
        readableUtxos.append(utxo.readableObject())
    return readableUtxos


def getUnspentTxOut():
    """
    Helper to create your utxo array
    """
    copyUTxOs = []
    for utxos in thisNode.utxos:
        newutxo = utxo.UTxO(utxos.txoutid, utxos.txoutidx, utxos.address, utxos.amount)
        copyUTxOs.append(newutxo)
    return copyUTxOs


def setUnspentTxOut(arr):
    thisNode.utxos = arr


## FLOODING HELPERS


def haveReceivedTx(tx):
    global thisNode
    if thisNode.recentTxId == tx.id:
        return True
    return False


def haveReceivedBlock(blck):
    global thisNode
    if blck.hash in thisNode.recentBlockHashs:
        return True
    return False


def floodTx(tx):
    if not haveReceivedTx(tx) and tx is not None:
        thisNode.recentTxId = tx.id  # ok you have received this so don't flood again
        for peer in thisNode.peers:
            endpoint = "http://172.17.0.1:" + peer + "/receiveTransaction"
            sendObj = {}
            sendObj["tx"] = tx.readableObject()
            res = requests.post(endpoint, json=sendObj)


def floodBlock(blck):
    if not haveReceivedBlock(blck) and blck is not None:
        # ok you have received this so don't flood again
        thisNode.recentBlockHashs.append(blck.hash)
        # flood
        for peer in thisNode.peers:
            endpoint = "http://172.17.0.1:" + peer + "/sendBlock"
            sendObj = {}
            sendObj["block"] = blck.readableObject()
            res = requests.post(endpoint, json=sendObj)
            res_obj = res.json()

            # failed to push blockchain, regroup
            if res_obj and not res_obj["accepted"]:
                thisNode.blockchain = recreateBlockchain(res_obj["chain"])
                thisNode.utxos = recreateUTxOs(res_obj["utxos"])
                return  # kills this iteration


## THREADING HELPERS


def minePool():
    global thisNode
    while not stop_event.is_set():
        b = thisNode.generateNextBlock()
        if b is not None:
            floodBlock(b)
        else:
            print("Failed to generate block in time.")
        time.sleep(1)  # Simulate some delay

    return


def startConstantAsyncMine():
    """
    Runs the async mining operation, the heart of Dotcoin
    """
    global proc, stop_event
    if proc is not None and proc.is_alive():
        print("Mining is already running.")
        return

    stop_event.clear()  # Reset the stop_event to ensure the thread runs
    proc = threading.Thread(target=minePool, args=())
    proc.start()


def stopConstantAsyncMine():
    global proc, stop_event
    if proc is not None and proc.is_alive():
        stop_event.set()  # Signal the thread to stop
        proc.join()  # Wait for the thread to finish
        proc = None  # Reset the proc after it finishes
    else:
        print("No mining process to stop.")
