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
                        // register user in the backend
                        $.ajax({url: "register_user",
                                data: {"first_name": firstname, "last_name": lastname},
                                error: function(request, status, error) {
                                  if (status === null)
                                      alert("Sorry, we caught an HttpError: " + error + ". Please wait for a few seconds and try again.");
                                  else
                                      alert("Sorry, we caught an error: " + status + ". Please wait for a few seconds and try again.");
                                },
                                success:  function(user_id, status) {
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
                                    console.log("User " + username_prefix + user_id.toString()
                                    + " created.");
                                }
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
                window.location.replace("/search.html");
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

    $('#user-forget-access-code').click(function() {
        BootstrapDialog.show({
            title: "You may retrieve access code with your first name and last name:",
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
                        $.getJSON("get_access_code", {first_name: firstname, last_name: lastname}, function(user_id) {
                            if (user_id === -1) {
                                BootstrapDialog.show({
                                    title: "Error retrieving access code",
                                    message: 'User "' + firstname + ' ' + lastname + '" not found. Please make sure your '
                                            + 'spelling is correct. If you continue to have this problem, email '
                                            + '<it>xilin@uw.edu</it>.',
                                    buttons: [{
                                        label: "Got it",
                                        cssClass: "btn-primary",
                                        action: function(dialogItself) {
                                            dialogItself.close();
                                        }
                                    }]
                                });
                            } else {
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
                            }
                        });
                        dialogItself.close()
                    }
                }
            }]
        });
        return false;
    });
});
