import wallet
import transaction
import txin
import txout
import utxo
import blockchain


class Node:
    def __init__(self, _transactionPool=None, _walletAddr=""):
        # transaction pool
        if _transactionPool is None:
            self.transactionPool = []
        else:
            self.transactionPool = _transactionPool
        self.walletAddr = _walletAddr  # my public key/wallet address
        self.blockchain = []  # my blockchain copy
        self.utxos = []  # all uTxOs available
        self.peers = []  # my peers
        self.recentTxId = None
        self.recentBlockHashs = []

    def sendTransaction(self, addr, amount, privateKey):
        """
        Uses this key pair to create a transaction from my account to the receiver
        """
        copyUTxOs = []
        for utxos in self.utxos:
            newutxo = utxo.UTxO(
                utxos.txoutid, utxos.txoutidx, utxos.address, utxos.amount
            )
            copyUTxOs.append(newutxo)

        # my keyPair, private key and public keys
        keyPair = [privateKey, self.walletAddr]

        # use my key pair to create a transaction from my account to the receiver
        tx = wallet.createTransaction(
            addr, keyPair, amount, copyUTxOs, self.transactionPool
        )

        # Add this transaction to the transaction pool
        if not self.addToPool(tx, copyUTxOs):
            return None
        return tx

    def addToPool(self, tx, utxos):
        """
        Add transactions to transaction pool if valid
        """
        # Validate if possible, otherwise reject it
        if not tx.validateTransaction(utxos):
            return False

        # Another check if these txins are actually in the pool
        if not tx.isValidTxForPool(self.transactionPool):
            return False

        # If checks passed, actually append
        self.transactionPool.append(tx)
        return True

    # all peers receive your transaction pool as theirs
    def broadcastPool(self):
        for peer in self.peers:
            peer.receivePool(self.transactionPool)

    def getPool(self):
        return self.transactionPool

    def getBlockchain(self):
        return self.blockchain

    # add a peer (using their port)
    def addNode(self, port):
        self.peers.append(port)

    def getNodes(self):
        return self.peers

    # overwrite my transaction pool with the parameter pool
    def receivePool(self, transactionPool):
        self.transactionPool = transactionPool

    # overwrite my blockchain copy if parameter blockchain is valid
    def receiveBlockchain(self, blockchains):
        if blockchain.validateBlockchain(blockchains):
            self.blockchain = blockchains

    def updatePool(self, txs):
        """
        Remove transactions from transaction pool
        """
        for tx in txs:
            for atx in self.transactionPool:
                if tx.getTransactionId() == atx.getTransactionId():
                    self.transactionPool.remove(atx)

    # set blockchain without question
    def setblockchain(self, chain):
        self.blockchain = chain

    def generateNextBlock(self):
        """
        As the name suggests, tries to mine the next block, if success, adds to the blockchain
        """
        data = []

        # make coinbase transaction to node mining the block, append to data
        tx = transaction.makeCoinbaseTransaction(self.walletAddr, len(self.blockchain))
        data.append(tx)

        # add all transaction pool transactions to data
        for transactions in self.transactionPool:
            data.append(transactions)

        # generate this block, including mining it
        newblock = blockchain.generateBlock(self.blockchain, data)
        if (
            newblock.index <= self.blockchain[len(self.blockchain) - 1].index
        ):  # if the block you spawned is old? the chain already moved ahead?
            return None

        self.addToBlockchain(newblock)
        return newblock

    def addToBlockchain(self, blck):
        """
        Adds a newly mined block to the blockchain
        """
        copyUTxOs = []
        for utxos in self.utxos:
            newutxo = utxo.UTxO(
                utxos.txoutid, utxos.txoutidx, utxos.address, utxos.amount
            )
            copyUTxOs.append(newutxo)

        # recount free uTxOs
        self.utxos = transaction.processTransactions(blck.data, copyUTxOs, blck.index)

        # remove transaction pool transactions that were mined
        self.updatePool(blck.data)
        self.blockchain.append(blck)
