
function document_preview(hash)
{
    console.log(hash);
    var url = "/docman/document/preview/"+hash;
    window.open(url,"_blank", "toolbar=no,scrollbars=yes,resizable=yes");
}

function open_doc_edit_window(hash)
{
    window.open("/docman/document/edit_document/"+hash,"_blank", "toolbar=yes,scrollbars=yes,resizable=yes width=screen.width, height=screen.height");
}

function delete_document(hash)
{
    window.open("/docman/document/delete/"+hash,"_blank", "toolbar=yes,scrollbars=yes,resizable=yes width=screen.width, height=screen.height");
}

function delete_file(doc_id,file_hash,file_name)
{
    if(confirm("Are you sure to delete: "+file_name))
    {
        console.log("Confirmed by user");
    }
    else{
        return;
    }

    var url = "/docman/document/delete_file/"+doc_id+"/"+file_hash
    post_request(url,null,on_file_delete);

}

function on_file_delete()
{
    if(this.status == 200){
        var jsonOptions = JSON.parse(this.responseText);
        alert(jsonOptions[1]);
        window.location.reload();
    }
}