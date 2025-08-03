function multiSearchKeyup(inputElement) {
    if(event.keyCode === 13) {
        var actual_element_id = inputElement.id;
        actual_element_id = actual_element_id.split("__")[0];
        var actual_element = document.getElementById(actual_element_id);
        actual_element.value = actual_element.value+inputElement.value.trim()+";"
        inputElement.parentNode.insertBefore(createFilterItem(inputElement.value), inputElement);
        inputElement.value = "";
    }
    function createFilterItem(text) {
        const item = document.createElement("div");
        item.setAttribute("class", "multi-search-item");
        const span = `<span>${text}</span>`;
        const close = `<div class="fa fa-close" onclick="this.parentNode.remove()"></div>`;
        // TODO: add support when a word is removed
        item.innerHTML = span+close;
        return item;
    }
}

function  enable_tagging_mode(element_id)
{
    console.log(element_id);

    var element = document.getElementById(element_id);
    element.style.display="none";
    var id=element.id+"__tagit";

    var element_string = '<textarea name="'+name+'" cols="40" rows="1" size="10" onkeyup="multiSearchKeyup(this)" placeholder="Press Enter after each keyword" id="'+id+'"></textarea>';

    var templete = document.createElement("template");
    element_string=element_string.trim();
    templete.innerHTML=element_string;

    console.log(element_string);

    element.parentNode.appendChild(templete.content.firstChild);

    document.getElementById(id).focus();

}