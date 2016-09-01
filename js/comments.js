function loadComments() {

    var page = { "page": $("title").text().replace(/ /g, "_")};
    var $postComments = $(".post-comments");

    var RequeestTimeout = setTimeout(function() {
            $("input:first").text("Failed to get resources.");
    }, 5000);

    $postComments.children().remove();

    $.ajax({
        url: "/getcomments",
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
             $postComments.append( "Be the <strong>first</strong> in comment this post! :D ");
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

    var RequeestTimeout = setTimeout(function() {
            $("#comment-error").text("Server Timeout... try again!");
    }, 5000);

    $("#comment-error").text("");

    $.ajax({
        url: "/",
        type: "POST",
        dataType: 'json',
        data : {"page": page, "comment": newComment }

    }).done( function( dataFromServer, status ) {

        console.log( status );
        // if ( dataFromServer ){
        //     $.each( dataFromServer, function( key, val ) {
        //         $postComments.append("<div class='user-comments'>\
        //                                 <h4><a href='/user/"+ val.user + "'>"+ val.user +"</a>: ("+ val.created +")</h4>\
        //                                 <textarea class='comment'>"+ val.comment +"</textarea>\
        //                             </div>");
        //     });

        // } else {
        //      $postComments.append( "Be the <strong>first</strong> in comment this post! :D ");
        // }

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