$(document).ready(function () {

  function start(query) {
    $.getJSON("/pick_url", {search_phrase: query}, function(url) {
      console.log(url);
      if (url === null) {
        alert("no URLs available!");
      } else {
        alert("TODO: you should be redirected to page 2");
      }
    });
  }


  $('#nl2cmd-keyword-search-button').click(function () {
    var search_query = $('#nl2cmd-keyword-search-box').val();
    start(search_query);
	});

	$('#nl2cmd-auto-redirect').click(function () {
    start("");
	});
});
