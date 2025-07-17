function next_page_report(page_no) {

var searchParams = new URLSearchParams(window.location.search);
    searchParams.set("page_no", page_no);
    window.location.search = searchParams.toString();
}