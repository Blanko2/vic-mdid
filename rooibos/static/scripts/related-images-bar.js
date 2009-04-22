var relatedImagesEnabled = false;

function showRelatedImages(querystring) {
    if (relatedImagesEnabled) {
        querystring += "&ps=5";    
        $.ajax({
            mode: 'queue',
            type: 'GET',
            url: '/explore/api/search/?' + querystring,
            dataType: 'json',
            success: function(r) {
                    $("#related-images-bar-content").html(r.html);
                    bindSelectRecordCheckboxes();
                }
        });
    }
}

function clearRelatedImages() {
    if (relatedImagesEnabled) {
        $("#related-images-bar-content").empty();
    }
}

function enableRelatedImages() {    
    var adjust = function() { $("#related-images-bar").width($(window).width()); };
    var toggle = function() { $("#related-images-bar, #related-images-bar-placeholder").
                                 height(158 - $("#related-images-bar").height()); };
    $(window).resize(adjust);
    $(window).scroll(adjust);
    adjust();
    $("#related-images-bar-toggle").click(toggle);
    $("#related-images-bar").show()
    $("#related-images-bar-placeholder").height($("#related-images-bar").height());
    relatedImagesEnabled = true;
}
