function  add_person(task_id) {
    window.open("/task_management/add_person/"+task_id, "_blank", "toolbar=yes,scrollbars=yes,resizable=no width=800, height=500");
}

function add_supervisor_feedback(task_id, exc_fb){
    window.open("/task_management/supervisor_feedback/"+task_id+"?exec_fb="+exc_fb, "_blank", "toolbar=yes,scrollbars=yes,resizable=no width=800, height=500");
}

function  add_comment(task_id) {
    window.open("/task_management/add_comment/"+task_id, "_blank", "toolbar=yes,scrollbars=yes,resizable=no width=800, height=500");
}

function consultant_tfb_add_comment(task_id)
{
    window.open("/task_management/consultant_task_feedback_add_comment/"+task_id,"_blank", "toolbar=yes,scrollbars=yes,resizable=no width=800, height=500")
}

function consultant_discussion_add_comment(id)
{
    window.open("/lecture/consultant_qa_add_comment/"+id,"_blank", "toolbar=yes,scrollbars=yes,resizable=no width=800, height=500")
}
function add_consultant_to_task(task_id)
{
    window.open("/task_management/add_task_consultant/"+task_id, "_blank", "toolbar=yes,scrollbars=yes,resizable=no width=800, height=500");
}
function  add_answer(task_id) {
}

function  add_activity(task_id) {
    window.open("/task_management/add_activity/"+task_id, "_blank", "toolbar=yes,scrollbars=yes,resizable=no width=800, height=500");
}

function fetch_assigned_task_list(user_mail)
{
    console.log(user_mail);
    var url = "/task_management/user_task_list/"+user_mail;

    get_request(url,onload_user_tasks);
}

function onload_user_tasks()
{
    if (this.status == 200) {

        var json_data = JSON.parse(this.responseText);
        console.log(json_data)
        var textBox = document.getElementById('details');

        textBox.value="";

        console.log(textBox);
        for (var i=0;i<json_data.length; i++){
                if(i==0){
                    textBox.value+=json_data[i]['user']+"\n";
                    textBox.value+="Total Tasks In Next 30 Days: "+json_data[i]['total_tasks']+"\n";
            }
            else{
                textBox.value+=(json_data[i]['task_id']+",  "+json_data[i]['planned_start_date']+"\n");
            }
        }

        document.getElementById('dialog').style.display='block';
    }
    console.log("User Tasks Loaded");
}
async function get_user_task_list(user_mail)
{
    var url = "/task_management/user_task_list/"+user_mail;

    get_request(url,onload_user_tasks);

}

function on_load_task_names()
{
     if (this.status == 200) {
         var select_elem = document.getElementById('id_tasks_options');
         var select = document.getElementById("id_tasks");
        //clear elements
          while (select_elem.firstChild) {
            select_elem.removeChild(select_elem.lastChild);
          }
          for (var i=select.options.length-1; i>=0 ;i--)
          {
              select.remove(i);
          }
         var json_data = JSON.parse(this.responseText);
         for (var i=0; i<json_data.length;i++) {
             var div = document.createElement('div',"data-selectable");
             div.className = "option";
             div.setAttribute("data-selectable","")
             div.setAttribute("data-value",json_data[i][0]);
             div.innerHTML = json_data[i][1];
             select_elem.appendChild(div);

             var opt = document.createElement('option')
             opt.value=json_data[i][0];
             opt.text=json_data[i][1];
             select.appendChild(opt);
         }
         // document.getElementsByClassName("multi selectize-dropdown")[0].style.display="block";
     }
}

function suggest_task_names(value) {
    console.log(value);
    var url = "/task_management/suggest_task/"+value;
    get_request(url,on_load_task_names)
}

function on_load_task_details()
{
    if (this.status == 200) {

        var json_data = JSON.parse(this.responseText);
        console.log(json_data)
        var textBox = document.getElementById('details');

        textBox.value=json_data;
        document.getElementById('dialog').style.display='block';
    }
}
function fetch_task_details(id)
{
    console.log(id);

    var url = "/task_management/task_details/"+id;
    get_request(url,on_load_task_details)
}

function download_task_report()
{
    var searchParams = new URLSearchParams(window.location.search);
    searchParams.set('download','excel');
    console.log(searchParams.toString());
    window.location.search = searchParams.toString();
    //document.getElementById('task_search_form').submit();
}
function post_request(url, data, on_load_function) {
    var csrf_token = document.getElementsByName("csrfmiddlewaretoken")[0].value;

    post_xhttp = new XMLHttpRequest();
    post_xhttp.open("POST", url, true);
    post_xhttp.setRequestHeader('Content-type', 'application/json; charset=utf-8');
    post_xhttp.setRequestHeader('X-CSRFToken', csrf_token);
    post_xhttp.send(data);
    post_xhttp.onload = on_load_function;

}

function get_request(url, on_load_function) {
    xhttp = new XMLHttpRequest();
    xhttp.open("GET", url, true);
    xhttp.send();
    xhttp.onload = on_load_function;
}
