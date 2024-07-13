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
import pickle
import os
import threading
from nacl.encoding import HexEncoder
from nacl.encoding import Base64Encoder
from nacl.signing import SigningKey
from nacl.signing import VerifyKey

app = Flask(__name__, static_folder="./app/")
app.debug = True
thisNode = None
killThread = 0

@app.route("/")
def serve():
    return send_from_directory(app.static_folder, "index.html")

@app.route("/start")
def start():
    dicti =  generate()
    startConstantAsyncMine()
    jsonobj = jsonify(dicti)
    jsonobj.headers.add("Access-Control-Allow-Origin", "*")
    return jsonobj

@app.route("/getBalance")
def balance():
    dicti = getBalance()
    jsonobj = jsonify(dicti)
    jsonobj.headers.add("Access-Control-Allow-Origin", "*")
    return jsonobj

@app.route("/mineBlock")
def mineBlock():
    blck = node.generateNextBlock(thisNode)
    if blck is not None:
        thisNode.recentBlockHashs.append(blck.hash) # ok you have received this so don't flood again
        for peer in thisNode.peers:
            endpoint = "http://172.17.0.1:"+peer+"/sendBlock"
            sendObj = {}
            sendObj['block'] = blck.readableObject()
            res = requests.post(endpoint, json=sendObj)
    poolNumber = {"block": blck.readableObject()}
    jsonobj = jsonify(poolNumber)
    jsonobj.headers.add("Access-Control-Allow-Origin", "*")
    return jsonobj

@app.route("/sendBlock", methods=['POST', 'OPTIONS'])
def sendBlock():
    if request.method == "POST":
        receivedData = request.json
        blck = receivedData['block']
        realblock = recreateBlock(blck)

        if realblock.index <= thisNode.blockchain[len(thisNode.blockchain) - 1].index: #received old block, discard
            rawObj = {'accepted': False}
            jsonobj = jsonify(rawObj)
            jsonobj.headers.add("Access-Control-Allow-Origin", "*")
            return jsonobj

        # a good block
        killThread = 1
        floodBlock(realblock)

        if block.validateBlock(thisNode.blockchain[len(thisNode.blockchain)-1],realblock):
            thisNode.blockchain.append(realblock)
            if bc.validateBlockchain(thisNode.blockchain):
                thisNode.blockchain.pop(len(thisNode.blockchain)-1)
                node.addToBlockchain(thisNode, realblock) # allowed!
                killThread = 0
                startConstantAsyncMine() # all values updated, now we can start again
                rawObj = {'accepted': True}
                jsonobj = jsonify(rawObj)
                jsonobj.headers.add("Access-Control-Allow-Origin", "*")
                return jsonobj
            else:
                this.blockchain.pop(len(this.blockchain)-1)

        killThread = 0
        startConstantAsyncMine()
        rawObj = {'accepted': False}
        jsonobj = jsonify(rawObj)
        jsonobj.headers.add("Access-Control-Allow-Origin", "*")
        return jsonobj

    if request.method == "OPTIONS":
        rawObj = {}
        jsonobj = jsonify(rawObj)
        jsonobj.headers.add("Access-Control-Allow-Origin", "*")
        jsonobj.headers.add('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE')
        jsonobj.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        jsonobj.headers.add('Access-Control-Max-Age', '300')
        return jsonobj


@app.route("/getPool")
def poolNumber():
    pool = []
    pool = getPool()
    jsonobj = jsonify(pool)
    jsonobj.headers.add("Access-Control-Allow-Origin", "*")
    return jsonobj

@app.route('/sendTransaction', methods=['POST', 'OPTIONS'])
def result():
    if request.method == "POST":
        receivedData = request.json
        key = receivedData['key']
        amount = int(receivedData['amt'])
        address = receivedData['addr']
        #byte_array = bytearray.fromhex(keys)
        keyBytes = bytes(key, 'utf-8')
        addressBytes = bytes(address, 'utf-8')
        tx1 = makeTransaction(keyBytes, amount, addressBytes)
        if tx1 is not None:
            rawObj = tx1.readableObject()
            thisNode.recentTxId = tx1.id #to prevent flooding infinitely
            for peer in thisNode.peers:
                endpoint = "http://172.17.0.1:"+peer+"/receiveTransaction"
                sendObj = {}
                sendObj['tx'] = rawObj
                res = requests.post(endpoint, json=sendObj)
        rawObj = {}
        jsonobj = jsonify(rawObj)
        jsonobj.headers.add("Access-Control-Allow-Origin", "*")
        return jsonobj

    if request.method == "OPTIONS":
        rawObj = {}
        jsonobj = jsonify(rawObj)
        jsonobj.headers.add("Access-Control-Allow-Origin", "*")
        jsonobj.headers.add('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE')
        jsonobj.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        jsonobj.headers.add('Access-Control-Max-Age', '300')
        return jsonobj

