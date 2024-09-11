app.factory("generateKeysService", [
  "$http",
  function ($http, baseEndpoint) {
    let apiObj = {};
    let endpoint = baseEndpoint + "/generateKeys";
    apiObj.getjsonData = () => {
      return $http.get(endpoint, { withCredentials: false }).then(
        (result) => {
          return result;
        },
        () => {
          return {};
        }
      );
    };
    return apiObj;
  },
]);

// generate your own public and private keys
