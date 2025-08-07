function select_group_to_manage(element_id)
{
    console.log(element_id);
    var element_name =  element_id.slice(3);
    var item_val = document.getElementById(element_id).value;

    if ('URLSearchParams' in window) {
        var searchParams = new URLSearchParams(window.location.search);
        searchParams.set(element_name,item_val);
        if(item_val == ""){
            searchParams = "";
        }
        window.location.search = searchParams.toString();
    }

}

function delete_group()
{
    var index  = document.getElementById("id_group").selectedIndex;
    var group_name = document.getElementById('id_group').options[index].text;
    var confirmation = "";

    if(index !=0){
        if (confirm("Sure to Delete Group: " + group_name + " ?")) {
                confirmation = "Yes";
            } else {
                confirmation = "No";
            }

        if(confirmation == "Yes"){
             if ('URLSearchParams' in window) {
                var searchParams = new URLSearchParams(window.location.search);
                searchParams.set("delete","true");
                window.location.search = searchParams.toString();
            }
        }
    }
}