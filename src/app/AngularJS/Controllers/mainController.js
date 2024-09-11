app.controller("mainController", function ($scope, $http, $route) {
  //initialize the application

  $scope.addr = "unknown"; //my addr
  $scope.private = ""; //hidden priv key

  $scope.allPeers = []; //my peers
  $scope.bal = -1; //my balance
  $scope.poolnum = -1; //not used
  $scope.keyIn = ""; //inputs
  $scope.amtIn = ""; //inputs
  $scope.addrIn = ""; //inputs
  $scope.pool = []; //transaction pool
  $scope.balance_obj = {}; //intermediate
  $scope.blockchain = []; //chain
  $scope.loader = false; //spinner
  let flag = 0;
  $scope.init = () => {};
  $scope.joinPort = "";
  $scope.destroy = {};
  $scope.tx = {};

  /* Function to copy over data from an existing node */
  let launchDataCopy = (port, myport) => {
    $http
      .get("http://localhost:" + port + "/getAll?port=" + myport, {
        //pull the data from the existing node
        withCredentials: false,
      })
      .then(
        (result) => {
          console.log(result.data);
          $http
            .post("/receiveAll", JSON.stringify(result.data), {
              // now send the data to yourself
              withCredentials: false,
              headers: { "Content-Type": "application/json" },
              transformRequest: angular.indentity,
            })
            .then(
              (data) => {
                $scope.getPoolNumber();
                $scope.getBlockchain();
              },
              (err) => {
                console.error(err);
              }
            );
        },
        (err) => {
          console.log(err);
        }
      );
  };

  /* Makes a transaction given details */
  $scope.sendTransaction = () => {
    obj = { key: $scope.private, addr: $scope.addrIn, amt: $scope.amtIn };
    jsonobj = JSON.stringify(obj);
    $http
      .post("/sendTransaction", jsonobj, {
        withCredentials: false,
        headers: { "Content-Type": "application/json" },
        transformRequest: angular.indentity,
      })
      .then(
        (res) => {
          $scope.getPoolNumber();
          $scope.getPeers();
          console.log(res.data);
        },
        (err) => {
          console.error(err);
        }
      );
  };

  /* Shows your balance, adds color and theme to changing balances */
  $scope.getBalance = () => {
    $http.get("/getBalance", { withCredentials: false }).then(
      (result) => {
        if ($scope.bal < result.data.amount) {
          $scope.balance_obj = { color: "green" };
          setTimeout(() => {
            $scope.balance_obj = { color: "black" };
            $scope.$digest();
          }, 500);
        } else if ($scope.bal > result.data.amount) {
          $scope.balance_obj = { color: "red" };
          setTimeout(() => {
            $scope.balance_obj = { color: "black" };
            $scope.$digest();
          }, 500);
        }
        $scope.bal = result.data.amount;
      },
      () => {
        console.log("Error in getBalance");
      }
    );
  };

  /* Gets your transaction pool */
  $scope.getPoolNumber = () => {
    $http.get("/getPool", { withCredentials: false }).then(
      (result) => {
        console.log(result.data);
        $scope.pool = result.data;
      },
      () => {
        console.log("Error in getPoolNumber");
      }
    );
  };

  /* Gets your blockchain to display */
  $scope.getBlockchain = () => {
    $http.get("/getBlockchain", { withCredentials: false }).then(
      (result) => {
        $scope.blockchain = result.data.chain;
        $scope.blockchain.reverse();
        console.log(result.data);
      },
      () => {
        console.log("Error in getBlockchain()");
      }
    );
  };

  /* Joins an existing node and generates self */
  $scope.joinNode = () => {
    $http
      .get("/generateNode?port=" + $scope.joinPort, { withCredentials: false })
      .then(
        (result) => {
          $scope.getPeers();
          if (result.data.clientAddr != "") {
            $scope.addr = result.data.clientAddr.slice(0, -1).substring(2); //client wallet addr
            $scope.private = result.data.clientKey.slice(0, -1).substring(2); //client public key
          }
          $scope.destroy = { display: "none" };
          let myPort = window.location.href.split(":")[2].split("/")[0];
          launchDataCopy($scope.joinPort, myPort); // need to copy over all the data
        },
        (err) => {
          console.error(err);
        }
      );
  };

  /* Gets all peers */
  $scope.getPeers = () => {
    $http.get("/getAllPeers", { withCredentials: false }).then(
      (result) => {
        $scope.allPeers = result.data;
        $scope.getBalance();
        $scope.getPoolNumber();
        $scope.getBlockchain();
      },
      (err) => {
        console.error(err);
      }
    );
  };

  /* Initial generation function */
  $scope.generate = () => {
    $scope.loader = true;
    if (flag != 1) {
      $http.get("/start", { withCredentials: false }).then(
        (result) => {
          $scope.addr = result.data.clientAddr.slice(0, -1).substring(2); // client's address, or public key
          $scope.private = result.data.clientKey.slice(0, -1).substring(2); // client's private key, stored locally in browser data
          $scope.getBalance(); // current balance
          $scope.getPoolNumber();
          $scope.loader = false;
        },
        () => {
          console.log("Failed generate");
        }
      );
    }

    flag = 1;
    $scope.destroy = { display: "none" };
  };
});

/* Tries to mine the next block */
$scope.mineBlock = (num) => {
  $scope.loader = true;
  $http.get("/mineBlock", { withCredentials: false }).then(
    (result) => {
      $scope.getBalance();
      $scope.getPoolNumber();
      $scope.getBlockchain();
      $scope.getPeers();
      $scope.loader = false;
    },
    () => {
      console.log("Error in mineBlock");
    }
  );
};
