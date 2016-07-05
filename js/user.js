$(document).ready(function () {
    $('#user-inspection').click(function() {
        var user_id = $('#userid').val()
        console.log(user_id)
        $.ajax({url: "user_record",
                data: {"user_id": user_id},
                success:  function(html) {
                    $('#user-record-panel').html(html);
                }
        });
    });
});