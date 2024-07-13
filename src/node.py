import wallet
import transaction
import txin
import txout
import utxo
import blockchain
import dotcoin as dc

class Node:
    def __init__(self, _transactionPool=None, _walletAddr=''):
        if _transactionPool is None:
            self.transactionPool = []
        else:
            self.transactionPool = _transactionPool
        self.walletAddr = _walletAddr
        self.blockchain = []
        self.utxos = []
        self.peers = []
        self.recentTxId = None
        self.recentBlockHashs = []

    def sendTransaction(self, addr, amount, privateKey):
        # my keyPair
        keyPair = [privateKey, self.walletAddr]
        tx = wallet.createTransaction(addr, keyPair, amount, dc.getUnspentTxOut(), self.transactionPool)
        if not self.addToPool(tx, dc.getUnspentTxOut()):
            return None
        #self.broadcastPool()
        return tx

    def addToPool(self, tx, utxos):
        if not transaction.validateTransaction(tx, utxos):
            return False
        # Another check if these txins are actually in the pool
        if not transaction.isValidTxForPool(tx, self.transactionPool):
            return False
        self.transactionPool.append(tx)
        return True

    def broadcastPool(self):
        for peer in self.peers:
            peer.receivePool(self.transactionPool)

    def getPool(self):
        return self.transactionPool

    def getBlockchain(self):
        return self.blockchain

    def addNode(self, port):
        self.peers.append(port)

    def getNodes():
        return self.peers

    def receivePool(self, transactionPool):
        self.transactionPool = transactionPool

    def receiveBlockchain(self, blockchains):
        if blockchain.validateBlockchain(blockchains):
            self.blockchain = blockchains

    def updatePool(self,utxos,txs):
        for tx in txs:
            for atx in self.transactionPool:
                if tx.getTransactionId() == atx.getTransactionId():
                    self.transactionPool.remove(atx)

    def setblockchain(self, chain):
        self.blockchain = chain

def generateNextBlock(node):
    data = []
    tx=transaction.makeCoinbaseTransaction(node.walletAddr, len(node.blockchain))
    data.append(tx)
    for transactions in node.transactionPool:
        data.append(transactions)
    newblock = blockchain.generateBlock(node.blockchain, data)
    if newblock.index <= node.blockchain[len(node.blockchain)-1].index: #if the block you spawned is old? the chain already moved ahead?
        return None
    addToBlockchain(node, newblock)
    return newblock

def addToBlockchain(node, blck):
    dc.setUnspentTxOut(transaction.processTransactions(blck.data, dc.getUnspentTxOut(), blck.index))
    node.updatePool(dc.getUnspentTxOut(), blck.data)
    node.blockchain.append(blck)
