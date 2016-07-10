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

    $('#user-record-milestone').click(function() {
        var user_id = $('#userid').val()
        console.log(user_id)
        $.ajax({url: "user_record_milestone",
                data: {"user_id": user_id},
                success:  function(time_stamp) {
                    if (time_stamp < 1)
                        alert("User " + user_id + " doesn't exist!");
                    else
                        alert("User " + user_id + " has completed " + time_stamp + " milestones!");
                }
        });
    });
});