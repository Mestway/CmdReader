$(document).ready(function () {
    var username_prefix = "nl2cmd";
    var user_id = -1;

    $('#new-user-registration').click(function() {
        BootstrapDialog.show({
            title: "Please tell us a bit more about yourself:",
            message: $('<div class="modal-body">'
                      +  '<form role="form">'
                      + '<div class="form-group">'
                      +    '<input type="firstname" class="form-control"'
                      +    'id="inputFirstName" placeholder="First Name"/>'
                      + '</div>'
                      + '<div class="form-group">'
                      +    '<input type="lastname" class="form-control"'
                      +        'id="inputLastName" placeholder="Last Name"/>'
                      + '</div>'
                      + '<span id="notification"></span>'
                      + '</form></div>'),
            modal:true,
            buttons: [{
                label: "Submit",
                cssClass: "btn-primary",
                action: function(dialogItself) {
                    var firstname = $('#inputFirstName').val();
                    var lastname = $('#inputLastName').val();
                    if (firstname.length === 0) {
                        $('#notification').text("Please don't leave first name empty.");
                    } else if (lastname.length === 0) {
                        $('#notification').text("Please don't leave last name empty.");
                    } else {
                        $.getJSON("count_current_users", function(num_users) {
                            // register user in the backend
                            user_id = num_users;
                            $.ajax({url: "register_user",
                                    data: {"user_id": user_id, "first_name": firstname, "last_name": lastname},
                                    success:  function(data, status) {
                                                console.log("User " + username_prefix + user_id.toString()
                                                + " created.");
                                    }
                            });
                            // confirm
                            BootstrapDialog.show({
                                title: "Login Information",
                                message: "Your access code: <b>" + username_prefix + user_id.toString() + "</b>",
                                buttons: [{
                                    label: "Got it",
                                    cssClass: "btn-primary",
                                    action: function(dialogItself) {
                                        dialogItself.close();
                                    }
                                }]
                            });
                        });
                        dialogItself.close()
                    }
                }
            }]
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
