$(document).ready(function() {
    $(".removetag").click(function() {
        var span = $(this).parent();
        ajaxManager.add({
            type: 'POST',
            url: this.href,
            dataType: 'json',
            success: function(r) { span.css('visibility', 'hidden'); }
        });
        return false;
    });
});