app.directive('transaction', function() {
  return {
    restrict: 'E',
    scope: {
      info: '='
    },
    templateUrl: './app/AngularJS/Directives/Views/transaction.html',
    transclude: true
  };
});
