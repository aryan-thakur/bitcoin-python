from nacl.encoding import Base64Encoder
from nacl.hash import sha256
import base64
import transaction

# Note that you can initialize the nonce as any number initially, the hash will
# be calculated accordingly. Both, the hash and nonce are not final until the
# block is mined.

# It is worth noting that in this coin, all the hashes are encoded in Base64


class Block:
    def __init__(
        self, _index, _timestamp, _data, _previousHash, _difficulty, _nonce, _hash
    ):
        self.index = _index
        self.timestamp = _timestamp
        self.data = _data
        self.hash = _hash
        self.previousHash = _previousHash
        self.difficulty = _difficulty
        self.nonce = _nonce

    # helper to store object data in a dictionary
    def readableObject(self):
        rep = {}
        rep["index"] = self.index
        rep["timestamp"] = self.timestamp
        rep["hash"] = str(self.hash)[2:-1]
        if self.previousHash == None:
            rep["previoushash"] = "NULL"
        else:
            rep["previoushash"] = str(self.previousHash)[2:-1]
        rep["difficulty"] = self.difficulty
        rep["nonce"] = self.nonce
        txs = []
        for tx in self.data:
            txs.append(tx.readableObject())
        rep["data"] = txs
        return rep

    # Hash validation
    def isValidHash(self):
        return (
            sha256(
                (
                    str.encode(
                        str(self.index)
                        + self.previousHash.decode("utf-8")
                        + str(self.timestamp)
                        + str(self.data)
                        + str(self.difficulty)
                        + str(self.nonce)
                    )
                ),
                Base64Encoder,
            )
            == self.hash
        )

    # Type validation
    def isValidBlockStructure(self):
        return (
            type(self.index) == int
            and type(self.timestamp) == float
            and type(self.hash) == bytes
            and type(self.previousHash) == bytes
        )

    def validateBlock(self, prev):
        """
        Main validation function to validate if a block 'cur' is valid
        """
        # checks data types
        if not self.isValidBlockStructure():
            return False
            # is this actually the immediate next block?
        elif self.index != prev.index + 1:
            return False
        # does the current block's previousHash match the previous block's hash?
        # no need to convert to utf8
        elif self.previousHash != prev.hash:
            return False

        elif not isValidDifficulty(self.hash, self.difficulty) == False:
            return False

        elif not self.isValidHash():
            return False

        return True

    def runMine(self):
        """
        This function will effectively 'mine' a block based on the difficulty
        mentioned in the block object passed and set the nonce and correct hash
        """
        nonce = 0
        while True:
            hash = calculateHash(
                self.index,
                self.previousHash,
                self.timestamp,
                self.data,
                self.difficulty,
                nonce,
            )
            if isValidDifficulty(hash, self.difficulty):
                self.nonce = nonce
                self.hash = hash
                return
            else:
                nonce = nonce + 1


# Only used to validate the genesis block, passed in as 'block'
def validateGenesis(block, genesis):
    import dotcoin as dc

    GENESIS = dc.getGenesis()
    if (
        block.index == GENESIS.index
        and block.timestamp == GENESIS.timestamp
        and block.hash == GENESIS.hash
        and block.previousHash == GENESIS.previousHash
        and block.data == GENESIS.data
    ):
        return True
    return False


def isValidDifficulty(hash: bytes, difficulty: int):
    """
    Used to validate if the hash 'hash' is of difficulty 'difficulty', i.e. does it start with 'difficulty'*'0'
    """
    decodedHash = base64.decodebytes(hash)
    binHashStr = "".join(["{:08b}".format(x) for x in decodedHash])

    difficultyStr = ""
    for i in range(difficulty):
        difficultyStr = difficultyStr + "0"

    return binHashStr.startswith(difficultyStr)


# Calculates the hash of a block given the paramters
def calculateHash(index, previousHash, timestamp, data, difficulty, nonce):
    if index != 0:
        return sha256(
            (
                str.encode(
                    str(index)
                    + previousHash.decode("utf-8")
                    + str(timestamp)
                    + str(data)
                    + str(difficulty)
                    + str(nonce)
                )
            ),
            Base64Encoder,
        )
    else:
        return sha256(
            (
                str.encode(
                    str(index)
                    + str(timestamp)
                    + str(data)
                    + str(difficulty)
                    + str(nonce)
                )
            ),
            Base64Encoder,
        )
