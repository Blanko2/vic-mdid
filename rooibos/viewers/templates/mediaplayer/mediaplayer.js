(function() {
var clip;
{% if streaming_server and streaming_media %}
clip = {
    clip: {
        autoPlay: false,
        url: '{{ streaming_media|escapejs }}',
        provider: 'influxis',
        scaling: 'fit'
    },
    plugins: {
        influxis: {
            url: "{{ server_url }}{% url static 'flowplayer/flowplayer.rtmp-3.2.3.swf' %}",
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
    };
{% else %}
clip = {
    clip: {
        autoPlay: false,
        url: '{{ server_url }}{{ delivery_url|escapejs }}'
        {% if audio %} ,
        type: 'audio'
        {% else %} ,
        scaling: 'fit'
        {% endif %}
    }
    {% if audio %} ,
    plugins: {
        audio: {
            url: "{{ server_url }}{% url static 'flowplayer/flowplayer.audio-3.2.1.swf' %}"
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
    flowplayer("player-{{ record.id }}-{{ selectedmedia.id }}", "{{ server_url }}{% url static 'flowplayer/flowplayer-3.2.4.swf' %}", clip);
}

if (typeof(flowplayer) == "function") {
    insert_flowplayer();
} else {
    var e = document.createElement("script");
    e.src = "{{ server_url }}{% url static 'flowplayer/flowplayer-3.2.4.min.js' %}";
    e.type = "text/javascript";
    e.onreadystatechange = insert_flowplayer;
    e.onload = insert_flowplayer;
    document.getElementsByTagName("head")[0].appendChild(e);
}
})();
