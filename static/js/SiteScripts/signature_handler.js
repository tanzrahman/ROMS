function load_signature_from_selected_file(field_id) {
    document.getElementById("my_signature").hidden = false;
    var selectedFile = document.getElementById("signature_file").files[0];
    var reader = new FileReader();
    var imgtag = document.getElementById("my_signature");

    var ok = true;
    imgtag.title = selectedFile.name;
    reader.onload = function (event) {
        imgtag.src = event.target.result;
    };
    reader.readAsDataURL(selectedFile);

    imgtag.onload = function handleLoad() {
        console.log(`Width: ${imgtag.naturalWidth}, Height: ${imgtag.naturalHeight}`);

        if (imgtag.naturalWidth > 200 || imgtag.naturalHeight > 100) {
            document.getElementById("my_signature").hidden = true;
            document.getElementById("signature_file").files[0] = null;
            alert(`Image Size (Width: ${imgtag.naturalWidth}, Height: ${imgtag.naturalHeight})  crossed the allowed limit`);

        }
        else
        {
            getFileInfo(field_id);
        }
    }
}