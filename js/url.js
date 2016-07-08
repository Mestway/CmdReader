$(document).ready(function () {
    $.ajax({url: "url_opr_history",
        success:  function(html) {
            $('#url-record-panel').html(html);
        }
    });

    $('#url-inspection').click(function() {
        var url = $('#url').val()
        console.log(url)
        $.ajax({url: "url_opr_history",
                data: {"url": url},
                success:  function(data) {
                    var url = data[0];
                    var html = data[1];
                    $('#url').val(url);
                    $('#url-record-panel').html(html);
                }
        });
    });
});