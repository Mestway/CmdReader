var myLayout;

var page_url = "";

var selected_text = "";

var row_count = 0;
var collected_pairs = [];
var safely_redirect = false;
var in_submission = false;
var error_detected = false;

/* --- The page content is only displayable to logged-in users --- */
var username_prefix = "nl2cmd";
var user_id;
var auto_cmd_detections;

$.ajax({url: "get_current_user",
        error: function(request, status, error) {
            safely_redirect = true;
            window.location.replace("/");
        },
        success: function(uid) {
            user_id = uid;
            console.log(username_prefix + user_id.toString());
            $('#user-log-out').children('a').text("Log Out (" + username_prefix + user_id.toString() + ')');
        }
});

$(document).ready(function(){

    window.onbeforeunload = function() {
        if (!safely_redirect)
            return "Your work will be lost.";
    };

    /* --- Load External Webpage --- */
	$.urlParam = function(name){
		// var results = new RegExp('[\?&]' + name + '=([^&#]*)').exec(window.location.href);
		var results = new RegExp('[\?&]' + name + '=(.*)').exec(window.location.href);
		if (results == null)
			return "http://www.uwplse.org";
		return results[1] || 0;
	}

	// example.com?param1=name&param2=&id=6
	page_url = $.urlParam('url'); // name
	console.log(page_url);
    $('#nl2cmd-new-tab-link').attr("href", page_url);

    $.ajax({url: "get_url_auto_detection",
        data: {"url": page_url},
        error: function(request, status, error) {
            alert("Failed to load command detections!");
        },
        success: function(data) {
            auto_cmd_detections = jQuery.parseJSON(data);
            // console.log(auto_cmd_detections)
        }
    });

    var vertical_split_layout_setting = {
		west: {
		    // minSize: 100,
		    size:	"35%",
		    resizable: false,
		    /* onopen_start: function() {
		        $("#nl2cmd-web-working-panel").width($("body").width() * 0.4);
		    }, */
            onopen_end: function() {
                $("#nl2cmd-web-content-panel").width($("body").width()-$("#nl2cmd-web-working-panel").width());
                $("#web-content-data").width($("#nl2cmd-web-content-panel").width());
            },
            /* onclose_start: function() {
                $("#nl2cmd-web-working-panel").width(0);
            }, */
            onclose_end: function() {
                $("#nl2cmd-web-content-panel").width($("body").width());
                $("#web-content-data").width($("#nl2cmd-web-content-panel").width());
            }
        },
		center: {
		    onresize_start: function() {
		        if (west__isClosed) {
                    $("#nl2cmd-web-content-panel").width($("body").width());
                } else {
                    $("#nl2cmd-web-content-panel").width($("body").width()-$("#nl2cmd-web-working-panel").width());
                }
		    },
		    onresize_end: function () {
                $("#web-content-data").width($("#nl2cmd-web-content-panel").width());
            }
        }
    }
	myLayout = $('body').layout(vertical_split_layout_setting);

	// inlining the web page to work on, if the page is not able to be display, 
	// show the url and ask the user to collect data on the target page

	// this tries to load the page
	var hypothes_header = "https://via.hypothes.is/"
    $("#nl2cmd-web-content-panel")
        .html('<object id="web-content-data" data="' + hypothes_header + page_url + '"/>'
    		/* + '<div id="web-content-data-error">'
            + '<p class="lead" id="error_info">If the page is not loaded successfully, '
            +                                 'click on the URL to open it in a new window: '
            + '<a id="nl2cmd-new-tab-link" href="'+ page_url + '">'
            + page_url
            + '</a>'
            + '. <br/>'
            + 'Otherwise, you may '
            + '<a id="hide-error-message">'
            + 'hide this message'
            + '</a>'
            + '.<p/>'
      	    + '</div>' */);

    /* $.getJSON('get_url_html', {url: page_url}, function(html) {
        $("#nl2cmd-web-content-panel").html(html);
        console.log(html);
	}); */

    $("#web-content-data").width($("#nl2cmd-web-content-panel").width());
    $('#web-content-data').height($('body').height());
    $("#hide-error-message").click(function() {
        // $('#web-content-data-error').hide();
    });
    $("#nl2cmd-new-tab-link").click(function() {
        window.open(this.href, 'newwindow', "width=480, height=640, top=0, left=960");
        myLayout.sizePane('west', $('body').width());
        return false;
    });


    /* --- Input Panel Management ---*/
    for (var i = 0; i < 1; i ++)
	    insert_pair_collecting_row();

    // when the columns are almost full, add content into the table.
    // this method checks every 500ms to to increase the table size
	setInterval(function() {
        if (!in_submission) {
            // var all_rows = $(".nl2cmd-pair-row");
            var blank_cell_count = 0;
            var cmd_spell_error = false;
            for (var i = 1; i <= row_count; i ++) {
                var cmd = $("#nl2cmd-row-no-" + i + " .nl2cmd-cmd").val().trim();
                var pair = $("#nl2cmd-row-no-" + i + " .nl2cmd-text").val().trim();

                if (pair !== "")
                    if (cmd !== "" && !check_verbatim(cmd, auto_cmd_detections)) {
                        if (!error_detected) {
                            /* $("#nl2cmd-row-no-" + i + " .nl2cmd-cmd").notify(
                                "Please make sure the command is copied verbatim from the web page.",
                                { position:'bottom' }
                            ); */
                            $.notify("Please make sure to not modify the commands besides spelling corrections.",
                                      { globalPosition: 'top left' });
                        }
                        cmd_spell_error = true;
                        break;
                    }
                if (cmd == "" || pair == "")
                    blank_cell_count ++;
            }
            if (cmd_spell_error)
                error_detected = true;
            else
                error_detected = false;

            if (blank_cell_count == 0 && !error_detected)
                insert_pair_collecting_row();
        }
	}, 500);

	$("#nl2cmd-submit").click(function() {
        // spellchecker.check();
        in_submission = true;
        remove_row(row_count);

        var num_annotations = collect_annotations();
        var exist_orphan_pair = (num_annotations == -1);

        if (exist_orphan_pair) {
          BootstrapDialog.show({
            message: "There exist incomplete text/cmd pairs, please review you submission.",
            buttons: [
            {
              label: 'Close',
              action: function(dialogItself){
                  dialogItself.close();
              }
            }],
          });
        } else if (error_detected) {
          BootstrapDialog.show({
            message: "You have input a command that doesn't match the web page content, please review you submission.",
            buttons: [
            {
              label: 'Close',
              action: function(dialogItself){
                  dialogItself.close();
              }
            }],
          });
        } else if (num_annotations === 0) {
          BootstrapDialog.show({
            message: 'You cannot submit an empty worksheet. '
                    + '<li>Use the "No pair" option if there is no pairs on the web page.</li>'
                    + '<li>Use the "Skip" option to skip the web page.</li>',
            buttons: [
            {
              label: 'Close',
              action: function(dialogItself){
                  dialogItself.close();
              }
            }],
          });
        } else {
            BootstrapDialog.show({
              message: "Submit " + num_annotations.toString() + " pairs and continue to the next page?",
              buttons: [
              {
                label: 'Yes',
                cssClass: 'btn-primary',
                action: function(dialogItself){
                  $.notify("Please wait while we retrieve the next URL.", { globalPosition: 'top cehter', className: "info"});
                  $.ajax({
                        url: "add-pairs",
                        data: {"pairs": JSON.stringify(collected_pairs)},
                        error: function(request, status, error) {
                            if (status === null)
                                alert("Sorry, we caught an HttpError: " + error + ". Please wait for a few seconds and try again.");
                            else
                                alert("Sorry, we caught an error: " + status + ". Please wait for a few seconds and try again.");
                        },
                        success:  function(data, status) {
                          console.log("yoo!" + data);
                          redirect_to_next()
                          dialogItself.close()
                        }
                      });
                }
              }, {
                label: 'Close',
                action: function(dialogItself){
                    dialogItself.close();
                }
              }],
          });
        }
        return false;
    });

	$("#nl2cmd-report-nopair").click(function() {
		console.log("nopair! " + page_url);
	    in_submission = true;
        remove_row(row_count);

        var num_annotations = collect_annotations();
        var no_pair_warning = 'Please make sure you have examed the web page carefully and didn\'t overlook anything.<br/> '
                              + 'If so, click "Yes" and proceed to the next page.';
        if (num_annotations != 0) {
            no_pair_warning = 'You have chosen the "No pair" option, anything you put in the collection entries will '
                              + 'be discarded. Still want to proceed to the next page?';
        }
		BootstrapDialog.show({
          message: no_pair_warning,
          buttons: [
          {
              label: 'Yes',
              cssClass: 'btn-primary',
              action: function(dialogItself){
                $.notify("Please wait while we retrieve the next URL.", { globalPosition: 'top cehter', className: "info"});
                $.ajax({
                      url: "no_pairs",
                      data: {"url": page_url},
                      error: function(request, status, error) {
                          if (status === null)
                              alert("Sorry, we caught an HttpError: " + error + ". Please wait for a few seconds and try again.");
                          else
                              alert("Sorry, we caught an error: " + status + ". Please wait for a few seconds and try again.");
                      },
                      success:  function(data, status) {
                        console.log("Yea!" + data);
                        redirect_to_next();
                        dialogItself.close();
                      }
                });
              }
          }, {
              label: 'Close',
              action: function(dialogItself){
                  dialogItself.close();
              }
          }],
	    });
      return false;
	 });

    /* --- Skip Current Page --- */
    $("#nl2cmd-skip-page").click(function() {
        var skip_warning = 'You may skip a web page when encounter technical issues. <br/>'
                           + 'If there is no pair on the web page, use the "No pair" option instead.';
        BootstrapDialog.show({
          message: skip_warning,
          buttons: [
          {
              label: 'Skip',
              cssClass: 'btn-primary',
              action: function(dialogItself){
                // record skip action
                // setTimeout(function() {
                $.notify("Please wait while we retrieve the next URL.", { globalPosition: 'top cehter', className: "info"});
                $.ajax({url: "skip_url",
                     data: {"url": page_url},
                     error: function(request, status, error) {
                          if (status === null)
                              alert("Sorry, we caught an HttpError: " + error + ". Please wait for a few seconds and try again.");
                          else
                              alert("Sorry, we caught an error: " + status + ". Please wait for a few seconds and try again.");
                     },
                     success:  function(data, status) {
                          console.log("User " + username_prefix + user_id.toString()
                                        + " chose to skip url " + page_url + ".");
                          redirect_to_next();
                          dialogItself.close();
                     }
                });
              }
          }, {
              label: 'Close',
              action: function(dialogItself){
                  dialogItself.close();
              }
          }],
	    });
    });

    $(window).on('hidden.bs.modal', function() {
        console.log('Fired when hide event has finished!');
        in_submission = false;
    });

	 /* --- textual input auto-resize --- */
	 var observe;
     if (window.attachEvent) {
        observe = function (element, event, handler) {
            element.attachEvent('on'+event, handler);
        };
     }
     else {
        observe = function (element, event, handler) {
            element.addEventListener(event, handler, false);
        };
     }
     function init () {
        var cmd = $(".nl2cmd-cmd");
        var text = $(".nl2cmd-text");
        function resize () {
            cmd.style.height = 'auto';
            cmd.style.height = cmd.scrollHeight+'px';
            text.style.height = 'auto';
            text.style.height = text.scrollHeight+'px';
        }
        /* 0-timeout to get the already changed text */
        function delayedResize () {
            window.setTimeout(resize, 0);
        }
        observe(cmd, 'change',  resize);
        observe(cmd, 'cut',     delayedResize);
        observe(cmd, 'paste',   delayedResize);
        observe(cmd, 'drop',    delayedResize);
        observe(cmd, 'keydown', delayedResize);
        observe(text, 'change',  resize);
        observe(text, 'cut',     delayedResize);
        observe(text, 'paste',   delayedResize);
        observe(text, 'drop',    delayedResize);
        observe(text, 'keydown', delayedResize);

        cmd.focus();
        cmd.select();
        text.focus();
        text.select();
        resize();
     }

	 /* --- Spell checking in textual input --- */
	 //TODO: unfinished
	var spellchecker = new $.SpellChecker('.nl2cmd-box nl2cmd-text', {
        lang: 'en',
        parser: 'html',
        webservice: {
          path: '../php/SpellChecker.php',
          driver: 'PSpell'
        },
        suggestBox: {
          position: 'below',
          offset: 1
        }
      });

      // Bind spellchecker handler functions
      spellchecker.on('check.success', function() {
        alert('There are no incorrectly spelt words!');
      });

      /* --- Select text with mouse --- */
      //TODO: not implemented

      /* --- Jump to search page --- */
      $('#nl2cmd-search').click(function() {
        window.location.replace("/search.html");
        // safely_redirect = true;
      });

      /* --- Renew URL lease every 5 minutes --- */
      setInterval(function() {
        $.ajax({url: "heartbeat"});
      }, 3e5);

      /* --- User log out --- */
      $('#user-log-out').click(function() {
        $.ajax({url: "logout_user",
             success:  function(data, status) {
                  console.log("User " + username_prefix + user_id.toString()
                                + " successfully log out.");
                  window.location.replace("/");
             }
        });
    });
});

