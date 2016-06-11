var myLayout;


$(document).ready(function(){

	myLayout = $('body').layout({
		west__minSize:	200,
		west__size:	"40%",
		west__onresize_end: function () {
    	$("#web-content-data").width($("body").width()-$("#nl2cmd-web-working-panel").width())
    	console.log($("body").height);
    },

	});

  $("#nl2cmd-web-content-panel")
      .html('<object id="web-content-data" height="100%" data="http://www.uwplse.org"/>');
  $("#web-content-data").width($("#nl2cmd-web-content-panel").width());
});