@app.route("/receiveTransaction", methods=['POST', 'OPTIONS'])
def resultTx():
    if request.method == "POST":
        receivedData = request.json
        tx = receivedData
        realTx = recreateTransaction(tx['tx'])
        floodTx(realTx) # flood if you haven't received it
        if realTx is None:
            rawObj = {'accepted': False}
            jsonobj = jsonify(rawObj)
            jsonobj.headers.add("Access-Control-Allow-Origin", "*")
            return jsonobj

        if thisNode.addToPool(realTx, getUnspentTxOut()): #if valid, accepted
            rawObj = {'accepted': True}
            jsonobj = jsonify(rawObj)
            jsonobj.headers.add("Access-Control-Allow-Origin", "*")
            return jsonobj

        rawObj = {'accepted': False}
        jsonobj = jsonify(rawObj)
        jsonobj.headers.add("Access-Control-Allow-Origin", "*")
        return jsonobj

    if request.method == "OPTIONS":
        rawObj = {}
        jsonobj = jsonify(rawObj)
        jsonobj.headers.add("Access-Control-Allow-Origin", "*")
        jsonobj.headers.add('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE')
        jsonobj.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        jsonobj.headers.add('Access-Control-Max-Age', '300')
        return jsonobj

@app.route("/getBlockchain")
def getBlockchain():
    jsonobj = jsonify(getReadableChain())
    jsonobj.headers.add("Access-Control-Allow-Origin", "*")
    return jsonobj

@app.route("/addPeer",  methods=['POST', 'OPTIONS'])
def addAPeer():
    if request.method == "POST":
        receivedData = request.json
        peer = receivedData['peer']
        for apeer in thisNode.peers: #peer exists
            if apeer == peer:
                rawObj = {}
                rawObj['accepted'] = False
                jsonobj = jsonify(rawObj)
                jsonobj.headers.add("Access-Control-Allow-Origin", "*")
                return jsonobj

        thisNode.peers.append(peer)
        rawObj = {}
        rawObj['accepted'] = True
        jsonobj = jsonify(rawObj)
        jsonobj.headers.add("Access-Control-Allow-Origin", "*")
        return jsonobj

    if request.method == "OPTIONS":
        rawObj = {}
        jsonobj = jsonify(rawObj)
        jsonobj.headers.add("Access-Control-Allow-Origin", "*")
        jsonobj.headers.add('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE')
        jsonobj.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        jsonobj.headers.add('Access-Control-Max-Age', '300')
        return jsonobj

@app.route("/getAllPeers") # sender
def getAllPeers():
    jsonobj = jsonify(getAllPeersFromNode())
    jsonobj.headers.add("Access-Control-Allow-Origin", "*")
    return jsonobj

@app.route("/generateNode") # sender
def makeNewConnection():
    port = request.args.get('port')
    jsonobj = jsonify(makeANewConnection(port)) #generation work
    jsonobj.headers.add("Access-Control-Allow-Origin", "*")
    return jsonobj

@app.route("/getAll") # receiver
def copyToNode():
    port = request.args.get('port')
    if port in thisNode.peers:
        jsonobj = jsonify({})
        jsonobj.headers.add("Access-Control-Allow-Origin", "*")
        return jsonobj

    thisNode.peers.append(port)
    chain = getReadableChain() #arr
    utxos = getReadableUnspentTxOut() #arr
    pool = getPool() #arr
    rawObj = {}
    rawObj['blockchain'] = chain
    rawObj['utxos'] = utxos
    rawObj['pool'] = pool
    jsonobj = jsonify(rawObj)
    jsonobj.headers.add("Access-Control-Allow-Origin", "*")
    return jsonobj