function remove_row(i) {
    var cmd = $("#nl2cmd-row-no-" + i + " div .nl2cmd-cmd").val();
    var text = $("#nl2cmd-row-no-" + i + " div .nl2cmd-text").val();

    if (cmd == "" && text == "") {
        $("#nl2cmd-row-tr-" + i).remove();
        row_count --;
    }
}

function collect_annotations() {
    collected_pairs = [];
    for (var i = 1; i <= row_count; i ++) {
          var cmd = $("#nl2cmd-row-no-" + i + " div .nl2cmd-cmd").val();
          var text = $("#nl2cmd-row-no-" + i + " div .nl2cmd-text").val();

          if ((cmd == "" && text != "" )|| (cmd != "" && text == "")) {
            return -1;
          } else {
            var data_entry = {"cmd":cmd, "nl":text, url:page_url};
            collected_pairs.push(data_entry);
          }
    }
    return collected_pairs.length;
}

function redirect_to_next() {
    var query = "";
    // retrieve current search query
    $.getJSON("get_search_phrase", function(search_query) {
        query = search_query;
        console.log(query)
    });

    $.getJSON("pick_url", {search_phrase: query}, function(url) {
      console.log(url);
      if (url === null) {
        var query_completion_warning = 'Congrats! You have annotated all the web pages we have gathered so far. '
            + 'You will be automatically redirect to the search page now.';
        BootstrapDialog.show({
          message: query_completion_warning,
          buttons: [
          {
              label: 'Close',
              action: function(dialogItself){
                  window.location.replace("/search.html");
                  dialogItself.close();
              }
          }]
	    });
      } else {
        window.location.replace("./collect_page.html?url=" + url);
      }
    });

    // in_submission = false;
    safely_redirect = true;
}

