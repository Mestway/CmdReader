$(document).ready(function () {
    var username_prefix = "nl2cmd";
    var user_id = -1;

    $('#create-new-user').click(function() {
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
                message: "Your username: " + username_prefix + user_id.toString(),
                buttons: [{
                    label: "Got it",
                    cssClass: "btn-primary",
                    action: function(dialogItself) {
                        dialogItself.close();
                    }
                }]
            });
        });
        return false;
    });

    $('#user-log-in').click(function() {
        var username = $('#username').val();
        $.getJSON("user_login", {username: username}, function(login_success) {
            if (login_success) {
                console.log("login_success");
                window.location.href = "/search.html";
            } else {
                BootstrapDialog.show({
                message: "User " + username + " does not exist. Please make sure the username is correct.",
                buttons: [{
                    label: "Got it",
                    cssClass: "btn-primary",
                    action: function(dialogItself) {
                        dialogItself.close();
                    }
                }]
                });
           }
        });
        return false;
    });
});
