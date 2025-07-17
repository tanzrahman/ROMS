function verify_ans_choice(id) {

    var val = document.getElementById(id).value;

    if (val == 'Yes') {
        //enable next answer
        var nid = parseInt(id.split('_')[1]) + 1
        var next_ans_id = "answer_" + nid;
        console.log(next_ans_id);
        document.getElementById(next_ans_id).disabled = false;
    }
    if (nid == 2) {
        //enable all the remaining field
        for (var i = 2; i <= 6; i++) {
            if (i == 4) {
                //skip the conditional question
                continue;
            }
            var next_ans_id = "answer_" + i;
            document.getElementById(next_ans_id).disabled = false;
        }
    }
}

function verify_ans_length(id, char_limit) {

    var val = document.getElementById(id).value;

    if (val.length >= char_limit) {
        //enable next answer
        var nid = parseInt(id.split('_')[1]) + 1
        var next_ans_id = "answer_" + nid;
        console.log(next_ans_id);
        document.getElementById(next_ans_id).disabled = false;
    }
}

function verify_ans_value(id, value) {
    var val = parseInt(document.getElementById(id).value);

    var nid = parseInt(id.split('_')[1]) + 1
    var next_ans_id = "answer_" + nid;
    if (nid == 13) {
        //enable submit button
        document.getElementById('submit_btn').disabled = false;
        return
    }
    if (val >= value) {
        //enable next answer
        console.log(next_ans_id);
        document.getElementById(next_ans_id).disabled = false;
    }

}

function verify_choice_visible_next(id) {
    var val = document.getElementById(id).value;

    if (val == 'No') {

        document.getElementById('q4').hidden = true;
    }
    if (val == 'Yes') {
        document.getElementById('q4').hidden = false;
        document.getElementById('answer_4').disabled = false;
    }
}

function verify_all_and_enable_submit() {
    var failed = false;
    for (var i = 1; i <= 6; i++) {
        var ans_id = "answer_" + i
        var item = document.getElementById(ans_id);
        if (item.disabled == false) {
            if (item.value == null || item.value == "") {
                console.log(ans_id);
                failed = true;
                alert("Please full-fill all the feedback questions");
                break;
            }
            if (i == 4 || i == 6) {
                var ans_len = item.value.length;
                if (ans_len < 200) {
                    if (i == 8) {
                        failed = true;
                        alert("Key differences between versions should be at least 200 character long");
                        continue;
                    }
                }
                if (i == 6) {
                    if (ans_len < 50) {
                        failed = true;
                        alert("Assessment of executor should be at least 50 characters.");
                        continue;
                    }
                }
            }
        }
    }
    if(failed == false){
        document.getElementById("sup_fb").submit();
    }

}