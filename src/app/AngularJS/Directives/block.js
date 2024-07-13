app.directive('block', function() {
  return {
    restrict: 'E',
    scope: {
      info: '='
    },
    templateUrl: './app/AngularJS/Directives/Views/block.html',
    transclude: true
  };
});
