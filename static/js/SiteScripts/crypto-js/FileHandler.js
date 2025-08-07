
function getFileInfo() 
{
    var reader = new FileReader(); //define a Reader

    var file = $("#file")[0].files[0]; //get the File object 
    if (!file) {
        alert("no file selected");
        return;
    } //check if user selected a file

    reader.onload = function (f) {
        var file_result = this.result; // this == reader, get the loaded file "result"
        var file_wordArr = CryptoJS.lib.WordArray.create(file_result); 
        var sha1_hash = CryptoJS.SHA1(file_wordArr); //calculate SHA1 hash
        alert("Calculated SHA1:" + sha1_hash.toString()); //output result
    };
    reader.readAsArrayBuffer(file); //read file as ArrayBuffer

}