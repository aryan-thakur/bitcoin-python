var app = angular.module("mainApp", ["ngRoute", "angularCSS"]);
app.config(function ($routeProvider) {
  $routeProvider
    .when('/', {
      controller: 'mainController',
      templateUrl: './app/AngularJS/Views/mainView.html',
      css: './app/Styles/mainStyle.css'
    })
    .otherwise({
      redirectTo: '/'
    });
});
app.constant('baseEndpoint', {value: '127.0.0.1:5000'});
//need to upload this key to github for this app to work on github pages