@app.route("/receiveAll",  methods=['POST', 'OPTIONS'])
def receiveAll():
    if request.method == "POST":
        receivedData = request.json #if we are not initialized already
        if(len(thisNode.blockchain) == 0 and len(thisNode.transactionPool) == 0 and len(thisNode.utxos) == 0):
            chain = receivedData['blockchain']
            utxos = receivedData['utxos']
            pool = receivedData['pool']
            pChain = recreateBlockchain(chain)
            pUTxOs = recreateUTxOs(utxos)
            pPool = recreatePool(pool)
            thisNode.blockchain = pChain
            thisNode.utxos = pUTxOs
            thisNode.transactionPool = pPool
            startConstantAsyncMine()
        rawObj = {}
        jsonobj = jsonify(rawObj)
        jsonobj.headers.add("Access-Control-Allow-Origin", "*")
        return jsonobj

    if request.method == "OPTIONS":
        rawObj = {}
        jsonobj = jsonify(rawObj)
        jsonobj.headers.add("Access-Control-Allow-Origin", "*")
        jsonobj.headers.add('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE')
        jsonobj.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        jsonobj.headers.add('Access-Control-Max-Age', '300')
        return jsonobj


# Only for the first node ever generated
def start():
    clientKeys = wallet.generateKeyPair()
    client = node.Node(None, clientKeys[1])
    global thisNode
    thisNode = client

    genesisTxIns = [txin.TxIn('', 0, '')]
    # Paying ourselves for starting the chain
    genesisTxOuts = [txout.TxOut(thisNode.walletAddr, 50)]
    genesisTransaction = [transaction.Transaction(genesisTxIns, genesisTxOuts)]

    GENESIS = block.Block(0, datetime.datetime.now().timestamp(), genesisTransaction, None, 19, 0, '')
    block.runMine(GENESIS)
    thisNode.blockchain.append(GENESIS)
    # Basically processing the GENESIS itself
    thisNode.utxos = transaction.processTransactions(thisNode.blockchain[0].data, [], 0)
    return clientKeys[0]

def getReadableUnspentTxOut():
    unspentTxOuts = getUnspentTxOut()
    readableUtxos = []
    for utxo in unspentTxOuts:
        readableUtxos.append(utxo.readableObject())
    return readableUtxos

def getUnspentTxOut():
    copyUTxOs = []
    for utxos in thisNode.utxos:
        newutxo = utxo.UTxO(utxos.txoutid, utxos.txoutidx, utxos.address, utxos.amount)
        copyUTxOs.append(newutxo)
    return copyUTxOs

def setUnspentTxOut(arr):
    thisNode.utxos = arr

def getGenesis():
    return thisNode.blockchain[0]

#def testPayServer():
    #nodes[0].sendTransaction(nodes[1].walletAddr, 10, clientPrivateKey[0])
    #node.generateNextBlock(nodes[1])
    #return wallet.getBalance(nodes[1].walletAddr, getUnspentTxOut())

def generate():
    privateKey = start()
    returndetails = {'clientKey': str(privateKey), 'clientAddr': str(thisNode.walletAddr)}
    return returndetails

def getPool():
    fixedPool = []
    for tx in thisNode.transactionPool:
        fixedPool.append(tx.readableObject())
    return fixedPool

def getBalance():
    money = wallet.getBalance(thisNode.walletAddr, getUnspentTxOut())
    returndetails = {'amount': money}
    return returndetails

def makeTransaction(key, amt, addr):
    signkey = SigningKey(key, HexEncoder)
    verkey = signkey.verify_key
    addrToMatch = verkey.encode(HexEncoder)
    if not thisNode.walletAddr == addrToMatch:
        return {}
    tx = {}
    try:
        tx = thisNode.sendTransaction(addr, amt, key)
        return tx
    except Exception as e:
        print(e)
        return None


def getReadableChain():
    read = []
    chain = thisNode.blockchain
    for b in chain:
        read.append(b.readableObject())
    res = {}
    res['chain'] = read
    return res

def getAllPeersFromNode():
    return thisNode.peers

def makeANewConnection(port):
    #spawn with a peer
    clientKeys = ["", ""]
    donotadd = 0
    global thisNode
    if thisNode is None:
        clientKeys = wallet.generateKeyPair()
        client = node.Node(None, clientKeys[1])
        thisNode = client
    else: # an additional peer or probably the same one again
        for aport in thisNode.peers:
            if aport == port:
                donotadd = 1
                break
    if donotadd == 0:
        thisNode.peers.append(port)
    retObj = {}
    retObj['clientKey'] = str(clientKeys[0])
    retObj['clientAddr'] = str(clientKeys[1])
    return retObj

