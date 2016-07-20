$(document).ready(function () {
    var user_id;
    var judgements;
    var eval_submitted;

    $('#user-eval-results').hide()

    $('#user-inspection').click(function() {
        user_id = $('#userid').val()
        console.log(user_id)
        $.ajax({url: "user_record",
                data: {"user_id": user_id},
                error: function(request, status, error) {
                    if (status === null)
                        alert("Sorry, we caught an HttpError: " + error + ". Please wait for a few seconds and try again.");
                    else
                        alert("Sorry, we caught an error: " + status + ". Please wait for a few seconds and try again.");
                },
                success:  function(data) {
                    var stats_html = data[0];
                    var eval_html = data[1];
                    var record_html = data[2];
                    var precision = data[3];
                    var recall = data[4];
                    $('#user-record-milestone').show();
                    $('#user-stats-panel').html(stats_html);
                    var chart = createPerformanceChart(data[5]);
                    chart.render();
                    $('#user-eval-results').show();
                    console.log(precision);
                    $('#precision').text(precision);
                    console.log(recall);
                    $('#recall').text(recall);
                    $('#f1').text(f1());
                    $('#user-eval-panel').html(eval_html);
                    $('#user-eval-submit').show();
                    $('#user-record-panel').html(record_html);

                    judgements = new Array();
                    eval_submitted = false;
                }
        });
    });

    $('#user-stats-panel').delegate('#user-record-milestone', "click", function() {
        user_id = $('#userid').val()
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

    var num_total = 10;
    $("#user-eval-panel").delegate(".pair-eval-judgement", "change", function() {
        var i = $(this).attr('name');
        var cmd = $("#pair-eval-cmd-" + i).text();
        var text = $("#pair-eval-nl-" + i).text();
        console.log(cmd);
        console.log(text);

        if ($(this).val() === "correct") {
            console.log("correct");
            var data_entry = {"cmd": cmd, "nl": text, "judgement": 1};
            judgements[i] = data_entry;
        } else if ($(this).val() === "partial") {
            console.log("partial");
            var data_entry = {"cmd": cmd, "nl": text, "judgement": 0.5};
            judgements[i] = data_entry;
        } else if ($(this).val() === "wrong") {
            console.log("wrong");
            var data_entry = {"cmd": cmd, "nl": text, "judgement": 0};
            judgements[i] = data_entry;
        };
        // console.log(judgements);
    });

    $("#user-eval-panel").delegate("#user-eval-submit", "click", function() {
        if (eval_submitted) {
            alert("You have already submitted evaluation for this page!");
            return;
        }

        var miss_judgement = false;
        for (var i = 1; i <= num_total; i ++) {
            if (!(i in judgements)) {
                // var cmd = $("#pair-eval-cmd-" + i).text();
                // var text = $("#pair-eval-nl-" + i).text();
                // var data_entry = {"cmd": cmd, "nl": text, "judgement": 0};
                // judgements[i] = data_entry;
                miss_judgement = true;
                alert("Judgement is missing!");
            }
        }

        if (!miss_judgement && !eval_submitted) {
            $.ajax({url: "add_judgements",
                 data: {"user_id": user_id, "judgements": JSON.stringify(judgements)},
                 error: function(request, status, error) {
                    if (status === null)
                        alert("Sorry, we caught an HttpError: " + error + ". Please wait for a few seconds and try again.");
                    else
                        alert("Sorry, we caught an error: " + status + ". Please wait for a few seconds and try again.");
                 },
                 success: function(precision) {
                    $("#precision").text(precision);
                    $("#f1").text(f1());
                    eval_submitted = true;
                 }
            });
        }
    });
});

function f1() {
    var precision = parseFloat($("#precision").text());
    var recall = parseFloat($("#recall").text());
    if (precision === 0)
        return 0;
    else if (recall === 0)
        return 0;
    else if (precision + recall === 0)
        return 0;
    else
        return 2 * precision * recall / (precision + recall);
}