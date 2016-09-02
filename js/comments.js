function loadComments() {

    var page = { "page": $("title").text().replace(/ /g, "_")};
    var $postComments = $(".post-comments");

    var RequeestTimeout = setTimeout(function() {
            $("input:first").text("Failed to get resources.");
    }, 5000);

    $postComments.children().remove();

    $.ajax({
        url: "/comments",
        type: "GET",
        dataType: 'json',
        data : page

    }).done(function(data) {
        if ( data ){
            $.each( data, function( key, val ) {
                $postComments.append("<div class='user-comments'>\
                                        <h4><a href='/user/"+ val.user + "'>"+ val.user +"</a>: ("+ val.created +")</h4>\
                                        <textarea class='comment' readonly>"+ val.comment +"</textarea>\
                                    </div>");
            });

            $("#comments-ammount").text( Object.keys( data ).length );

        } else {
             $postComments.append( "<span>Be the <strong>first</strong> in comment this post! :D</span>");
        }

        clearTimeout(RequeestTimeout);

    }).fail(function(e) {
        console.log("e: "+ e);
    });

    return false;
};


function addComment() {

    var newComment = $(".tarea-comments").val() ;
    var page = "/" + $("title").text().replace(/ /g, "_");

    if( newComment.length == 0){
        $("#comment-error").append("<p>A empty comment ... Jhon travolta is confused. <br> \
            <iframe src='//giphy.com/embed/rCAVWjzASyNlm' width='480' height='240' frameBorder='0' class='giphy-embed' allowFullScreen></iframe><p><a href='http://giphy.com/gifs/confused-lego-travolta-rCAVWjzASyNlm'>via GIPHY</a></p>");
        $(".tarea-comments").attr("placeholder", "WRITE SOMETHING FIRST!");
        $(".tarea-comments").focus();
        return false;
    } else {
        $(".tarea-comments").attr("placeholder", "Add a comment");
    }

    var RequeestTimeout = setTimeout(function() {
            $("#comment-error").text("Server Timeout... try again!");
    }, 5000);

    $("#comment-error").text("");

    $.ajax({
        url: "/comments",
        type: "POST",
        dataType: 'json',
        data : {"page": page, "comment": newComment }

    }).done( function( dataFromServer, status ) {

        if ( status ){
            $(".tarea-comments").val("");
            loadComments();
        }

        clearTimeout(RequeestTimeout);

    }).fail(function(e) {
        console.log("e: "+ e);
    });

    return false;
};

$( document ).ready( loadComments );

$("form").submit( function ( event ) {
    event.preventDefault();

    addComment();
    //return false;
} );