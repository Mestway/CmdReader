var myLayout;
var row_count = 0;
var page_url = "";

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

  $("#nl2cmd-web-content-panel")
      .html('<object id="web-content-data" height="100%" data="' + page_url + '"/>');
  $("#web-content-data").width($("#nl2cmd-web-content-panel").width());

  for (var i = 0; i < 5; i ++)
  	insert_pair_collecting_row();

	setInterval(function() {
  	var all_rows = $(".nl2cmd-pair-row");
  	var blank_cell_count = 0;

  	for (var i = 1; i <= row_count; i ++) {
  		var cmd = $("#nl2cmd-row-no-" + i + " .nl2cmd-cmd").val();
  		var pair = $("#nl2cmd-row-no-" + i + " .nl2cmd-text").val();

  		if (cmd == "" && pair == "")
  			blank_cell_count ++;
  	}

  	if (blank_cell_count == 0)
  		insert_pair_collecting_row();
	}, 500);

	$("#nl2cmd-submit").click(function() {
		var collected_pairs = [];
		for (var i = 1; i <= row_count; i ++) {
  		var cmd = $("#nl2cmd-row-no-" + i + " div .nl2cmd-cmd").val();
  		var text = $("#nl2cmd-row-no-" + i + " div .nl2cmd-text").val();
  		console.log
  		var data_entry = {"cmd":cmd, "nl":text, url:"uwplse.org"};
  		collected_pairs.push(data_entry);
  	}
  	
  	console.log(collected_pairs);

  	// TODO: deal with the communication to the server
  	$.ajax({
		  url: "/add-pairs",
		  data: {"pairs": JSON.stringify(collected_pairs)},
		   success:  function(data, status) {
		  	console.log("yoo!" + data);
		  }
		});
	});

	$("#nl2cmd-report-nopair").click(function() {
		console.log("nopair!");
		console.log(page_url);
		
		$.ajax({
		  url: "/no_pairs",
		  data: {"url": page_url},
		  success:  function(data, status) {
		  	console.log("Yea!" + data);
		  }

		});

	});
});

function insert_pair_collecting_row() {
	row_count ++;
	$("#nl2cmd-pair-collect-table tbody").append(
  			'<tr class="nl2cmd-pair-row"><th scope="">'
  			+ row_count 
  			+ '</th><td id="' + "nl2cmd-row-no-" + row_count + '" class="nl2cmd-pair-td">'
  			+ '<div class="input-group">'
  			+    '<span class="input-group-addon nl2cmd-span" id="basic-addon1">cmd</span>'
  			+ 	 '<input type="text" class="nl2cmd-box nl2cmd-cmd form-control" placeholder="Command" />'
  			+ '</div>'
  			+ '<br/>'
  			+ '<div class="input-group">'
  			+    '<span class="input-group-addon nl2cmd-span basic-addon1">txt</span>'
  			+ 	 '<textarea type="text" class="nl2cmd-box nl2cmd-text form-control vresize" placeholder="Description" />'
  			+ '</div>'
  			+ '</td></tr>');
}
