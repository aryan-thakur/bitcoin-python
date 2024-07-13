from nacl.encoding import Base64Encoder
from nacl.hash import sha256
import datetime
import base64
import transaction
import dotcoin as dc

# Note that you can initialize the nonce as any number initially, the hash will
# be calculated accordingly. Both, the hash and nonce are not final until the
# block is mined.

class Block:
    def __init__(self, _index, _timestamp, _data, _previousHash, _difficulty, _nonce, _hash):
        self.index = _index
        self.timestamp = _timestamp
        self.data = _data
        self.hash = _hash
        self.previousHash = _previousHash
        self.difficulty = _difficulty
        self.nonce = _nonce

    def readableObject(self):
        rep = {}
        rep['index'] = self.index
        rep['timestamp'] = self.timestamp
        rep['hash'] = str(self.hash)[2:-1]
        if self.previousHash == None:
            rep['previoushash'] = "NULL"
        else:
            rep['previoushash'] = str(self.previousHash)[2:-1]
        rep['difficulty'] = self.difficulty
        rep['nonce'] = self.nonce
        txs = []
        for tx in self.data:
            txs.append(tx.readableObject())
        rep['data'] = txs
        return rep

# It is worth noting that in this coin, all the hashes are encoded in Base64

def isValidBlockStructure(block):
    return type(block.index) == int and type(block.timestamp) == float and type(block.hash) == bytes and type(block.previousHash) == bytes

def validateBlock(prev, cur):
        # checks data types
    if not isValidBlockStructure(cur):
        return False
        # is this actually the immediate next block?
    elif cur.index != prev.index + 1:
        return False
        # does the current block's previousHash match the previous block's hash?
        # no need to convert to utf8
    elif cur.previousHash != prev.hash:
        return False

    elif isValidDifficulty(cur.hash, cur.difficulty) == False:
        return False
        
        # checks if the current block's hash is correct
    #elif sha256((str.encode(str(cur.index)+cur.previousHash.decode("utf-8")+str(cur.timestamp)+str(cur.data)+str(cur.difficulty)+str(cur.nonce))), Base64Encoder) != cur.hash:
        #return False
    return True

def validateGenesis(block):
    GENESIS = dc.getGenesis()
    if block.index == GENESIS.index and block.timestamp == GENESIS.timestamp and block.hash == GENESIS.hash and block.previousHash == GENESIS.previousHash and block.data == GENESIS.data:
        return True
    return False

def isValidDifficulty(hash: bytes, difficulty: int):
    decodedHash = base64.decodebytes(hash)
    binHashStr = "".join(["{:08b}".format(x) for x in decodedHash])

    difficultyStr = ""
    for i in range(difficulty):
        difficultyStr = difficultyStr + '0'

    return binHashStr.startswith(difficultyStr)

def calculateHash(index, previousHash, timestamp, data, difficulty, nonce):
    if index != 0:
        return sha256((str.encode(str(index)+previousHash.decode("utf-8")+str(timestamp)+str(data)+str(difficulty)+str(nonce))), Base64Encoder)
    else:
        return sha256((str.encode(str(index)+str(timestamp)+str(data)+str(difficulty)+str(nonce))), Base64Encoder)

# this function will effectively 'mine' a block based on the difficulty
# mentioned in the block object passed

def runMine(block):
    nonce = 0
    while True:
        hash = calculateHash(block.index, block.previousHash, block.timestamp, block.data, block.difficulty, nonce)
        if isValidDifficulty(hash, block.difficulty):
            block.nonce = nonce
            block.hash = hash
            return
        else:
            nonce = nonce + 1
