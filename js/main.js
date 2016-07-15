/* --- The page content is only displayable to logged-in users --- */

var username_prefix = "nl2cmd";
var user_id;

$.ajax({url: "get_current_user",
        error: function(request, status, error) {
            window.location.replace("/");
        },
        success: function(uid) {
            user_id = uid;
            console.log(user_id);
            $('#nl2cmd-user-log-out').children('a').text("Log Out (" + username_prefix + user_id.toString() + ')');
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

  $('#nl2cmd-auto-redirect').click(function() {
    $("#index-progress-img").show()
    $("#index-progress").text("Please wait while we automatically redirecting you to a web page.");
    start("RANDOM_SELECTION");
    return false;
  });

  $('#nl2cmd-user-view-report').click(function() {
    $.getJSON("get_user_report", function(data) {
        // console.log(data)
        var encouraging_msg;
        if (data[1].toString() === '0')
            encouraging_msg = 'You haven\'t submitted any pair so far. Looking forward to your input!<br>';
        else
            encouraging_msg = '              Great Job! Keep going!          <br>';
        var user_report = '';
        // user_report = user_report + '<span></span><br>';
        user_report = user_report + '<span>Total number of pairs annotated:&#9;' + data[1] + '</span><br>';
        user_report = user_report + '<span>Number of urls annotated:&#9;       ' + data[2] + '</span><br>';
        user_report = user_report + '<span>Number of urls with no pairs:&#9;   ' + data[3] + '</span><br>';
        user_report = user_report + '<span>Number of urls skipped:&#9;         ' + data[4] + '</span><br>';
        user_report = user_report + '<br>';
        user_report = user_report + encouraging_msg;
        user_report = user_report + '                    ¯\\_(ツ)_/¯                <br>';
        BootstrapDialog.show({
            title: '======== ' + data[0] + ' ========',
            message: user_report,
            buttons: [
                {
                  label: 'Close',
                  action: function(dialogItself){
                      window.location.replace("/search.html");
                      dialogItself.close();
                }
            }]
        });
    });
    return false;
  });

  $('#nl2cmd-user-leaderboard').click(function() {
    $.getJSON("get_leaderboard", function(data) {
        console.log(data);
        if (data.length > 0) {
            var leaderboard = '<ol type="1">';
            var on_leaderboard = -1;
            var encouraging_msg;
            for (var i = 0; i < data.length; i ++) {
                var display_name = data[i][1];
                var num_pairs = data[i][2];
                if (data[i][0] === user_id) {
                    display_name = '<b>' + display_name + '</b>';
                    on_leaderboard = i;
                }
                leaderboard = leaderboard + '<span>' + (i+1).toString() + '. ' + display_name + ' (' + num_pairs
                            + ' pairs)</span><br>';
            }
            leaderboard = leaderboard + '</ol>';
            if (on_leaderboard === 0) {
                encouraging_msg = '          Excellent! You are No.1!          <br>';
            } else if (on_leaderboard > 0) {
                encouraging_msg = '           Great Job! Keep going!         <br>';
            } else {
                encouraging_msg = '         Don\'t be discouraged -- annotate more and your name will show here!       <br>';
            }
            leaderboard = leaderboard + encouraging_msg;
            leaderboard = leaderboard + '                  ✌(◕‿-)✌                <br>';
            BootstrapDialog.show({
                title: 'Leaderboard',
                message: leaderboard,
                buttons: [
                    {
                      label: 'Close',
                      action: function(dialogItself){
                          window.location.replace("/search.html");
                          dialogItself.close();
                    }
                }]
            });
        }
    });
    return false;
  });

  $('#nl2cmd-user-log-out').click(function() {
        $.ajax({url: "logout_user",
             success:  function(data, status) {
                  console.log("User " + username_prefix + user_id.toString()
                                + " successfully log out.");
                  window.location.replace("/");
             }
        });
  });
});
