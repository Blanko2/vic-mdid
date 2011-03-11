{% load ui %}

(function() {
var clip;
{% if streaming_server and streaming_media %}
clip = {
{% if flowplayer_key %}
    key: '{{ flowplayer_key }}',
{% endif %}
    clip: {
        autoPlay: {{ autoplay|yesno:"true,false" }},
        url: '{{ streaming_media|escapejs }}',
        provider: 'influxis',
        scaling: 'fit'
    },
    plugins: {
        influxis: {
            url: "{{ server_url }}{% url static 'flowplayer/flowplayer.rtmp-*.swf'|fileversion %}",
            netConnectionUrl: '{{ streaming_server|escapejs }}'
            {% if audio %} ,
            durationFunc: 'getStreamLength'
            {% endif %}
        }
        {% if audio %} ,
        controls: {
            fullscreen: false,
            height: 30,
            autoHide: false
        }
        {% endif %}
    }
};
{% else %}
clip = {
{% if flowplayer_key %}
    key: '{{ flowplayer_key }}',
{% endif %}
    clip: {
        autoPlay: {{ autoplay|yesno:"true,false" }},
        url: '{{ delivery_url|escapejs }}'
        {% if audio %} ,
        type: 'audio'
        {% else %} ,
        scaling: 'fit'
        {% endif %}
    }
    {% if audio %} ,
    plugins: {
        audio: {
            url: "{{ server_url }}{% url static 'flowplayer/flowplayer.audio-*.swf'|fileversion %}"
        },
        controls: {
            fullscreen: false,
            height: 30,
            autoHide: false
        }
    }
    {% endif %}
};
{% endif %}

function insert_flowplayer() {
    var e = document.getElementById("player-{{ record.id }}-{{ selectedmedia.id }}");
    e.style.width = "{{ selectedmedia.width|default:"520" }}px";
    e.style.height = "{% if audio %}30{% else %}{{ selectedmedia.height|default:"330" }}{% endif %}px";
    $f("player-{{ record.id }}-{{ selectedmedia.id }}",
        "{{ server_url }}{% if flowplayer_key %}{% url static 'flowplayer/flowplayer.commercial-*.swf'|fileversion %}{% else %}{% url static 'flowplayer/flowplayer-*.swf'|fileversion %}{% endif %}", clip).ipad();
}

if (typeof(flowplayer) == "function") {
    insert_flowplayer();
} else {
    var e = document.createElement("script");
    e.src = "{{ server_url }}{% url static 'flowplayer/flowplayer-*.min.js'|fileversion %}";
    e.type = "text/javascript";
    document.getElementsByTagName("head")[0].appendChild(e);
    var e = document.createElement("script");
    e.src = "{{ server_url }}{% url static 'flowplayer/flowplayer.ipad-*.min.js'|fileversion %}";
    e.type = "text/javascript";
    e.onreadystatechange = insert_flowplayer;
    e.onload = insert_flowplayer;
    document.getElementsByTagName("head")[0].appendChild(e);
}
})();
