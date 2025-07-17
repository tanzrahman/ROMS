function filter_lecture_tasks_list()
{

    var div = document.getElementById('id_target_division').value;
    var keyword = document.getElementById('id_task_filter').value;
    console.log("filter tasks")
    if ('URLSearchParams' in window) {
        var searchParams = new URLSearchParams(window.location.search);
        if(div!=''){
            searchParams.set('div',div);
        }
        if(keyword!=''){
            searchParams.set('keyword',keyword);
        }
        window.location.search = searchParams.toString();
    }

}