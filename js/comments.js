function loadComments() {

    var page = $("title").text().replace(/ /g, "_");
    var $postComments = $(".post-comments");

    var RequeestTimeout = setTimeout(function() {
            $("input:first").text("Failed to get resources.");
    }, 5000);

    $postComments.children().remove();

    $.ajax({
        url: "/getcomments/"+page,
        type: "POST",
        dataType: 'json'

    }).done(function(data) {
        if ( data ){
            $.each( data, function( key, val ) {
                $postComments.append("<div class='user-comments'>\
                                        <h4><a href='/user/"+ val.user + "'>"+ val.user +"</a>: ("+ val.created +")</h4>\
                                        <textarea class='comment'>"+ val.comment +"</textarea>\
                                    </div>");
            });

        } else {
             $postComments.append( "Be the <strong>first</strong> in comment this post! :D ");
        }

        clearTimeout(RequeestTimeout);

    }).fail(function(e) {
        console.log("e: "+ e);
    });

    return false;
};


$( document ).ready( loadComments );

$(".comment").submit( loadComments )