function insert_pair_collecting_row() {
	row_count ++;
	$("#nl2cmd-pair-collect-table tbody").append(
  			'<tr class="nl2cmd-pair-row" id="' + "nl2cmd-row-tr-" + row_count + '"><th scope="">'
  			+ row_count 
  			+ '</th><td id="' + "nl2cmd-row-no-" + row_count + '" class="nl2cmd-pair-td">'
  			+ '<div class="input-group">'
  			+    '<span class="input-group-addon nl2cmd-span" id="basic-addon1">cmd</span>'
  			+ 	 '<textarea type="text" rows="1" class="nl2cmd-box nl2cmd-cmd form-control" spellcheck="false" placeholder="Command" />'
  			+ '</div>'
  			+ '<br/>'
  			+ '<div class="input-group">'
  			+    '<span class="input-group-addon nl2cmd-span basic-addon1">txt</span>'
  			+ 	 '<textarea type="text" class="nl2cmd-box nl2cmd-text form-control vresize" spellcheck="true" placeholder="Description" />'
  			+ '</div>'
  			+ '</td></tr>');    // default html textarea spellcheck disabled

  	$("").append()
}

function check_verbatim(cmd, auto_cmd_detections) {
    for (var i = 0; i < auto_cmd_detections.length; i ++) {
        var auto_detection = auto_cmd_detections[i];
        // console.log(auto_detection);
        if (auto_detection.indexOf(cmd) > -1)
            // check if command is substring of auto-detection
            return true;
        else if (cmd.indexOf(auto_detection) > -1)
            // check if auto-detection is substring of command
            return true;
        else if (levDist(cmd, auto_detection) <= 3)
            return true;
    }
    return false;
    // return true;
}

