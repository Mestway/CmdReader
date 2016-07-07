$(document).ready(function () {
    $('#url-inspection').click(function() {
        var url = $('#url').val()
        console.log(url)
        $.ajax({url: "url_opt_history",
                data: {"url": url},
                success:  function(html) {
                    $('#url-record-panel').html(html);
                }
        });
    });
});