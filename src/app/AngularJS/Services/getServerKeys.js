app.factory('generateKeysService', ['$http', function($http, baseEndpoint) {
  let apiObj = {};
  let endpoint = baseEndpoint+"/getServerKeys"
  apiObj.getjsonData = () => {
  return $http.get(endpoint, {withCredentials: false})
  .then((result) => {return result;},() => {return {};});};
  return apiObj;
}]);

// get the server node's public and private keys for transactions
