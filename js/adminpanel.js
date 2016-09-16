function swap_post_state(post_id) {
    console.log( post_id);
    $.ajax({
        url: "/disable",
        type: "GET",
        dataType: 'json',
        data : {"post_id" : post_id}

    }).done(function(data) {
        if ( data ){

            var $rankPosts = $("#rank_posts");

            $rankPosts.childrens().remove();

            for(var i = 0; i < data.tt_views; i++){
                $rankPosts.append("<td class='center'>"+i+"</td>"/
                    "<td> <a href="+data.tt_views[i][1].title+">"+data.tt_views[i][1].title+"</a><small> (in <a href='/search/"+ data.tt_views[i][1].topic +"'>"+data.tt_views[i][1].topic+"</a>)</small></td>");


                // <td class="text-center date-col"> <a href="/user/{{ p[2].user }}">{{ p[2].user }} </a></td>
                //     <td class="text-center date-col"> {{ p[2].modified.strftime('%d-%m-%y') }}</td>
                //     <td class="text-center"> {{ p[2].views }}</td>

                //     {% if p[2].state %}
                //         <td class="disable center"> <a href="#" alt="{{ p[2].key().id() }}"><b>[ &#9671; ]</b></a></td>
                //     {% else %}
                //         <td class="enable center"> <a href="#" alt="{{ p[2].key().id() }}"><b>[ &#9670; ]</b></a></td>
                //     {% endif %}

            }

        } else {
            alert("nope");
        }


    }).fail(function(e) {
        console.log("e: "+ e);
    });
}


$(".enable a, .disable a").click( function() {
    swap_post_state( $( this ).attr("alt") );
});