function levDist(s, t) {
    var d = []; //2d matrix

    // Step 1
    var n = s.length;
    var m = t.length;

    if (n == 0) return m;
    if (m == 0) return n;

    //Create an array of arrays in javascript (a descending loop is quicker)
    for (var i = n; i >= 0; i--) d[i] = [];

    // Step 2
    for (var i = n; i >= 0; i--) d[i][0] = i;
    for (var j = m; j >= 0; j--) d[0][j] = j;

    // Step 3
    for (var i = 1; i <= n; i++) {
        var s_i = s.charAt(i - 1);

        // Step 4
        for (var j = 1; j <= m; j++) {

            //Check the jagged ld total so far
            if (i == j && d[i][j] > 4) return n;

            var t_j = t.charAt(j - 1);
            var cost = (s_i == t_j) ? 0 : 1; // Step 5

            //Calculate the minimum
            var mi = d[i - 1][j] + 1;
            var b = d[i][j - 1] + 1;
            var c = d[i - 1][j - 1] + cost;

            if (b < mi) mi = b;
            if (c < mi) mi = c;

            d[i][j] = mi; // Step 6

            //Damerau transposition
            if (i > 1 && j > 1 && s_i == t.charAt(j - 2) && s.charAt(i - 2) == t_j) {
                d[i][j] = Math.min(d[i][j], d[i - 2][j - 2] + cost);
            }
        }
    }

    // Step 7
    return d[n][m];
}

function getSelectedText(e) {
    selected_text = (document.all) ? document.selection.createRange().text :
                    document.getSelection();
    $("#nl2cmd-row-no-1 div .nl2cmd-cmd").val(selected_text);
}
