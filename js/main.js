$(document).ready(function () {

  function start(query) {
    $.getJSON("pick_url", {search_phrase: query}, function(url) {
      console.log(url);
      if (url === null) {
        alert("Search failed to retrieve any URLs for this query. Please try another one.");
        // history.pushState({}, 'Title: search page', './search.html');
        // window.location.replace("./collect_page.html?url=http://www.uwplse.org");
      } else {
        console.log(url)
        // similar behavior as an HTTP redirect
        history.pushState({}, 'Title: search page', './search.html');
        window.location.replace("./collect_page.html?url=" + url);
      }
    });
  }

  // trigger search by pressing "Enter" key
  $("#nl2cmd-keyword-search-box").keyup(function(event){
    if(event.keyCode == 13){
      $("#nl2cmd-keyword-search-button").click();
    }
  });

  $('#nl2cmd-keyword-search-button').click(function() {
    var search_query = $('#nl2cmd-keyword-search-box').val();
    if (search_query) {         // ignore empty search query
        start(search_query);
    }
  });

  $('#nl2cmd-auto-redirect').click(function(){
    start("RANDOM_SELECTION");
  });

});