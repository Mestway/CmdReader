$(document).ready(function () {
  $('#nl2cmd-keyword-search-button').click(function () {
    var search_query = $('#nl2cmd-keyword-search-box').val();
    console.log(search_query);
	});

	$('#nl2cmd-auto-redirect').click(function () {
    var url = $.get( "/service", function( data ) {
		  console.log(data);
		});
	});
});
