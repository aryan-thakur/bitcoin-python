import block
from nacl.encoding import Base64Encoder
from nacl.hash import sha256
import datetime

# Genesis block always the head of the chain

BLOCK_GENERATION_INTERVAL = 10
DIFFICULTY_ADJUSTMENT_INTERVAL = 10


def generateBlock(chain, data):
    prevBlock = chain[len(chain) - 1]
    diff = getDifficulty(chain)
    nextIdx = len(chain)
    nextTime = datetime.datetime.now().timestamp()
    newblock = block.Block(nextIdx, nextTime, data, prevBlock.hash, diff, 0, '')
    block.runMine(newblock)
    return newblock


# Basic function to validate the blockchain
def validateBlockchain(chain):
    if len(chain) == 0:
        return False
    for i in range(len(chain)):
        if i == 0:
            if not block.validateGenesis(chain[0]):
                return False
        else:
            if not block.validateBlock(chain[i-1], chain[i]):
                return False
    return True

def replaceBlockchain(chain):
    if(validateBlockchain(chain) and (len(chain) > len(getBlockchain))):
        blockChain = chain
        broadcast()
        return True
    else:
        return False

# This function should ideally replace the one above, will return true
# if the chain has been replaced based on the nakamoto consensus

def correctChain(chain):
    nakamotoVal = 0
    for block in chain:
        sub = 2**(block.difficulty)
        nakamotoVal = nakamotoVal + sub

    currentNakamotoVal = 0
    for block in blockChain:
        sub = 2**(block.difficulty)
        currentNakamotoVal = currentNakamotoVal + sub

    if nakamotoVal > currentNakamotoVal and validateBlockchain(chain):
        blockChain = chain
        broadcast()
        return True
    else:
        return False

# Function that determines the current difficulty of the blockchain

def getDifficulty(chain):
    latestBlock = chain[len(chain)-1]
    if(latestBlock.index % DIFFICULTY_ADJUSTMENT_INTERVAL == 0 and latestBlock.index != 0):
        return getAdjustedDifficulty(latestBlock, chain)
    else:
        return latestBlock.difficulty

def getAdjustedDifficulty(block, chain):
    prevAdjBlock = chain[len(chain)-DIFFICULTY_ADJUSTMENT_INTERVAL]
    timeExpected = DIFFICULTY_ADJUSTMENT_INTERVAL*BLOCK_GENERATION_INTERVAL
    timeTaken = block.timestamp - prevAdjBlock.timestamp

    if(timeTaken < timeExpected/2):
        return prevAdjBlock.difficulty + 1
    elif(timeTaken > timeExpected*2):
        return prevAdjBlock.difficulty - 1
    else:
        return prevAdjBlock.difficulty

def isValidTimestamp(prevBlock, blck):
    return (prevBlock.timestamp - 60 < blck.timestamp) and (blck.timestamp - 60 < datetime.datetime.now().timestamp())
