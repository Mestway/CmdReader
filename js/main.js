$(document).ready(function () {

  function start(query) {
    $.getJSON("/pick_url", {search_phrase: query}, function(url) {
      console.log(url);
      if (url === null) {
        alert("no URLs available!");
      } else {
        // similar behavior as an HTTP redirect
        window.location.replace("./collect_page?url=" + url);
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
