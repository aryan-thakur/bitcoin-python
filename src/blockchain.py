from nacl.encoding import Base64Encoder
from nacl.hash import sha256
import datetime
import block
from typing import List

# Static file

# Genesis block always the head of the chain
BLOCK_GENERATION_INTERVAL = 10
DIFFICULTY_ADJUSTMENT_INTERVAL = 10


# Generates a block then mines it
def generateBlock(chain, data):
    prevBlock = chain[len(chain) - 1]
    diff = getDifficulty(chain)
    nextIdx = len(chain)
    nextTime = datetime.datetime.now().timestamp()
    newblock = block.Block(nextIdx, nextTime, data, prevBlock.hash, diff, 0, "")
    newblock.runMine()
    return newblock


# Basic function to validate the blockchain
def validateBlockchain(chain: List[(block.Block)]):
    if len(chain) == 0:
        return False
    for i in range(len(chain)):
        if i == 0:
            if not block.validateGenesis(chain[0]):
                return False
        else:
            if not chain[i].validateBlock(chain[i - 1]):
                return False
    return True


def getDifficulty(chain):
    """
    Function that determines the current difficulty of the blockchain
    """
    latestBlock = chain[len(chain) - 1]

    # If the current block is on the difficulty adjustment interval, try to adjust the difficulty
    if (
        latestBlock.index % DIFFICULTY_ADJUSTMENT_INTERVAL == 0
        and latestBlock.index != 0
    ):
        return getAdjustedDifficulty(latestBlock, chain)
    else:
        return latestBlock.difficulty


def getAdjustedDifficulty(block, chain):
    """
    Adjusts the difficulty of the chain, returning the new difficulty
    """
    prevAdjBlock = chain[len(chain) - DIFFICULTY_ADJUSTMENT_INTERVAL]

    # The time expected between the latest two difficulty adjustment blocks is the difficulty adjustment interval
    # i.e. the count of blocks between them times the constant of block_generation_interval in seconds
    timeExpected = DIFFICULTY_ADJUSTMENT_INTERVAL * BLOCK_GENERATION_INTERVAL

    # The actual time taken is the difference in timestamps between the latest two difficulty adjustment blocks
    timeTaken = block.timestamp - prevAdjBlock.timestamp

    # Adjust the difficulty based on certain predefined crtierion
    if timeTaken < timeExpected / 2:
        return prevAdjBlock.difficulty + 1
    elif timeTaken > timeExpected * 2:
        return prevAdjBlock.difficulty - 1
    else:
        return prevAdjBlock.difficulty


def isValidTimestamp(prevBlock, blck):
    return (prevBlock.timestamp - 60 < blck.timestamp) and (
        blck.timestamp - 60 < datetime.datetime.now().timestamp()
    )


# UNUSED/REFERENCE FUNCTIONS
# Will return true if the chain has been replaced based on the nakamoto consensus, used for blockchain forks
def correctChain(chain):
    nakamotoVal = 0
    for block in chain:
        sub = 2 ** (block.difficulty)
        nakamotoVal = nakamotoVal + sub

    currentNakamotoVal = 0
    for block in blockChain:
        sub = 2 ** (block.difficulty)
        currentNakamotoVal = currentNakamotoVal + sub

    if nakamotoVal > currentNakamotoVal and validateBlockchain(chain):
        blockChain = chain
        broadcast()
        return True
    else:
        return False


# This function is no longer used but is kept in the codebase for reference purposes
def replaceBlockchain(chain):
    if validateBlockchain(chain) and (len(chain) > len(getBlockchain)):
        blockChain = chain
        broadcast()
        return True
    else:
        return False
