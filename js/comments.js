var commentsLeftToShow  = 0;
var comments_limit      = 5; // limit to show per clic/load
var $postComments       = $(".post-comments");
var $data               = null;
var user                = $("#user").text();


function loadComments() {

    var page = { "page": $("title").text().replace(/ /g, "_")};

    var RequeestTimeout = setTimeout(function() {
            $("input:first").text("Failed to get resources.");
    }, 5000);

    $postComments.children().remove();

    var sort_by = function(field, reverse, primer){
        var key = function (x) {return primer ? primer(x[field]) : x[field]};

        return function (a,b) {
            var A = key(a), B = key(b);
            return ( (A < B) ? -1 : ((A > B) ? 1 : 0) ) * [-1,1][+!!reverse];
        }
    }

    $.ajax({
        url: "/comments",
        type: "GET",
        dataType: 'json',
        data : page

    }).done(function(data) {
        if ( data ){
            $data = data;
            commentsLeftToShow = data.length;
            rationalizeComments ();

            $("#comments-ammount").text( Object.keys( data ).length );

        } else {
             $postComments.append( "<span>Be the <strong>first</strong> in comment this post! :D</span>");
             $( "#load-more-comments" ).fadeOut("slow");
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



function editComment(id){
    if( $("textarea#"+id).siblings().length < 2 ){
        $(".user-comments").children("span").remove();

        $("textarea#"+id).removeAttr("readonly").focusout( function () {
            $( this ).attr("readonly","");
            $(".user-comments").children("span").remove();
        });

        $("textarea#"+id).focus();
        $("textarea#"+id).parent().append("<a href='javascript:saveComment("+id+")'><span id='save' class='btn action'>Save</span></a>");
    }
}

function saveComment(id){
    updatedComment = $("textarea#"+id).val();

    $.ajax({
        url: "/comments",
        type: "GET",
        dataType: 'json',
        data : {"action": "updateComment", "id": id, "comment": updatedComment }

    }).done( function( dataFromServer, status ) {

        if ( status ){
            $("textarea#"+id).attr("readonly","");
            $("textarea#"+id).parent().append("<span id='success' class='btn success'>Comment edited</span></a>").fadeIn("slow");
        //$("#save").fadeout(500);
        $(".user-comments").children("span, a").fadeOut(700);
            //$("#success").fadeOut("slow");
        }

    }).fail(function(e) {
        console.log("e: "+ e);
    });


    return false;
}

function rationalizeComments() {

    var count = comments_limit;

    for (var i = commentsLeftToShow -1; count > 0 ; i--) {

            if( $data[i][1].user == user ){
                $postComments.append("<div class='user-comments'>\
                                        <div class='comment-header'><h4><a href='/user/"+ $data[i][1].user + "'>"+ $data[i][1].user +"</a>: ("+ $data[i][1].created +")</h4><span class='btn action edit-comment'><a href='javascript:editComment("+$data[i][1].id +")'>Edit</a></span> </div>\
                                        <textarea id='"+ $data[i][1].id +"' class='comment' readonly>"+ $data[i][1].comment +"</textarea>\
                                    </div>");
            } else {
                $postComments.append("<div class='user-comments'>\
                                        <div class='comment-header'><h4><a href='/user/"+ $data[i][1].user + "'>"+ $data[i][1].user +"</a>: ("+ $data[i][1].created +")</h4></div>\
                                        <textarea class='comment' readonly>"+ $data[i][1].comment +"</textarea>\
                                    </div>");
            }

        count--;
        commentsLeftToShow--;

        if( commentsLeftToShow == 0 ){
            $( "#load-more-comments" ).fadeOut( "slow");

            break;
        }

    }
}

$("form").submit( function ( event ) {
    event.preventDefault();
    addComment();
} );

$("#load-more-comments").click( function() {
    rationalizeComments();
});


$( document ).ready( loadComments );





