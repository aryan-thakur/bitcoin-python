app.controller('mainController', function($scope, $http, $route) {
//initialize the application
$scope.addr = "unknown"; //my addr
$scope.allPeers = []; //my peers
$scope.bal = -1; //my balance
$scope.poolnum = -1; //not used
$scope.keyIn = "" //inputs
$scope.amtIn = "" //inputs
$scope.addrIn = "" //inputs
$scope.private = "" //hidden privvy key
$scope.pool = []; //transaction pool
$scope.balance_obj = {}; //intermediate
$scope.blockchain = [] //chain
$scope.loader = false;
let flag = 0;
$scope.init = () => {}
$scope.joinPort = ""
$scope.destroy = {};
$scope.tx = {};
let launchDataCopy = (port, myport) => {
  $http.get('http://localhost:'+port+'/getAll?port='+myport, {withCredentials: false})
  .then((result) => {
    console.log(result.data)
    $http.post("/receiveAll", JSON.stringify(result.data), {
      withCredentials: false,
      headers: {'Content-Type': 'application/json'},
      transformRequest: angular.indentity
    }).then((data)=>{
      $scope.getPoolNumber();
      $scope.getBlockchain();
    },
    (err)=>{
      console.error(err);
    });
  },
  (err) => {
    console.log(err);
   });
}
$scope.sendTransaction = () => { /*
  $http.get('/sendTransaction?key='+$scope.private+'&addr='+$scope.addrIn+'&amt='+$scope.amtIn,
    {withCredentials: false}).then((result) =>
    {
      $scope.getPoolNumber();
    },
    () => { console.error("Ay yo!");}); */
    obj = {key: $scope.private, addr: $scope.addrIn, amt: $scope.amtIn};
    jsonobj = JSON.stringify(obj)
    $http.post("/sendTransaction", jsonobj, {
      withCredentials: false,
      headers: {'Content-Type': 'application/json'},
      transformRequest: angular.indentity
    }).then((res)=>{
      $scope.getPoolNumber();
      $scope.getPeers();
      console.log('you see')
      console.log(res.data)
  },(err)=>{console.error(err);});
}
$scope.getBalance = () => {
  $http.get('/getBalance', {withCredentials: false})
  .then((result) => {
    if ($scope.bal < result.data.amount){
      $scope.balance_obj = {color: 'green'};
      setTimeout(() => {$scope.balance_obj = {color: 'black'}; $scope.$digest();}, 500);
    }
    else if ($scope.bal > result.data.amount){
      $scope.balance_obj = {color: 'red'};
      setTimeout(() => {$scope.balance_obj = {color: 'black'}; $scope.$digest();}, 500);
    }
    $scope.bal = result.data.amount;
  },
  () => {
    console.log('Ay yo!');
   });
  }
$scope.getPoolNumber = () => {
    $http.get('/getPool', {withCredentials: false})
    .then((result) => {
      console.log(result.data)
      $scope.pool = result.data;
    },
    () => {
      console.log('Ay yo!');
     });
}
$scope.mineBlock = (num) => {
  $scope.loader = true;
  $http.get('/mineBlock', {withCredentials: false})
  .then((result) => {
    $scope.getBalance();
    $scope.getPoolNumber();
    $scope.getBlockchain();
    $scope.getPeers();
    $scope.loader = false;
  },
  () => {
    console.log('Ay yo!');
   });
}
$scope.getBlockchain = () => {
  $http.get('/getBlockchain', {withCredentials: false})
  .then((result) => {
    $scope.blockchain = result.data.chain;
    $scope.blockchain.reverse();
    console.log(result.data);
  },
  () => {
    console.log('Ay yo!');
   });
}
$scope.joinNode = () => {
  $http.get("/generateNode?port="+$scope.joinPort, {withCredentials: false})
  .then((result)=>{
    $scope.getPeers();
    if(result.data.clientAddr != ""){
    $scope.addr = result.data.clientAddr.slice(0,-1).substring(2);
    $scope.private = result.data.clientKey.slice(0,-1).substring(2);
    }
    $scope.destroy = {display: "none"};
    let myPort = window.location.href.split(':')[2].split('/')[0];
    launchDataCopy($scope.joinPort, myPort)
  },
  (err)=>{console.error(err);});
  }
$scope.getPeers = () => {
  $http.get('/getAllPeers', {withCredentials: false})
  .then((result) => {
     $scope.allPeers = result.data;
     $scope.getBalance();
     $scope.getPoolNumber();
     $scope.getBlockchain();
  },(err)=>{console.error(err);});
}
$scope.generate = () => {
  $scope.loader = true;
  if(flag != 1){
  $http.get('/start', {withCredentials: false})
  .then((result) => {
    $scope.addr = result.data.clientAddr.slice(0,-1).substring(2);
    $scope.private = result.data.clientKey.slice(0,-1).substring(2);
    $scope.getBalance();
    $scope.getPoolNumber();
    $scope.loader = false;
  },
  () => {
    console.log('Ay yo!');
   });
  }

  flag = 1
  $scope.destroy = {display: "none"};
}
})
