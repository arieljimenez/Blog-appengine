
function searchComments( user ) {


    $.ajax({
        url: "/comments",
        type: "GET",
        dataType: 'json',
        data : {"action": "getCommentsUser", "user": user }

    }).done( function( dataFromServer ) {

        if ( dataFromServer ){
            console.log ( dataFromServer );
        }

    }).fail(function(e) {
        console.log("e: "+ e);
    });
}