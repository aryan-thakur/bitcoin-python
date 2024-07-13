Dotcoin
-----

This is a Python version of Naivecoin (a simplified version of Bitcoin) called *Dotcoin*.

The blockchain will run within a Docker container and use [Python Flask](https://palletsprojects.com/p/flask/) for the HTTP server (instead of Node Express in the tutorial) and the [Python Libsodium Library (PyNaCl)](https://pynacl.readthedocs.io/en/latest/) for the cryptography primitives.

Build the docker image (first time only)

```
docker build -t dotcoin .
```

To run your code in debug mode (the server will automatically reload when the source files change)

```
docker run --rm -p 5000:5000 -v $(pwd)/src:/shared dotcoin flask --app dotcoin.py --debug run --host=0.0.0.0
```

Type `ctrl-c` to stop the server.
----
# How To Run:
Run an instance (container) on Docker of this Dotcoin application using:
```
docker run --rm -p 5000:5000 -v $(pwd)/src:/shared dotcoin flask --app dotcoin.py --debug run --host=0.0.0.0
```
### Start
Spawn as many instances as you like while changing the port in the following manner: `<custom port>:5000`

Please build this application using the Dockerfile I have provided since I have added the 'requests' module to facilitate easy HTTP requests from the backend itself. No other modules have been added.

Navigate to `http://localhost:<port>/` to open the front end of the node

For the first node press the `GENERATE` button, this will start the node and set the blockchain with the genesis block. Please wait for the genesis block to be mined, once its mined, it will update the balance and your address.

For all consecutive nodes do not press `GENERATE` but instead write a port to connect to in the provided input section and press the `Join` button. This should instantiate the node and copy over all required data

### Transactions
Note that wallet addresses and make transactions as you like. If you send coins to an address that does not exist, those coins are effectively burned. All pending (yet valid) transactions should should show up in the 'Transaction Pool' section of the front end. To update the pool display on other nodes you will need to press the `Refresh` button

### Mining
Mining is automatic. It is done through a background thread corresponding to each node. If the node is successful (the mine was not late), the block is immediately flooded across the network, suspending other miners, updating their chains and data structures and resuming mining. It takes 5 to 30 seconds for a block to be mined.

### Color codings
All transactions are color coded, the `red` upper part is the transaction id, the `green` middle area is a list of TxIns and the `purple` lower part is a list of TxOuts

### Conclusions
You can connect to multiple nodes and form a network graph in any way you like, the flooding algorithm should take care of appropriate forwarding of transactions and newly mined blocks

Thank you for reviewing my project, and please reach out to me if you have any questions
