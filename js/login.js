$(document).ready(function () {
    var username_prefix = "nl2cmd";
    var user_id = -1;

    $('#create-new-user').click(function() {
        // get current number of users in DB
        $.getJSON("count_current_users", function(num_users) {
            user_id = num_users;
            $.ajax({url: "register_user",
                    data: {"user_id": user_id},
                    success:  function(data, status) {
                                console.log("User " + username_prefix + user_id.toString()
                                + " created.");
                              }
            });
            BootstrapDialog.show({
                message: "You username: " + username_prefix + user_id.toString(),
                buttons: [{
                    label: "Got it",
                    cssClass: "btn-primary",
                    action: function(dialogItself) {
                        dialogItself.close();
                    }
                }]
            });
        });
    });

});