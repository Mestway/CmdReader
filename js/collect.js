var myLayout;

var page_url = "";

var selected_text = "";

var row_count = 0;
var collected_pairs = [];
var being_submitted = false;

$(document).ready(function(){

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

    var default_layout_setting = {
		west__minSize: 100,
		west__size:	"40%",
		west__resizable: false,
		center__onresize_end: function () {
    	    $("#web-content-data").width($("body").width()-$("#nl2cmd-web-working-panel").width())
    	}
    }

	myLayout = $('body').layout(default_layout_setting);

	// inlining the web page to work on, if the page is not able to be display, 
	// show the url and ask the user to collect data on the target page

	// this tries to load the page
    $("#nl2cmd-web-content-panel")
        .html('<object id="web-content-data" height="85%" data="' + page_url + '"/>'
    		+'<div id="web-content-data-error" class="error_report" height="100%">'
            + '<p class="lead" id="error_info">If the page is not successfully loaded,'
            +                                 'open the following link and view it in another tab.'
            + '<a class="lead" id="nl2cmd-new-tab-link" href="'+ page_url + '" target="_blank">' + page_url + '</a></p>'
      	    + '</div>');
    $("#web-content-data").width($("#nl2cmd-web-content-panel").width());

    $("#nl2cmd-new-tab-link").click(function() {
        // $("#nl2cmd-web-content-panel").hide();
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
              message: "Are you sure to submit these pairs and move on to a new page?",
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

	 });

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
        window.location.href = "./collect_page.html?url=" + url;
      }
    });
}

function insert_pair_collecting_row() {
	row_count ++;
	$("#nl2cmd-pair-collect-table tbody").append(
  			'<tr class="nl2cmd-pair-row" id="' + "nl2cmd-row-tr-" + row_count + '"><th scope="">'
  			+ row_count 
  			+ '</th><td id="' + "nl2cmd-row-no-" + row_count + '" class="nl2cmd-pair-td">'
  			+ '<div class="input-group">'
  			+    '<span class="input-group-addon nl2cmd-span" id="basic-addon1">cmd</span>'
  			+ 	 '<input type="text" class="nl2cmd-box nl2cmd-cmd form-control" spellcheck="false" placeholder="Command" />'
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
