/* --- The page content is only displayable to logged-in users --- */
$.getJSON("get_current_user", function(uid) {
    var user_id = uid;
    console.log(user_id);
    if (user_id === null) {
        window.location.replace("/");
    }
});

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
    return false;
  });

  $('#nl2cmd-auto-redirect').click(function(){
    start("RANDOM_SELECTION");
    return false;
  });

  $('#user-log-out').click(function() {
        var username_prefix = "nl2cmd";
        console.log("...")
        $.ajax({url: "logout_user",
             success:  function(data, status) {
                  console.log("User " + username_prefix + user_id.toString()
                                + " successfully log out.");
                  }
        });
  });
});