def recreateBlock(b):
    dataArr = b['data']
    emptyTxArr = []
    for tx in dataArr:
        realtx = recreateTransaction(tx)
        emptyTxArr.append(realtx)
    #all transactions fixed
    idx = int(b['index'])
    time = float(b['timestamp'])
    prevHash = bytes(b['previoushash'], 'utf-8')
    difficulty = int(b['difficulty'])
    nonce = int(b['nonce'])
    hash = bytes(b['hash'], 'utf-8')
    realBlock = block.Block(idx, time, emptyTxArr, prevHash, difficulty, nonce, hash)
    return realBlock

def recreateBlockchain(chain):
    blockArr = chain['chain']

    realChain = []
    for b in blockArr:
        dataArr = b['data']
        emptyTxArr = []
        for tx in dataArr:
            realtx = recreateTransaction(tx)
            emptyTxArr.append(realtx)
        #all transactions fixed
        idx = int(b['index'])
        time = float(b['timestamp'])
        prevHash = bytes(b['previoushash'], 'utf-8')
        difficulty = int(b['difficulty'])
        nonce = int(b['nonce'])
        hash = bytes(b['hash'], 'utf-8')
        realBlock = block.Block(idx, time, emptyTxArr, prevHash, difficulty, nonce, hash)
        realChain.append(realBlock)
    return realChain

def recreateUTxOs(utxos):
    utxoarr = []
    for autxo in utxos:
        realutxo = recreateUTxO(autxo)
        utxoarr.append(realutxo)
    return utxoarr

def recreatePool(pool):
    txarr = []
    for tx in pool:
        realtx = recreateTransaction(tx)
        txarr.append(realtx)
    return txarr

def recreateTransaction(tx):
    txoutarr = []
    txinarr = []
    try:
        for txouts in tx['txouts']:
            realtxout = recreateTxOut(txouts)
            txoutarr.append(realtxout)
    except Exception as e:
        return None
    try:
        for txins in tx['txins']:
            realtxin = recreateTxIn(txins)
            txinarr.append(realtxin)
    except:
        return None
    try:
        id = bytes(tx['id'], 'utf-8')
    except:
        return None
    return transaction.Transaction(txinarr, txoutarr, id)

def recreateTxIn(atxin):
    infile = open(atxin['signature'],'rb')
    new_dict = pickle.load(infile)
    infile.close()
    os.remove(atxin['signature'])
    sign = new_dict
    txoutid = bytes(atxin['txoutid'], 'utf-8')
    txoutidx = int(atxin['txoutidx'])
    return txin.TxIn(txoutid, txoutidx, sign)

def recreateTxOut(atxout):
    addr = bytes(atxout['address'], 'utf-8')
    amt = int(atxout['amount'])
    return txout.TxOut(addr, amt)

def recreateUTxO(autxo):
    addr = bytes(autxo['address'], 'utf-8')
    amt = int(autxo['amount'])
    id = bytes(autxo['txoutid'], 'utf-8')
    idx = int(autxo['txoutidx'])
    return utxo.UTxO(id, idx, addr, amt)

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
        thisNode.recentTxId = tx.id # ok you have received this so don't flood again
        for peer in thisNode.peers:
            endpoint = "http://172.17.0.1:"+peer+"/receiveTransaction"
            sendObj = {}
            sendObj['tx'] = tx.readableObject()
            res = requests.post(endpoint, json=sendObj)

def floodBlock(blck):
    if not haveReceivedBlock(blck) and blck is not None:
        thisNode.recentBlockHashs.append(blck.hash)# ok you have received this so don't flood again
        for peer in thisNode.peers:
            endpoint = "http://172.17.0.1:"+peer+"/sendBlock"
            sendObj = {}
            sendObj['block'] = blck.readableObject()
            res = requests.post(endpoint, json=sendObj)

def startConstantAsyncMine():
    global thisNode
    proc = threading.Thread(target=minePool, args=(thisNode,))
    proc.start() # starting processing

def minePool(n):
    while True:
        if killThread == 1: #received a new block, kill this
            break
        b = node.generateNextBlock(n)
        if b is not None: # failed to get it in time
            floodBlock(b) # otherwise flood
