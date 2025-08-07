function change_upload_form_view(element_id)
{
    console.log(element_id);
    var element_name =  element_id.slice(3);
    var item_val = document.getElementById(element_id).value;


    if ('URLSearchParams' in window) {
        var searchParams = new URLSearchParams(window.location.search);
        searchParams.set(element_name,item_val);
        if(item_val=='_'){
            searchParams.delete(element_name);
        }
        if(element_name=='phase'){
            if(searchParams.has('document_type')){
                searchParams.delete('document_type');
            }

        }
        window.location.search = searchParams.toString();
    }
}
function change_search_form_view() {
    var doc_type = document.getElementById("type_of_doc").value;

    document.getElementById("wd_fields").style.display = "none";
    document.getElementById("wep_fields").style.display = "none";
    document.getElementById("iic_fields").style.display = "none";
    document.getElementById("comdoc_fields").style.display = "none";

    if (doc_type == "Working Documentation") {
        document.getElementById("wd_fields").style.display ="table-row-group";
    }
    if (doc_type == "Work Execution Plan") {
        document.getElementById("wep_fields").style.display = "table-row-group";
    }
    if (doc_type == "Incoming Inspection Control") {
        document.getElementById("iic_fields").style.display = "table-row-group";
    }
    if (doc_type == "Commissioning Documents") {
        console.log("Com Doc");
        document.getElementById("comdoc_fields").style.display = "table-row-group";
    }
}
function clearForm() {
    console.log("clear_form");
}

function getDate() {
    var today = new Date();
    document.getElementById("upload_date").value = today.toLocaleDateString();

}


function add_more_rows_for_files()
{
    var table = document.getElementById("file_table");
    var rows = table.rows.length;
    var count = rows + 1;
    var row_id = "file_"+count;

    var tr = document.createElement("tr");
    tr.style = "border: black 1px solid";
    var td = document.createElement("td");

    var inp = document.createElement("input");
    inp.type = "file";
    inp.id = row_id;
    inp.name = row_id;
    inp.id = row_id;
    inp.onchange = function(){
        getFileInfo(row_id);

    };

    var hidden_td = document.createElement("td");
    hidden_td.hidden = true;
    var hash_inp = document.createElement("input");
    var hash_id = "file_"+count+"_hash";
    hash_inp.type = "text";
    hash_inp.id = hash_id;
    hash_inp.name = hash_id;
    hash_inp.onchange = function(){
        check_file_existance(this.value);
    }

    hidden_td.appendChild(hash_inp);

    td.appendChild(inp);
    tr.appendChild(td);
    tr.appendChild(hidden_td);
    table.appendChild(tr);
}

function validate_and_submit()
{
    console.log("Hellow");
    var node_list = document.querySelectorAll("input[type=file]");

    for (var i=0;i<node_list.length;i++)
    {
        var file_id = node_list[i].id;

        if(document.getElementById(file_id).files.length==0){
            alert("File missing! Please add files");
            return;
        }
    }
    document.getElementById("document_form").submit();
}