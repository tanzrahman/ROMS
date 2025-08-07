
function getFileInfo(elem_hash_id)
{
    var reader = new FileReader(); //define a Reader

    console.log(elem_hash_id);
    var elem_id = elem_hash_id + "_file"

    var file = document.getElementById(elem_id).files[0]; //get the File object

    if (!file) {
        alert("no file selected");
        return;
    } //check if user selected a file

    reader.onload = function (f) {
        var file_result = this.result;
        var file_wordArr = CryptoJS.lib.WordArray.create(file_result); 
        var sha1_hash = CryptoJS.SHA1(file_wordArr); //calculate SHA1 hash
        document.getElementById(elem_hash_id).value = sha1_hash.toString();
        //check_file_existance(sha1_hash.toString());

    };
    reader.readAsArrayBuffer(file); //read file as ArrayBuffer
}

function check_file_existance(file_hash)
{
    var data = {
        "type":"file_existance",
        "file_hash":file_hash,
    }
    data = JSON.stringify(data);
    var url = '/docman/api';

    post_request(url,data,if_file_exists)
}

function if_file_exists()
{
    if(this.status == 200){
        var jsonOptions = JSON.parse(this.responseText);
        console.log(jsonOptions[0]);
        if(jsonOptions[0] == "True"){
            alert("file already exists");
        }

    }
}
function post_request(url, data, onload_function) {
    var csrf_token = document.getElementsByName("csrfmiddlewaretoken")[0].value;
    post_xhttp = new XMLHttpRequest();
    post_xhttp.open("POST", url, true);
    post_xhttp.setRequestHeader('Content-type', 'application/json; charset=utf-8');
    post_xhttp.setRequestHeader('X-CSRFToken', csrf_token);
    post_xhttp.send(data);
    post_xhttp.onload = onload_function;
}

function get_request(url,data, on_load_function) {
    xhttp = new XMLHttpRequest();
    xhttp.open("GET", url, true);
    xhttp.send(data);
    xhttp.onload = on_load_function;
}