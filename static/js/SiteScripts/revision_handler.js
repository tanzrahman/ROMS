function show_add_files_div(hash)
{
    //document.getElementById("add_revision").style.display = 'block';
    window.open("/docman/document/add_files/"+hash,"_blank", "toolbar=yes,scrollbars=yes,resizable=yes width=screen.width, height=screen.height");
}
function calculate_revision_file_hash()
{
    var file = document.getElementById("revesion_file").files[0]; //get the File object
    var reader = new FileReader(); //define a Reader

    reader.onload = function (f) {
        var file_result = this.result;
        var file_wordArr = CryptoJS.lib.WordArray.create(file_result);
        var sha1_hash = CryptoJS.SHA1(file_wordArr); //calculate SHA1 hash
        console.log(sha1_hash.toString());
        document.getElementById("revision_file_hash").value = sha1_hash.toString();
    };
    reader.readAsArrayBuffer(file); //read file as ArrayBuffer
}
function calculate_hash(field_id)
{
    console.log(field_id);

    var reader = new FileReader(); //define a Reader

    var file = document.getElementById(field_id).files[0]; //get the File object

    if (!file) {
        alert("no file selected");
        return;
    } //check if user selected a file

    reader.onload = function (f) {
        var file_result = this.result;
        var file_wordArr = CryptoJS.lib.WordArray.create(file_result);
        var sha1_hash = CryptoJS.SHA1(file_wordArr); //calculate SHA1 hash
        var hash_field_id = field_id+"_hash";
        console.log(sha1_hash.toString());
        document.getElementById(hash_field_id).value = sha1_hash.toString();
    };
    reader.readAsArrayBuffer(file); //read file as ArrayBuffer
}
function add_more_rows_for_support_doc()
{
    var table = document.getElementById("support_doc_table");
    var rows = table.rows.length;
    var count = rows + 1;
    var row_id = "support_doc_"+count;

    var tr = document.createElement("tr");
    tr.style = "border: black 1px solid";
    var td = document.createElement("td");

    var inp = document.createElement("input");
    inp.type = "file";
    inp.id = row_id;
    inp.name = row_id;
    inp.id = row_id;
    inp.onchange = function(){
        calculate_hash(row_id);
    };

    var hidden_td = document.createElement("td");
    hidden_td.hidden = true;
    var hash_inp = document.createElement("input");
    var hash_id = "support_doc_"+count+"_hash";
    hash_inp.type = "text";
    hash_inp.id = hash_id;
    hash_inp.name = hash_id;

    hidden_td.appendChild(hash_inp);

    console.log(hidden_td);

    td.appendChild(inp);
    tr.appendChild(td);
    tr.appendChild(hidden_td);
    table.appendChild(tr);
}