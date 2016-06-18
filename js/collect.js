var myLayout;
var row_count = 0;
var page_url = "";
var selected_text = "";
var being_submitted = false;

$(document).ready(function(){

	$.urlParam = function(name){
		var results = new RegExp('[\?&]' + name + '=([^&#]*)').exec(window.location.href);
		if (results == null)
			return "http://www.uwplse.org";
		return results[1] || 0;
	}

	// example.com?param1=name&param2=&id=6
	page_url = $.urlParam('url'); // name
	console.log(page_url);

	myLayout = $('body').layout({
		east__minSize: 200,
		east__size:	"60%",
		east__onresize_end: function () {
    	$("#web-content-data").width($("body").width()-$("#nl2cmd-web-working-panel").width())
    },
	});

	// inlining the web page to work on, if the page is not able to be display, 
	// show the url and ask the user to collect data on the target page

	// this tries to load the page
    $("#nl2cmd-web-content-panel")
        .html('<object id="web-content-data" height="85%" data="' + page_url + '"/>'
    		+'<div id="web-content-data" class="error_report" height="100%">'
            + '<p class="lead" id="error_info">If the page is not successfully loaded,'
            +                                 'open the following link and view it in another tab.'
            + '<a class="lead" id="nl2cmd-new-tab-link" href="'+ page_url + '" target="_blank">' + page_url + '</a></p>'
      	    + '</div>');
    $("#web-content-data").width($("#nl2cmd-web-content-panel").width());

    $("#nl2cmd-web-content-panel").click(function() {
        $("#nl2cmd-web-content-panel").hide()
    });

    // tries to set the page to
    /* if (true) {
		web_content_data.width($("#nl2cmd-web-content-panel").width());
    } else {
	   $("#nl2cmd-web-content-panel")
      .html('<div id="web-content-data" class="error_report" height="100%">' 
      	+ '<h1>We are sorry!!</h1>'
        + '<p class="lead">We are unable to inline the page in this working panel, please copy and open the following link in another browser tab to collect data.'
        + '<br/><a class="lead" href="'+ page_url + '">' + page_url + '</a></p>'
      	+ '</div>');
	   }*/

  for (var i = 0; i < 5; i ++)
	    insert_pair_collecting_row();

    // when the columns are almost full, add content into the table.
    // this method checks every 500ms to to increase the table size
	setInterval(function() {
  	var all_rows = $(".nl2cmd-pair-row");
  	var blank_cell_count = 0;

  	for (var i = 1; i <= row_count; i ++) {
  		var cmd = $("#nl2cmd-row-no-" + i + " .nl2cmd-cmd").val();
  		var pair = $("#nl2cmd-row-no-" + i + " .nl2cmd-text").val();

  		if (cmd == "" || pair == "")
  			blank_cell_count ++;
  	}

  	if (blank_cell_count == 0 && !being_submitted)
  		insert_pair_collecting_row();
	}, 500);

	$("#nl2cmd-submit").click(function() {

    being_submitted = true;
    var collected_pairs = [];
    var exists_orphan_pair = false;
		for (var i = 1; i <= row_count; i ++) {
      var cmd = $("#nl2cmd-row-no-" + i + " div .nl2cmd-cmd").val();
      var text = $("#nl2cmd-row-no-" + i + " div .nl2cmd-text").val();
      
      if (cmd == "" && text == "")
        $("#nl2cmd-row-tr-" + i).remove();

      if ((cmd == "" && text != "" )|| (cmd != "" && text == ""))
        exists_orphan_pair = true;

      var data_entry = {"cmd":cmd, "nl":text, url:"uwplse.org"};
      collected_pairs.push(data_entry);
    }

    if (exists_orphan_pair) {
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
      return;    
    }

    BootstrapDialog.show({
      message: "Are you sure to submit these pairs and move on to a new page?",
      buttons: [
      {
        label: 'Yes',
        cssClass: 'btn-primary',
        action: function(){
          // TODO: deal with the communication to the server
          $.ajax({
                url: "/add-pairs",
                data: {"pairs": JSON.stringify(collected_pairs)},
                  success:  function(data, status) {
                  console.log("yoo!" + data);
                }
              });
          window.location.replace("/search.html");
        }
      }, {
        label: 'Close',
        action: function(dialogItself){
            dialogItself.close();
            being_submitted = false;
        }
      }]
    });
  });

	$("#nl2cmd-report-nopair").click(function() {
		console.log("nopair! " + page_url);
	
		BootstrapDialog.show({
          message: "Are you sure there is no pair on this page and want to work on a new page?",
          buttons: [
          {
              label: 'Yes',
              cssClass: 'btn-primary',
              action: function(){
                // TODO: deal with the communication to the server
                $.ajax({
                      url: "/no_pairs",
                      data: {"url": page_url},
                      success:  function(data, status) {
                        console.log("Yea!" + data);
                      }
                    });
                    window.location.replace("/search.html");
              }
          }, {
              label: 'Close',
              action: function(dialogItself){
                  dialogItself.close();
              }
          }]
	    });
	 });
});

function getSelectedText(e) {
    selected_text = (document.all) ? document.selection.createRange().text :
                    document.getSelection();
    $("#nl2cmd-row-no-1 div .nl2cmd-cmd").val(selected_text);
}

function insert_pair_collecting_row() {
	row_count ++;
	$("#nl2cmd-pair-collect-table tbody").append(
  			'<tr class="nl2cmd-pair-row" id="' + "nl2cmd-row-tr-" + row_count + '"><th scope="">'
  			+ row_count 
  			+ '</th><td id="' + "nl2cmd-row-no-" + row_count + '" class="nl2cmd-pair-td">'
  			+ '<div class="input-group">'
  			+    '<span class="input-group-addon nl2cmd-span" id="basic-addon1">cmd</span>'
  			+ 	 '<input type="text" class="nl2cmd-box nl2cmd-cmd form-control" placeholder="Command" />'
  			+ '</div>'
  			+ '<br/>'
  			+ '<div class="input-group">'
  			+    '<span class="input-group-addon nl2cmd-span basic-addon1">txt</span>'
  			+ 	 '<textarea type="text" class="nl2cmd-box nl2cmd-text form-control vresize" spellcheck="true" placeholder="Description" />'
  			+ '</div>'
  			+ '</td></tr>');
}
