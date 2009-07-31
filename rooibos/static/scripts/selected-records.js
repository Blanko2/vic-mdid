function recordSelection(ids, checked) {
    if (!ids.length) ids = [ids];
    $.ajax({
        mode: 'queue',
        type: 'POST',
        url: '/ui/api/select-record/',
        data: {'id': ids, 'checked': checked},
        dataType: 'json',
        success: function(r) {
                $("#selected-records div[id^=selected-record-]").remove();
                for (i in r.records) {
                    addSelectedRecord(r.records[i].id, r.records[i].img_url, r.records[i].record_url, r.records[i].title);
                }
                $("#session-status").html(r.status);
            }
    })
}

function updateSelectedRecords() {
    recordSelection(0, false);
}

function addSelectedRecord(id, img_url, record_url, title) {
    var img = $("<img>").attr('src', img_url).attr('alt', title).attr('title', title);
    var a = $("<a>").attr('href', record_url).append(img);
    var div = $("<div>").attr('id', 'selected-record-' + id).append(a);
    var checkbox = $("<input type='checkbox' checked='checked'>").click(function() {
            recordSelection(id, false);
            div.remove();            
            $(".record-select[value='" + id + "']").removeAttr("checked");
        });
    div.append(checkbox);
    $("#selected-records").append(div);
}

function adjustSelectedMenuHeight() {
    $("#selected-records").height($(window).height() - 100);
}

function deselectAll() {
    var ids = Array();
    $("#selected-records div[id^=selected-record-]").each(function(i) {
        ids[i] = this.id.substring(16);
        $(".record-select[value='" + ids[i] + "']").removeAttr("checked");
    }).remove();
    recordSelection(ids, false);
}

function exportAll() {
	document.location = "/flickr/export-photo-list"
}

function bindSelectRecordCheckboxes() {
    $(".record-select").click(function() { recordSelection($(this).attr('value'), $(this).attr('checked')); });
}

$(document).ready(function() {
    $("#selected-records-menu").append($('<div class="dropdown">').append($("#selected-records")));
    bindSelectRecordCheckboxes()
    $("#selected-records-deselect-all").click(deselectAll);
    $("#selected-records-export-flickr").click(exportAll);
    $(window).resize(adjustSelectedMenuHeight);
    adjustSelectedMenuHeight();
});
