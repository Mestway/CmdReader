/* --- The page content is only displayable to logged-in users --- */
var username_prefix = "nl2cmd";

$.getJSON("get_current_user", function(uid) {
    var user_id = uid;
    console.log(user_id);
    if (user_id === null) {
        window.location.replace("/");
    } else {
        $('#user-log-out').children('a').text("Log Out (" + username_prefix + user_id.toString() + ')');
    }
});

$(document).ready(function () {

  $("#index-progress-img").hide()
  
  function start(query) {
    if (query !== "RANDOM_SELECTION") {
        $.getJSON("already_searched", {search_phrase: query}, function(searched) {
            if (!searched)
                $("#index-progress-img").show()
                $("#index-progress").text("Indexing webpages... You will be automatically redirect when finished.");
        });
    }

    $.getJSON("pick_url", {search_phrase: query}, function(url) {
      console.log(url);
      if (url === null) {
        var no_url_warning;
        if (query === "RANDOM_SELECTION")
            no_url_warning = 'Oops, you have seen all URLs in our database. Please try search for something new.';
        else
            no_url_warning = '"' + query + '" has been searched before and you have seen all the URLs retrieved. '
                             + 'Please search with a novel query. ';
        BootstrapDialog.show({
          message: no_url_warning,
          buttons: [
          {
              label: 'Close',
              action: function(dialogItself){
                  window.location.replace("/search.html");
                  dialogItself.close();
              }
          }]
	    });
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
        console.log("...")
        $.ajax({url: "logout_user",
             success:  function(data, status) {
                  console.log("User " + username_prefix + user_id.toString()
                                + " successfully log out.");
                  }
        });
  });
});
