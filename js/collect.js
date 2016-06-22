var myLayout;

var page_url = "";

var selected_text = "";

var row_count = 0;
var collected_pairs = [];
var safely_redirect = false;
var being_submitted = false;

/* --- The page content is only displayable to logged-in users --- */
$.getJSON("get_current_user", function(uid) {
    var user_id = uid;
    console.log(user_id);
    if (user_id === null) {
        safely_redirect = true;
        window.location.replace("/");
    }
});

$(document).ready(function(){

    window.onbeforeunload = function() {
        if (!safely_redirect)
            return "Your work will be lost.";
    };

    /* --- Load External Webpage --- */
	$.urlParam = function(name){
		var results = new RegExp('[\?&]' + name + '=([^&#]*)').exec(window.location.href);
		if (results == null)
			return "http://www.uwplse.org";
		return results[1] || 0;
	}

	// example.com?param1=name&param2=&id=6
	page_url = $.urlParam('url'); // name
	console.log(page_url);

    var vertical_split_layout_setting = {
		west__minSize: 100,
		west__size:	"40%",
		west__resizable: false,
		west__onopen_end: function() {
		    $("#nl2cmd-web-content-panel").width($("body").width()-$("#nl2cmd-web-working-panel").width());
		    $("#web-content-data").width($("#nl2cmd-web-content-panel").width());
		},
		west__onclose_end: function() {
		    $("#nl2cmd-web-content-panel").width($("body").width());
		    $("#web-content-data").width($("#nl2cmd-web-content-panel").width());
		},
		center__onresize_end: function () {
		    if (west__isClosed) {
		        $("#nl2cmd-web-content-panel").width($("body").width());
		    } else {
		        $("#nl2cmd-web-content-panel").width($("body").width()-$("#nl2cmd-web-working-panel").width());
		    }
		    $("#web-content-data").width($("#nl2cmd-web-content-panel").width());
    	}
    }
	myLayout = $('body').layout(vertical_split_layout_setting);

	// inlining the web page to work on, if the page is not able to be display, 
	// show the url and ask the user to collect data on the target page

	// this tries to load the page
    $("#nl2cmd-web-content-panel")
        .html('<object id="web-content-data" width="100%" height="85%" data="' + page_url + '"/>'
    		+ '<div id="web-content-data-error" class="error_report" height="100%">'
            + '<p class="lead" id="error_info">If the page is not successfully loaded, '
            +                                 'click '
            + '<a class="lead" id="nl2cmd-new-tab-link" href="'+ page_url + '" target="_blank">'
            + 'here '
            + '</a>'
            + 'and view it in another tab. '
            + 'Otherwise, you may '
            + '<a id="hide-error-message">'
            + 'hide this message'
            + '</a>'
            + '.'
      	    + '</div>' );

    $("#web-content-data").width($("#nl2cmd-web-content-panel").width());
    $("#hide-error-message").click(function() {
        $('#web-content-data').height($('body').height());
        $('#web-content-data-error').hide();
    });
    $("#nl2cmd-new-tab-link").click(function() {
        myLayout.sizePane('west', $('body').width());
    });


    /* --- Input Panel Management ---*/
    for (var i = 0; i < 1; i ++)
	    insert_pair_collecting_row();

    // when the columns are almost full, add content into the table.
    // this method checks every 500ms to to increase the table size
	setInterval(function() {
	if (!being_submitted) {
        var all_rows = $(".nl2cmd-pair-row");
        var blank_cell_count = 0;

        for (var i = 1; i <= row_count; i ++) {
            var cmd = $("#nl2cmd-row-no-" + i + " .nl2cmd-cmd").val();
            var pair = $("#nl2cmd-row-no-" + i + " .nl2cmd-text").val();

            if (cmd == "" || pair == "")
                blank_cell_count ++;
        }

        if (blank_cell_count == 0)
            insert_pair_collecting_row();
        }
	}, 500);

	$("#nl2cmd-submit").click(function() {
        // spellchecker.check();
        being_submitted = true;
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
                  being_submitted = false;
              }
            }]
          });
        } else {
            BootstrapDialog.show({
              message: "Submit and continue to the next page?",
              buttons: [
              {
                label: 'Yes',
                cssClass: 'btn-primary',
                action: function(dialogItself){
                  $.ajax({
                        url: "add-pairs",
                        data: {"pairs": JSON.stringify(collected_pairs)},
                          success:  function(data, status) {
                          console.log("yoo!" + data);
                        }
                      });
                  redirect_to_next(dialogItself)
                }
              }, {
                label: 'Close',
                action: function(dialogItself){
                    being_submitted = false;
                    dialogItself.close();
                }
              }]
            });
        }
        return false;
    });

	$("#nl2cmd-report-nopair").click(function() {
		console.log("nopair! " + page_url);
	    being_submitted = true;
        remove_row(row_count);

        var num_annotations = collect_annotations();
        var no_pair_warning = "Are you sure there is no pair on this page and want to work on a new page?";
        if (num_annotations != 0) {
            no_pair_warning = 'You have chose the "No pair" option, anything you put in the collection entries will '
                              + 'be discarded. Still want to proceed to a new page?';
        }
		BootstrapDialog.show({
          message: no_pair_warning,
          buttons: [
          {
              label: 'Yes',
              cssClass: 'btn-primary',
              action: function(dialogItself){
                $.ajax({
                      url: "no_pairs",
                      data: {"url": page_url},
                      success:  function(data, status) {
                        console.log("Yea!" + data);
                      }
                });
                redirect_to_next(dialogItself);
              }
          }, {
              label: 'Close',
              action: function(dialogItself){
                  being_submitted = false;
                  dialogItself.close();
              }
          }]
	    });
      return false;
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

      /* --- User log out --- */
      $('#user-log-out').click(function() {
        $.ajax({url: "logout_user",
             data: {"user_id": user_id},
             success:  function(data, status) {
                  console.log("User " + username_prefix + user_id.toString()
                                + " successfully log out.");
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

function redirect_to_next(dialog) {
    var query = "";
    // retrieve current search query
    $.getJSON("get_search_query", function(search_query) {
        query = search_query;
    });

    $.getJSON("pick_url", {search_phrase: query}, function(url) {
      console.log(url);
      if (url === null) {
        alert('Congrats! You completed annotations of all webpages retrieved by the current search query: '
              + '"' + query + '".');
        window.location.href = "/search.html";
      } else {
        dialog.close();
        window.location.replace("./collect_page.html?url=" + url);
      }
    });

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
  			+ 	 '<textarea type="text" class="nl2cmd-box nl2cmd-text form-control vresize" spellcheck="false" placeholder="Description" />'
  			+ '</div>'
  			+ '</td></tr>');    // default html textarea spellcheck disabled

  	$("").append()
}

function getSelectedText(e) {
    selected_text = (document.all) ? document.selection.createRange().text :
                    document.getSelection();
    $("#nl2cmd-row-no-1 div .nl2cmd-cmd").val(selected_text);
}
