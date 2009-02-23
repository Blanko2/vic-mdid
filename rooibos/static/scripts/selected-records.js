function recordSelection(id, checked) {
    $.ajax({
        mode: 'queue',
        type: 'POST',
        url: '/ui/api/select-record/',
        data: {'id': id, 'checked': checked},
        dataType: 'json',
        success: function(r) { if (checked) addSelectedRecord(r.id, r.img_url, r.record_url, r.title);
                                $("#session-status").html(r.status); }
    })
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

$(document).ready(function() {
    $("#selected-records-menu").append('<div class="dropdown"><div id="selected-records" class="menu"></div></div>');
    $(".record-select").click(function() { recordSelection($(this).attr('value'), $(this).attr('checked')); });
    $(window).resize(adjustSelectedMenuHeight);
    adjustSelectedMenuHeight();
});
